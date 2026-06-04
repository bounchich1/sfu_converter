from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.ast_nodes import SourceSpan
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.domain.formatting import FormattingProfile, FormattingRule, unsupported_rule_diagnostics
from sfu_converter.infrastructure.paragraph_roles import ParagraphRole, classify
from sfu_converter.registry import get_profile, get_rule

_LENGTH_TOLERANCE_EMU = 1000
_POINT_TOLERANCE = 0.5
_SPACING_TOLERANCE = 0.1

_ALIGNMENT_BY_NAME = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

_HEADING_ROLES = {
    ParagraphRole.HEADING_H1,
    ParagraphRole.HEADING_H2,
    ParagraphRole.HEADING_H3,
    ParagraphRole.HEADING_H4,
}

_HEADING_RULE_BY_ROLE = {
    ParagraphRole.HEADING_H1: "common.heading.h1",
    ParagraphRole.HEADING_H2: "common.heading.h2",
    ParagraphRole.HEADING_H3: "common.heading.h3",
    ParagraphRole.HEADING_H4: "common.heading.h4",
}


class DocxValidator:
    """Validate generated DOCX files against registry-backed formatting rules."""

    def __init__(
        self,
        profile: FormattingProfile | None = None,
        *,
        config_class=SIBFUConfig,
    ):
        self.profile = profile or get_profile("common")
        self.config = config_class
        self.diagnostics: list[Diagnostic] = []

    def validate_file(self, file_path: str) -> list[Diagnostic]:
        self.diagnostics = []
        doc_path = Path(file_path)
        if not doc_path.exists():
            self._add(
                code="DOCX_FILE_NOT_FOUND",
                message=f"Файл не найден: {file_path}",
                severity=Severity.ERROR,
            )
            return self.diagnostics

        try:
            doc = Document(str(doc_path))
        except Exception as exc:
            self._add(
                code="DOCX_OPEN_FAILED",
                message=f"Не удалось открыть файл: {exc}",
                severity=Severity.ERROR,
            )
            return self.diagnostics

        self.diagnostics.extend(unsupported_rule_diagnostics(self.profile, component="validator"))
        self._validate_margins(doc)
        self._validate_page_numbering(doc)

        paragraphs = list(doc.paragraphs)
        for index, paragraph in enumerate(paragraphs, start=1):
            prev = paragraphs[index - 2] if index >= 2 else None
            nxt = paragraphs[index] if index < len(paragraphs) else None
            role = classify(paragraph, prev=prev, next=nxt, profile=self.profile)
            self._validate_paragraph(paragraph, index, role)

        for table_index, table in enumerate(doc.tables, start=1):
            self._validate_table(table, table_index)

        return self.diagnostics

    def _validate_page_numbering(self, doc) -> None:
        rule_id = "common.page.numbering"
        try:
            rule = self._rule(rule_id)
        except KeyError:
            return

        from docx.oxml.ns import qn as _qn

        for section_index, section in enumerate(doc.sections, start=1):
            sect_pr = section._sectPr

            if section_index == 1:
                title_pg = sect_pr.find(_qn("w:titlePg"))
                title_pg_active = title_pg is not None and title_pg.get(
                    _qn("w:val")
                ) not in ("0", "false")
                if not title_pg_active:
                    self._add(
                        code=DiagnosticCodes.FORMAT_PAGE_NUMBERING,
                        message=(
                            f"Section {section_index}: titlePg flag is missing — "
                            f"page number would appear on the title page"
                        ),
                        rule_id=rule_id,
                    )

            footer = section.footer
            footer_xml = footer._element.xml
            if " PAGE " not in footer_xml:
                continue

            for paragraph in footer.paragraphs:
                if " PAGE " not in paragraph._p.xml:
                    continue

                alignment = paragraph.paragraph_format.alignment
                if alignment != WD_ALIGN_PARAGRAPH.CENTER:
                    self._add(
                        code=DiagnosticCodes.FORMAT_PAGE_NUMBERING,
                        message=(
                            f"Section {section_index}: page number alignment "
                            "must be center"
                        ),
                        rule_id=rule_id,
                    )

                first_line_indent = paragraph.paragraph_format.first_line_indent
                if first_line_indent is not None and abs(first_line_indent - Cm(0)) > _LENGTH_TOLERANCE_EMU:
                    self._add(
                        code=DiagnosticCodes.FORMAT_PAGE_NUMBERING,
                        message=(
                            f"Section {section_index}: page number first-line "
                            f"indent {first_line_indent.cm:.2f} cm, expected 0 cm"
                        ),
                        rule_id=rule_id,
                    )

                for run in paragraph.runs:
                    font_name = run.font.name
                    if font_name and font_name != rule.parameters["font_name"]:
                        self._add(
                            code=DiagnosticCodes.FORMAT_PAGE_NUMBERING,
                            message=(
                                f"Section {section_index}: page number font "
                                f"'{font_name}', expected '{rule.parameters['font_name']}'"
                            ),
                            rule_id=rule_id,
                        )

                    font_size = _pt_value(run.font.size)
                    expected_size = rule.parameters["font_size_pt"]
                    if font_size and abs(font_size - expected_size) > _POINT_TOLERANCE:
                        self._add(
                            code=DiagnosticCodes.FORMAT_PAGE_NUMBERING,
                            message=(
                                f"Section {section_index}: page number size "
                                f"{font_size:.1f}pt, expected {expected_size}pt"
                            ),
                            rule_id=rule_id,
                        )

    def _validate_margins(self, doc) -> None:
        rule_id = "common.page.margins.portrait"
        params = self._rule(rule_id).parameters
        checks = (
            ("top_margin", "top_mm", DiagnosticCodes.FORMAT_MARGIN_TOP, "Top"),
            ("bottom_margin", "bottom_mm", DiagnosticCodes.FORMAT_MARGIN_BOTTOM, "Bottom"),
            ("left_margin", "left_mm", DiagnosticCodes.FORMAT_MARGIN_LEFT, "Left"),
            ("right_margin", "right_mm", DiagnosticCodes.FORMAT_MARGIN_RIGHT, "Right"),
        )

        for section_index, section in enumerate(doc.sections, start=1):
            for attr_name, param_name, code, label in checks:
                actual = getattr(section, attr_name)
                expected = Cm(params[param_name] / 10)
                if abs(actual - expected) > _LENGTH_TOLERANCE_EMU:
                    self._add(
                        code=code,
                        message=(
                            f"{label} margin in section {section_index} is "
                            f"{actual.cm:.2f} cm, expected {expected.cm:.2f} cm"
                        ),
                        rule_id=rule_id,
                    )

    def _validate_paragraph(self, paragraph, index: int, role: ParagraphRole | None = None) -> None:
        if not paragraph.text.strip():
            return

        if role is None:
            role = classify(paragraph, profile=self.profile)

        if role is ParagraphRole.FIGURE_PLACEHOLDER:
            self._add(
                code=DiagnosticCodes.FIGURE_MISSING_IMAGE,
                message=f"Paragraph {index}: figure image is missing",
                severity=Severity.INFO,
                rule_id="common.figure.image",
                source=SourceSpan(index, index),
            )
            return

        for run_index, run in enumerate(paragraph.runs, start=1):
            self._validate_run_font(run, index, run_index)

        if role in _HEADING_ROLES:
            self._validate_heading(paragraph, index, role)
            return
        if role is ParagraphRole.STRUCTURAL_HEADING or role is ParagraphRole.TOC_HEADING:
            self._validate_styled_paragraph(paragraph, index, "common.structural.heading")
            return
        if role is ParagraphRole.APPENDIX_HEADING:
            rule_id = "common.appendix.heading"
            try:
                self._validate_styled_paragraph(paragraph, index, rule_id)
            except KeyError:
                self._validate_styled_paragraph(paragraph, index, "common.structural.heading")
            return
        if role is ParagraphRole.TOC_ENTRY:
            return
        if role is ParagraphRole.TABLE_CAPTION:
            self._validate_styled_paragraph(paragraph, index, "common.table.caption")
            return
        if role is ParagraphRole.FIGURE_CAPTION:
            self._validate_styled_paragraph(paragraph, index, "common.figure.caption")
            return
        if role is ParagraphRole.FIGURE_EXPLANATORY:
            self._validate_styled_paragraph(paragraph, index, "common.figure.explanatory_data")
            return
        if role is ParagraphRole.LIST_ITEM:
            self._validate_styled_paragraph(paragraph, index, "common.list.item")
            return
        if role is ParagraphRole.FORMULA_BODY:
            self._validate_styled_paragraph(paragraph, index, "common.formula.body")
            return
        if role is ParagraphRole.FORMULA_EXPLANATION:
            self._validate_styled_paragraph(paragraph, index, "common.formula.explanation")
            return
        if role is ParagraphRole.BIBLIOGRAPHY_ENTRY:
            self._validate_styled_paragraph(paragraph, index, "common.bibliography.entry")
            return
        if role is ParagraphRole.UNKNOWN:
            self._add(
                code=DiagnosticCodes.FORMAT_ROLE_UNRECOGNIZED,
                message=f"Paragraph {index}: paragraph role could not be classified",
                severity=Severity.WARNING,
                source=SourceSpan(index, index),
            )
            return

        self._validate_body_paragraph(paragraph, index)

    def _validate_styled_paragraph(self, paragraph, index: int, rule_id: str) -> None:
        """Validate ``paragraph`` against a non-body rule's paragraph format."""

        params = self._rule(rule_id).parameters
        if "indent_cm" in params:
            self._validate_first_line_indent(
                paragraph, index, rule_id=rule_id, expected_cm=params["indent_cm"]
            )
        if "line_spacing" in params:
            self._validate_line_spacing(
                paragraph, index, rule_id=rule_id, expected=params["line_spacing"]
            )
        if "alignment" in params:
            self._validate_alignment(
                paragraph, index, rule_id=rule_id, expected=params["alignment"]
            )
        self._validate_paragraph_spacing(paragraph, index, rule_id)

    def _validate_body_paragraph(self, paragraph, index: int) -> None:
        self._validate_first_line_indent(
            paragraph,
            index,
            rule_id="common.text.indent.first_line",
            expected_cm=self._rule("common.text.indent.first_line").parameters["indent_cm"],
        )
        self._validate_line_spacing(
            paragraph,
            index,
            rule_id="common.text.line_spacing",
            expected=self._rule("common.text.line_spacing").parameters["spacing"],
        )
        self._validate_alignment(
            paragraph,
            index,
            rule_id="common.text.alignment",
            expected=self._rule("common.text.alignment").parameters["alignment"],
        )
        self._validate_paragraph_spacing(paragraph, index, "common.text.line_spacing")

    def _validate_heading(self, paragraph, index: int, role: ParagraphRole | None = None) -> None:
        if role is None or role not in _HEADING_RULE_BY_ROLE:
            rule_id = self._heading_rule_id(paragraph)
        else:
            rule_id = _HEADING_RULE_BY_ROLE[role]
        params = self._rule(rule_id).parameters

        self._validate_first_line_indent(
            paragraph,
            index,
            rule_id=rule_id,
            expected_cm=params.get("indent_cm", 0),
        )
        self._validate_line_spacing(
            paragraph,
            index,
            rule_id=rule_id,
            expected=params.get("line_spacing", 1.0),
        )
        self._validate_alignment(
            paragraph,
            index,
            rule_id=rule_id,
            expected=params.get("alignment", "left"),
        )
        self._validate_paragraph_spacing(paragraph, index, rule_id)

        expected_bold = bool(params.get("bold", False))
        if expected_bold and paragraph.runs and not any(run.bold for run in paragraph.runs):
            self._add(
                code=DiagnosticCodes.FORMAT_HEADING_BOLD,
                message=f"Paragraph {index}: heading must be bold",
                rule_id=rule_id,
                source=SourceSpan(index, index),
            )

        if paragraph.text.strip().endswith("."):
            self._add(
                code=DiagnosticCodes.FORMAT_HEADING_NO_PERIOD,
                message=f"Paragraph {index}: heading must not end with a period",
                rule_id="common.heading.no_period",
                source=SourceSpan(index, index),
            )

    def _validate_table(self, table, table_index: int) -> None:
        rule = self._rule("common.table.font.size")
        min_size = rule.parameters["min_size_pt"]
        max_size = rule.parameters["max_size_pt"]

        for row_index, row in enumerate(table.rows, start=1):
            for cell_index, cell in enumerate(row.cells, start=1):
                for paragraph in cell.paragraphs:
                    for run_index, run in enumerate(paragraph.runs, start=1):
                        self._validate_run_font(
                            run,
                            f"table {table_index} row {row_index} cell {cell_index}",
                            run_index,
                            validate_size=False,
                        )
                        size = _pt_value(run.font.size)
                        if size and not (min_size <= size <= max_size):
                            self._add(
                                code=DiagnosticCodes.FORMAT_TABLE_FONT_SIZE,
                                message=(
                                    "Table "
                                    f"{table_index} row {row_index} cell {cell_index} "
                                    f"run {run_index}: size {size:.1f}pt, "
                                    f"expected {min_size}-{max_size}pt"
                                ),
                                rule_id=rule.id,
                            )

    def _validate_run_font(
        self,
        run,
        paragraph_index,
        run_index: int,
        *,
        validate_size: bool = True,
    ) -> None:
        name_rule = self._rule("common.text.font.name")
        expected_name = name_rule.parameters["font_name"]
        if run.font.name and run.font.name != expected_name:
            self._add(
                code=DiagnosticCodes.FORMAT_FONT_NAME,
                message=(
                    f"Paragraph {paragraph_index} run {run_index}: font '{run.font.name}', expected '{expected_name}'"
                ),
                rule_id=name_rule.id,
                source=_source_for_index(paragraph_index),
            )

        if validate_size:
            size_rule = self._rule("common.text.font.size")
            expected_size = size_rule.parameters["font_size_pt"]
            current_size = _pt_value(run.font.size)
            if current_size and abs(current_size - expected_size) > _POINT_TOLERANCE:
                self._add(
                    code=DiagnosticCodes.FORMAT_FONT_SIZE,
                    message=(
                        f"Paragraph {paragraph_index} run {run_index}: "
                        f"size {current_size:.1f}pt, expected {expected_size}pt"
                    ),
                    rule_id=size_rule.id,
                    source=_source_for_index(paragraph_index),
                )

        color_rule = self._rule("common.text.font.color")
        expected_color = tuple(color_rule.parameters["color_rgb"])
        current_color = run.font.color.rgb
        if current_color is not None and tuple(current_color) != expected_color:
            self._add(
                code=DiagnosticCodes.FORMAT_FONT_COLOR,
                message=(
                    f"Paragraph {paragraph_index} run {run_index}: "
                    f"color {tuple(current_color)}, expected {expected_color}"
                ),
                rule_id=color_rule.id,
                source=_source_for_index(paragraph_index),
            )

    def _validate_first_line_indent(
        self,
        paragraph,
        index: int,
        *,
        rule_id: str,
        expected_cm: float,
    ) -> None:
        current = paragraph.paragraph_format.first_line_indent
        if current is None:
            return
        expected = Cm(expected_cm)
        if abs(current - expected) > _LENGTH_TOLERANCE_EMU:
            self._add(
                code=DiagnosticCodes.FORMAT_INDENT,
                message=(f"Paragraph {index}: first-line indent {current.pt:.1f}pt, expected {expected.pt:.1f}pt"),
                rule_id=rule_id,
                source=SourceSpan(index, index),
            )

    def _validate_line_spacing(
        self,
        paragraph,
        index: int,
        *,
        rule_id: str,
        expected: float,
    ) -> None:
        current = paragraph.paragraph_format.line_spacing
        if current is None:
            return
        spacing = _spacing_value(current)
        if abs(spacing - expected) > _SPACING_TOLERANCE:
            self._add(
                code=DiagnosticCodes.FORMAT_LINE_SPACING,
                message=f"Paragraph {index}: line spacing {spacing}, expected {expected}",
                rule_id=rule_id,
                source=SourceSpan(index, index),
            )

    def _validate_alignment(
        self,
        paragraph,
        index: int,
        *,
        rule_id: str,
        expected: str,
    ) -> None:
        current = paragraph.paragraph_format.alignment
        if current is None:
            return
        expected_alignment = _ALIGNMENT_BY_NAME[expected]
        if current != expected_alignment:
            self._add(
                code=DiagnosticCodes.FORMAT_ALIGNMENT,
                message=f"Paragraph {index}: alignment {current}, expected {expected}",
                rule_id=rule_id,
                source=SourceSpan(index, index),
            )

    def _validate_paragraph_spacing(self, paragraph, index: int, rule_id: str) -> None:
        pf = paragraph.paragraph_format
        for label, value in (("before", pf.space_before), ("after", pf.space_after)):
            current = _pt_value(value)
            if current > 1:
                self._add(
                    code=DiagnosticCodes.FORMAT_PARAGRAPH_SPACING,
                    message=(f"Paragraph {index}: spacing {label} {current:.1f}pt, expected 0pt"),
                    rule_id=rule_id,
                    source=SourceSpan(index, index),
                )

    def _is_heading_paragraph(self, paragraph) -> bool:
        style_name = paragraph.style.name if paragraph.style else ""
        return style_name.startswith("Heading") or (
            paragraph.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
            and any(run.bold for run in paragraph.runs)
        )

    def _heading_rule_id(self, paragraph) -> str:
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name.startswith("Heading 2"):
            return "common.heading.h2"
        if style_name.startswith("Heading 3"):
            return "common.heading.h3"
        return "common.heading.h1"

    def _rule(self, rule_id: str) -> FormattingRule:
        for rule in self.profile.rules:
            if rule.id == rule_id:
                return rule
        return get_rule(rule_id)

    def _add(
        self,
        *,
        code: str,
        message: str,
        severity: Severity = Severity.ERROR,
        rule_id: str | None = None,
        source: SourceSpan | None = None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                severity=severity,
                rule_id=rule_id,
                source=source,
            )
        )


def diagnostic_to_json(diagnostic: Diagnostic) -> dict[str, object]:
    source = _diagnostic_source(diagnostic)
    payload: dict[str, object] = {
        "code": diagnostic.code,
        "severity": diagnostic.severity.value,
        "message": diagnostic.message,
        "ruleId": diagnostic.rule_id,
        "source": source,
        "data": dict(diagnostic.data or {}),
    }
    if diagnostic.rule_id:
        try:
            rule = get_rule(diagnostic.rule_id)
        except KeyError:
            rule = None
        if rule is not None:
            payload["source"] = {
                **source,
                "document": rule.source_doc,
                "section": rule.source_section,
            }
    if diagnostic.target is not None:
        payload["target"] = diagnostic.target
    if diagnostic.suggestion:
        payload["suggestion"] = diagnostic.suggestion
    return payload


def _diagnostic_source(diagnostic: Diagnostic) -> dict[str, object]:
    span = diagnostic.source
    return {
        "document": span.filename if span is not None else None,
        "section": None,
        "lineStart": span.line_start if span is not None else None,
        "lineEnd": span.line_end if span is not None else None,
    }


def _source_for_index(index) -> SourceSpan | None:
    return SourceSpan(index, index) if isinstance(index, int) else None


def _pt_value(value) -> float:
    if value is None:
        return 0
    if hasattr(value, "pt"):
        return float(value.pt)
    return float(value)


def _spacing_value(value) -> float:
    if hasattr(value, "pt"):
        return float(value.pt)
    return float(value)


def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "-")
