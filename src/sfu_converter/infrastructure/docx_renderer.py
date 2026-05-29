from __future__ import annotations

import logging
import re
from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from sfu_converter.config import PathConfig, SIBFUConfig
from sfu_converter.domain.ast_nodes import (
    AppendixNode,
    BibliographyEntryNode,
    Document,
    FigureNode,
    FormulaNode,
    HeadingLevel,
    HeadingNode,
    ListNode,
    ListType,
    PageBreakNode,
    ParagraphNode,
    RawBlockNode,
    ReferenceNode,
    StructuralSectionNode,
    StructuralSectionType,
    TableCaptionNode,
    TableNode,
    TableOfContentsNode,
    TitlePageNode,
)
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.domain.formatting import FormattingProfile, RuleStatus, unsupported_rule_diagnostics
from sfu_converter.infrastructure import docx_styles
from sfu_converter.ports.renderer import RendererPort
from sfu_converter.registry import get_profile
from sfu_converter.utils_image_insert import insert_image


_SFU_STYLE_BY_TYPE = {
    "caption_img": docx_styles.FIGURE_CAPTION,
    "caption_table": docx_styles.TABLE_CAPTION,
    "formula": docx_styles.FORMULA_BODY,
    "formula_explanation": docx_styles.FORMULA_EXPLANATION,
    "bibliography_entry": docx_styles.BIBLIOGRAPHY_ENTRY,
    "list_item": docx_styles.LIST_ITEM,
    "structural_section": docx_styles.STRUCTURAL_HEADING,
}


class SectionNumberer:
    """Tracks hierarchical section numbers for H1-H3 headings."""

    def __init__(self):
        self._counters = [0, 0, 0]

    def next_number(self, level: int) -> str:
        if level < 1 or level > len(self._counters):
            raise ValueError(f"Unsupported heading level: {level}")

        index = level - 1
        for parent_index in range(index):
            if self._counters[parent_index] == 0:
                self._counters[parent_index] = 1

        self._counters[index] += 1
        for lower_index in range(index + 1, len(self._counters)):
            self._counters[lower_index] = 0

        return ".".join(str(part) for part in self._counters[:level])

    def reset(self):
        self._counters = [0, 0, 0]


_RUSSIAN_LIST_LETTERS = (
    "а",
    "б",
    "в",
    "г",
    "д",
    "е",
    "ж",
    "и",
    "к",
    "л",
    "м",
    "н",
    "п",
    "р",
    "с",
    "т",
    "у",
    "ф",
    "х",
    "ц",
    "ш",
    "щ",
    "э",
    "ю",
    "я",
)


class DocxRenderer(RendererPort):
    """python-docx renderer for the domain AST."""

    def __init__(self, config_class=SIBFUConfig, base_dir=None, logger=None):
        self.config = config_class
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.doc = None
        self.logger = logger or logging.getLogger(__name__)
        self._style_map = self._build_style_map()
        self._bold_styles = frozenset({"h1", "h2", "structural_section"})
        self._section_numberer = SectionNumberer()
        self._rendered_body_blocks = False

    def render(
        self,
        document: Document,
        profile: FormattingProfile,
        template_path: str | None = None,
        template_mode: str = "append",
    ) -> bytes:
        self._initialize_document(template_path, template_mode=template_mode, profile=profile)
        self._render_from_ast(document)
        buffer = BytesIO()
        self.doc.save(buffer)
        return buffer.getvalue()

    def render_to_file(
        self,
        document: Document,
        profile: FormattingProfile,
        output_path: str,
        template_path: str | None = None,
        template_mode: str = "append",
    ) -> list[Diagnostic]:
        diagnostics = unsupported_rule_diagnostics(profile, component="renderer")
        self._initialize_document(template_path, template_mode=template_mode, profile=profile)
        self._render_from_ast(document)
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(destination))
        return diagnostics + self._title_page_diagnostics

    def _set_run_style(self, run, bold=False, italic=False):
        run.font.name = self.config.FONT_NAME
        run.font.size = self.config.FONT_SIZE
        run.font.color.rgb = RGBColor(*self.config.FONT_COLOR_RGB)
        run.bold = bold
        run.italic = italic
        run._element.rPr.rFonts.set(qn("w:eastAsia"), self.config.FONT_NAME)

    def _build_style_map(self):
        """Return style_type -> formatting parameters dict.

        Each entry may carry the optional keys ``word_style``, ``align``,
        ``indent``, ``line_spacing``, ``space_before``, ``space_after``. Only
        present keys are applied to the paragraph; missing keys are left
        untouched. Resolved once per renderer instance and cached.
        """

        cfg = self.config
        zero = Pt(0)
        no_indent = Cm(0)

        return {
            "normal": {
                "align": cfg.ALIGNMENT,
                "indent": cfg.FIRST_LINE_INDENT,
                "line_spacing": cfg.LINE_SPACING_NORMAL,
                "space_before": zero,
                "space_after": zero,
            },
            "h1": {
                "word_style": "Heading 1",
                "align": cfg.H1["align"],
                "indent": cfg.H1["indent"],
                "line_spacing": cfg.H1["line_spacing"],
                "space_before": cfg.H1["space_before"],
                "space_after": cfg.H1["space_after"],
            },
            "h2": {
                "word_style": "Heading 2",
                "align": cfg.H2["align"],
                "indent": cfg.H2["indent"],
                "line_spacing": cfg.H2["line_spacing"],
                "space_before": cfg.H2["space_before"],
                "space_after": cfg.H2["space_after"],
            },
            "h3": {
                "word_style": "Heading 3",
                "align": cfg.H3["align"],
                "indent": cfg.H3["indent"],
                "line_spacing": cfg.H3["line_spacing"],
                "space_before": cfg.H3["space_before"],
                "space_after": cfg.H3["space_after"],
            },
            "list_item": {
                "align": cfg.LIST_ITEM["align"],
                "indent": cfg.LIST_ITEM["indent"],
                "line_spacing": cfg.LIST_ITEM["line_spacing"],
                "space_before": cfg.LIST_ITEM["space_before"],
                "space_after": cfg.LIST_ITEM["space_after"],
            },
            "structural_section": {
                "align": cfg.STRUCTURAL_SECTION["align"],
                "indent": cfg.STRUCTURAL_SECTION["indent"],
                "line_spacing": cfg.STRUCTURAL_SECTION["line_spacing"],
                "space_before": cfg.STRUCTURAL_SECTION["space_before"],
                "space_after": cfg.STRUCTURAL_SECTION["space_after"],
            },
            "caption_img": {
                "align": cfg.CAPTION_IMAGE["align"],
                "indent": cfg.CAPTION_IMAGE["indent"],
                "line_spacing": cfg.CAPTION_IMAGE["line_spacing"],
                "space_before": cfg.CAPTION_IMAGE["space_before"],
                "space_after": cfg.CAPTION_IMAGE["space_after"],
            },
            "caption_table": {
                "align": cfg.CAPTION_TABLE["align"],
                "indent": cfg.CAPTION_TABLE["indent"],
                "line_spacing": cfg.CAPTION_TABLE["line_spacing"],
                "space_before": cfg.CAPTION_TABLE["space_before"],
                "space_after": cfg.CAPTION_TABLE["space_after"],
            },
            "empty_before_header": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_BEFORE_HEADER["line_spacing"],
                "space_before": cfg.EMPTY_BEFORE_HEADER["space_before"],
                "space_after": cfg.EMPTY_BEFORE_HEADER["space_after"],
            },
            "empty_after_header": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_AFTER_HEADER["line_spacing"],
                "space_before": cfg.EMPTY_AFTER_HEADER["space_before"],
                "space_after": cfg.EMPTY_AFTER_HEADER["space_after"],
            },
            "empty_before_image": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_BEFORE_IMAGE["line_spacing"],
                "space_before": zero,
                "space_after": zero,
            },
            "empty_after_image": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_AFTER_IMAGE["line_spacing"],
                "space_before": cfg.EMPTY_AFTER_IMAGE["space_before"],
                "space_after": cfg.EMPTY_AFTER_IMAGE["space_after"],
            },
            "empty_before_table": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_BEFORE_TABLE["line_spacing"],
                "space_before": zero,
                "space_after": zero,
            },
            "empty_after_table": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_AFTER_TABLE["line_spacing"],
                "space_before": zero,
                "space_after": zero,
            },
            "empty_before_formula": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_BEFORE_FORMULA["line_spacing"],
                "space_before": zero,
                "space_after": zero,
            },
            "empty_after_formula": {
                "indent": no_indent,
                "line_spacing": cfg.EMPTY_AFTER_FORMULA["line_spacing"],
                "space_before": zero,
                "space_after": zero,
            },
            "formula": {
                "align": cfg.FORMULA["align"],
                "indent": cfg.FORMULA["indent"],
                "line_spacing": cfg.FORMULA["line_spacing"],
                "space_before": cfg.FORMULA["space_before"],
                "space_after": cfg.FORMULA["space_after"],
            },
            "formula_explanation": {
                "align": cfg.FORMULA_EXPLANATION["align"],
                "indent": cfg.FORMULA_EXPLANATION["indent"],
                "line_spacing": cfg.FORMULA_EXPLANATION["line_spacing"],
                "space_before": cfg.FORMULA_EXPLANATION["space_before"],
                "space_after": cfg.FORMULA_EXPLANATION["space_after"],
            },
            "bibliography_entry": {
                "align": cfg.BIBLIOGRAPHY_ENTRY["align"],
                "indent": cfg.BIBLIOGRAPHY_ENTRY["indent"],
                "line_spacing": cfg.BIBLIOGRAPHY_ENTRY["line_spacing"],
                "space_before": cfg.BIBLIOGRAPHY_ENTRY["space_before"],
                "space_after": cfg.BIBLIOGRAPHY_ENTRY["space_after"],
            },
        }

    def _set_paragraph_format(self, para, style_type="normal"):
        style = self._style_map.get(style_type)
        if style is None:
            self.logger.warning("Unknown style_type: %s", style_type)
            return

        word_style = style.get("word_style")
        sfu_style = _SFU_STYLE_BY_TYPE.get(style_type)
        if sfu_style is not None and self.doc is not None and sfu_style in [s.name for s in self.doc.styles]:
            para.style = self.doc.styles[sfu_style]
        elif word_style is not None and self.doc is not None:
            para.style = self.doc.styles[word_style]

        pf = para.paragraph_format
        if "align" in style:
            pf.alignment = style["align"]
        if "indent" in style:
            pf.first_line_indent = style["indent"]
        if "line_spacing" in style:
            pf.line_spacing = style["line_spacing"]
        if "space_before" in style:
            pf.space_before = style["space_before"]
        if "space_after" in style:
            pf.space_after = style["space_after"]

        if not para.runs:
            para.add_run()
        bold = style_type in self._bold_styles
        for run in para.runs:
            self._set_run_style(run, bold=bold)

    def _add_empty_paragraph(self, style_type="empty_after_image"):
        p = self.doc.add_paragraph()
        self._set_paragraph_format(p, style_type)

    def _insert_image(self, image_path=None, caption=None):
        if not image_path:
            self._add_empty_paragraph("empty_before_image")
            if caption:
                p = self.doc.add_paragraph(caption)
                self._set_paragraph_format(p, "caption_img")
            self._add_empty_paragraph("empty_after_image")
            self._rendered_body_blocks = True
            return

        full_path = self._resolve_image_path(image_path)
        self._add_empty_paragraph("empty_before_image")

        if not full_path.exists():
            self.logger.warning(f"Изображение не найдено: {full_path}")
            p = self.doc.add_paragraph(f"[Изображение не найдено: {image_path}]")
            self._set_paragraph_format(p, "caption_img")
            if docx_styles.FIGURE_PLACEHOLDER in [s.name for s in self.doc.styles]:
                p.style = self.doc.styles[docx_styles.FIGURE_PLACEHOLDER]
        else:
            try:
                success = insert_image(
                    doc=self.doc,
                    image_path=full_path,
                    config=self.config.IMAGE,
                    logger=self.logger,
                )
                if success:
                    self.logger.info(f"Изображение вставлено: {image_path}")
                else:
                    self.logger.info(f"Ошибка вставки: {image_path}")
            except Exception as exc:
                self.logger.error(f"Ошибка вставки изображения: {exc}")
                p = self.doc.add_paragraph(f"[Ошибка: {image_path}]")
                self._set_paragraph_format(p, "caption_img")
                if docx_styles.FIGURE_PLACEHOLDER in [s.name for s in self.doc.styles]:
                    p.style = self.doc.styles[docx_styles.FIGURE_PLACEHOLDER]

        if caption:
            p = self.doc.add_paragraph(caption)
            self._set_paragraph_format(p, "caption_img")

        self._add_empty_paragraph("empty_after_image")
        self._rendered_body_blocks = True

    def _parse_table_line(self, line):
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            return None
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        return cells if cells else None

    def _create_table(self, rows_data, caption=None):
        if not rows_data:
            return

        self._add_empty_paragraph("empty_before_table")

        if caption:
            p = self.doc.add_paragraph(caption)
            self._set_paragraph_format(p, "caption_table")

        table_cfg = self.config.TABLE
        num_cols = len(rows_data[0])
        table = self.doc.add_table(rows=len(rows_data), cols=num_cols)
        table.style = "Table Grid"
        table.autofit = False

        for row_idx, row_cells in enumerate(rows_data):
            row = table.rows[row_idx]
            is_header = row_idx == 0
            for col_idx, text in enumerate(row_cells):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    cell.text = text
                    for para in cell.paragraphs:
                        pf = para.paragraph_format
                        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_header else WD_ALIGN_PARAGRAPH.LEFT
                        pf.space_before = table_cfg["cell_padding"]
                        pf.space_after = table_cfg["cell_padding"]
                        pf.first_line_indent = Cm(0)
                        pf.line_spacing = table_cfg["line_spacing"]

                        for run in para.runs:
                            self._set_run_style(
                                run,
                                bold=is_header and table_cfg["header_bold"],
                            )
                            run.font.size = table_cfg["header_font_size"] if is_header else table_cfg["font_size"]

        if table_cfg["header_repeat_on_pages"]:
            self._set_repeat_header_row(table.rows[0])

        self._add_empty_paragraph("empty_after_table")
        self._rendered_body_blocks = True

    def _set_repeat_header_row(self, row):
        """Mark a row so Word repeats it on every continuation page."""

        tr = row._tr
        tr_pr = tr.get_or_add_trPr()
        tbl_header = OxmlElement("w:tblHeader")
        tr_pr.append(tbl_header)

    def _format_table_caption(self, caption, table_number):
        if not caption:
            return None
        text = caption.strip()
        if not text:
            return None
        if text.startswith("Таблица"):
            return _normalize_caption_dashes(text)
        return f"Таблица {table_number} — {text}"

    def _setup_document_margins(self):
        for section in self.doc.sections:
            section.top_margin = self.config.MARGINS["top"]
            section.bottom_margin = self.config.MARGINS["bottom"]
            section.left_margin = self.config.MARGINS["left"]
            section.right_margin = self.config.MARGINS["right"]

    def _add_page_numbering(self):
        page_cfg = self.config.PAGE_NUMBERING

        for section in self.doc.sections:
            section.different_first_page_header_footer = page_cfg["skip_first_page"]

            footer = section.footer
            footer.is_linked_to_previous = False

            paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            paragraph.clear()
            pf = paragraph.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Cm(0)
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)

            run = paragraph.add_run()
            run.font.name = page_cfg["font_name"]
            run.font.size = page_cfg["font_size"]
            run.font.color.rgb = RGBColor(*self.config.FONT_COLOR_RGB)
            run._element.get_or_add_rPr().rFonts.set(
                qn("w:eastAsia"),
                page_cfg["font_name"],
            )

            field_begin = OxmlElement("w:fldChar")
            field_begin.set(qn("w:fldCharType"), "begin")
            run._element.append(field_begin)

            instruction = OxmlElement("w:instrText")
            instruction.set(qn("xml:space"), "preserve")
            instruction.text = " PAGE "
            run._element.append(instruction)

            field_end = OxmlElement("w:fldChar")
            field_end.set(qn("w:fldCharType"), "end")
            run._element.append(field_end)

            first_footer = section.first_page_footer
            first_footer.is_linked_to_previous = False
            first_paragraph = first_footer.paragraphs[0] if first_footer.paragraphs else first_footer.add_paragraph()
            first_paragraph.clear()

    def _load_template(self, template_path):
        template_file = self._resolve_template_path(template_path)
        if template_file.exists():
            self.doc = DocxDocument(str(template_file))
            self.logger.info(f"Шаблон загружен: {template_file}")
        else:
            self.doc = DocxDocument()
            self._setup_document_margins()
            self.logger.info("Создан новый документ")

    def _initialize_document(self, template=None, *, template_mode: str = "append", profile: FormattingProfile | None = None):
        if template:
            self._load_template(template)
        else:
            self.doc = DocxDocument()
        self._setup_document_margins()
        docx_styles.register_styles(self.doc)
        self._add_page_numbering()
        self._section_numberer.reset()
        self._rendered_body_blocks = False
        self._table_counter = 0
        self._formula_counter = 0
        self._template_mode = template_mode
        self._title_page_emitted = False
        self._profile = profile
        self._title_page_diagnostics = []

    def _render_from_ast(self, document):
        for block in document.blocks:
            if isinstance(block, StructuralSectionNode):
                self._render_structural_section(block)
            elif isinstance(block, HeadingNode):
                self._render_heading(block)
            elif isinstance(block, ParagraphNode):
                self._render_paragraph(block)
            elif isinstance(block, TableNode):
                rows = [[cell.text for cell in row.cells] for row in block.rows]
                self._table_counter += 1
                caption = self._format_table_caption(block.caption, self._table_counter)
                self._create_table(rows, caption)
            elif isinstance(block, TableCaptionNode):
                p = self.doc.add_paragraph(block.text)
                self._set_paragraph_format(p, "caption_table")
            elif isinstance(block, FigureNode):
                self._insert_image(block.src, block.caption)
            elif isinstance(block, PageBreakNode):
                self.doc.add_page_break()
            elif isinstance(block, FormulaNode):
                self._render_formula(block)
            elif isinstance(block, ListNode):
                self._render_list(block)
            elif isinstance(block, AppendixNode):
                self._render_appendix(block)
            elif isinstance(block, TableOfContentsNode):
                self._render_table_of_contents(block)
            elif isinstance(block, BibliographyEntryNode):
                self._render_bibliography_entry(block)
            elif isinstance(block, RawBlockNode):
                self._render_text_block(block.text)
            elif isinstance(block, ReferenceNode):
                self._render_text_block(f"[{block.target}]")
            elif isinstance(block, TitlePageNode):
                self._render_title_page(document.metadata, block.profile)

    def _render_heading(self, block):
        if block.level is HeadingLevel.H1 and self._rendered_body_blocks:
            self.doc.add_page_break()

        if block.level is HeadingLevel.H2:
            self._add_empty_paragraph("empty_before_header")

        style_type = {
            HeadingLevel.H1: "h1",
            HeadingLevel.H2: "h2",
            HeadingLevel.H3: "h3",
        }[block.level]
        p = self.doc.add_paragraph(self._heading_text(block))
        self._set_paragraph_format(p, style_type)
        self._add_empty_paragraph("empty_after_header")
        self._rendered_body_blocks = True

    def _heading_text(self, block):
        if block.number != "auto":
            return block.text

        number = self._section_numberer.next_number(block.level.value)
        title = block.text.rstrip().removesuffix(".")
        return f"{number} {title}"

    def _render_structural_section(self, block):
        if block.section_type is StructuralSectionType.CONTENTS:
            self._render_table_of_contents(TableOfContentsNode(title=block.title, source=block.source))
            return

        if self.config.STRUCTURAL_SECTION["page_break_before"]:
            self.doc.add_page_break()

        title = block.title.upper() if self.config.STRUCTURAL_SECTION["uppercase"] else block.title
        p = self.doc.add_paragraph()
        run = p.add_run(title)
        self._set_paragraph_format(p, "structural_section")
        run.underline = False
        self._apply_word_heading_style(p, "Heading 1")
        self._add_empty_paragraph("empty_after_header")
        self._rendered_body_blocks = True

    def _render_title_page(self, metadata, profile_name=None):
        """Generate a title page from document metadata.

        Skipped when the renderer is composing into a template prefix that
        already provides its own title page (``template_mode='preserve-prefix'``)
        or when a title page has already been emitted for this document.

        When the effective profile declares an implemented ``title_page.form_*``
        rule, a profile-specific layout (document-type label, ``на тему:`` line,
        signatory blocks) is rendered and missing required metadata is reported
        as ``TXT_MISSING_METADATA`` diagnostics. Otherwise a generic title page
        is produced.
        """

        if self._template_mode == "preserve-prefix":
            return
        if self._title_page_emitted:
            return

        metadata = dict(metadata or {})
        profile = self._resolve_title_profile(profile_name)
        form_rule = self._title_form_rule(profile)

        if form_rule is not None:
            self._render_profile_title_page(metadata, form_rule)
        else:
            self._render_generic_title_page(metadata)

        self.doc.add_page_break()
        self._title_page_emitted = True

    def _resolve_title_profile(self, profile_name):
        if profile_name:
            try:
                return get_profile(profile_name)
            except KeyError:
                pass
        return self._profile

    @staticmethod
    def _title_form_rule(profile):
        if profile is None:
            return None
        for rule in profile.rules:
            if (
                rule.renderer_status is RuleStatus.IMPLEMENTED
                and ".title_page.form" in rule.id
                and "default_document_type" in rule.parameters
            ):
                return rule
        return None

    def _render_generic_title_page(self, metadata):
        ministry = metadata.get(
            "ministry",
            "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
        )
        university = metadata.get("university", "Сибирский федеральный университет")
        institute = metadata.get("institute", "")
        department = metadata.get("department", "")
        title = metadata.get("title", "")
        subject = metadata.get("subject", "")
        student = metadata.get("student", "")
        group = metadata.get("group", "")
        supervisor = metadata.get("supervisor", "")
        supervisor_title = metadata.get("supervisor_title", "")
        city = metadata.get("city", "Красноярск")
        year = metadata.get("year", "")

        self._add_title_paragraph(ministry.upper(), bold=False)
        self._add_title_paragraph(university.upper(), bold=True)
        if institute:
            self._add_title_paragraph(institute, bold=False)
        if department:
            self._add_title_paragraph(department, bold=False)

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        if subject:
            self._add_title_paragraph(subject.upper(), bold=False)
        if title:
            self._add_title_paragraph(title, bold=True, size=Pt(16))

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        if supervisor:
            label = "Руководитель"
            if supervisor_title:
                label = f"{label}, {supervisor_title}"
            self._add_title_paragraph(
                f"{label} ____________ {supervisor}",
                bold=False,
                align=WD_ALIGN_PARAGRAPH.RIGHT,
            )
        if student:
            label = "Студент"
            if group:
                label = f"{label} {group}"
            self._add_title_paragraph(
                f"{label} ____________ {student}",
                bold=False,
                align=WD_ALIGN_PARAGRAPH.RIGHT,
            )

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        if city or year:
            footer = " ".join(part for part in (city, year) if part)
            self._add_title_paragraph(footer, bold=False)

    def _render_profile_title_page(self, metadata, form_rule):
        self._report_missing_title_metadata(metadata, form_rule)

        ministry = metadata.get(
            "ministry",
            "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
        )
        university = metadata.get("university", "Сибирский федеральный университет")
        institute = metadata.get("institute", "")
        department = metadata.get("department", "")
        document_type = metadata.get("document_type") or form_rule.parameters["default_document_type"]
        title = metadata.get("title", "")
        teacher = metadata.get("teacher", "")
        supervisor = metadata.get("supervisor", "")
        supervisor_title = metadata.get("supervisor_title", "")
        student = metadata.get("student", "")
        group = metadata.get("group", "")
        record_book = metadata.get("record_book", "")
        city = metadata.get("city", "Красноярск")
        year = metadata.get("year", "")

        self._add_title_paragraph(ministry.upper(), bold=False)
        self._add_title_paragraph(university.upper(), bold=True)
        if institute:
            self._add_title_paragraph(institute, bold=False)
        if department:
            self._add_title_paragraph(department, bold=False)

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        self._add_title_paragraph(document_type, bold=True)
        if title:
            self._add_title_paragraph(f"на тему: {title}", bold=False)

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        if teacher:
            self._add_title_paragraph(
                f"Преподаватель ____________ {teacher}",
                bold=False,
                align=WD_ALIGN_PARAGRAPH.RIGHT,
            )
        if supervisor:
            label = "Руководитель"
            if supervisor_title:
                label = f"{label}, {supervisor_title}"
            self._add_title_paragraph(
                f"{label} ____________ {supervisor}",
                bold=False,
                align=WD_ALIGN_PARAGRAPH.RIGHT,
            )
        if student:
            label = "Студент"
            if group:
                label = f"{label} {group}"
            if record_book:
                label = f"{label}, № {record_book}"
            self._add_title_paragraph(
                f"{label} ____________ {student}",
                bold=False,
                align=WD_ALIGN_PARAGRAPH.RIGHT,
            )

        for _ in range(4):
            self._add_title_paragraph("", bold=False)

        if city or year:
            footer = " ".join(part for part in (city, year) if part)
            self._add_title_paragraph(footer, bold=False)

    def _report_missing_title_metadata(self, metadata, form_rule):
        required = form_rule.parameters.get("required_metadata", ())
        for field in required:
            if not metadata.get(field):
                self._title_page_diagnostics.append(
                    Diagnostic(
                        code=DiagnosticCodes.TXT_MISSING_METADATA,
                        message=f"Title page metadata field '{field}' is required for {form_rule.id}",
                        severity=Severity.WARNING,
                        rule_id=form_rule.id,
                        data={"field": field},
                    )
                )

    def _add_title_paragraph(self, text, *, bold=False, size=None, align=None):
        para = self.doc.add_paragraph()
        para.paragraph_format.alignment = align or WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.first_line_indent = Cm(0)
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1.0
        run = para.add_run(text)
        run.font.name = self.config.FONT_NAME
        run.font.size = size or self.config.FONT_SIZE
        run.font.color.rgb = RGBColor(*self.config.FONT_COLOR_RGB)
        run.bold = bold
        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), self.config.FONT_NAME)

    def _render_appendix(self, block):
        """Render ``ПРИЛОЖЕНИЕ X`` on a new page with the standard heading layout.

        STU 7.5-07-2021 requires: page break before, centered bold heading using
        Russian uppercase letters (no Ё, З, Й, О, Ч, Ъ, Ы, Ь), optional content
        type below, and an optional appendix title separated by one blank line.
        """

        self.doc.add_page_break()

        heading_text = block.title or "ПРИЛОЖЕНИЕ"
        if block.letter and block.letter not in heading_text:
            heading_text = f"ПРИЛОЖЕНИЕ {block.letter}"

        heading_para = self.doc.add_paragraph()
        heading_run = heading_para.add_run(heading_text.upper())
        self._set_paragraph_format(heading_para, "structural_section")
        heading_run.underline = False
        self._apply_word_heading_style(heading_para, "Heading 1")

        if block.appendix_type:
            type_para = self.doc.add_paragraph()
            type_run = type_para.add_run(f"({block.appendix_type})")
            self._set_paragraph_format(type_para, "caption_img")
            type_run.bold = False
            type_run.italic = False

        if block.subtitle:
            self._add_empty_paragraph("empty_after_header")
            subtitle_para = self.doc.add_paragraph()
            subtitle_run = subtitle_para.add_run(block.subtitle)
            self._set_paragraph_format(subtitle_para, "structural_section")
            subtitle_run.underline = False

        self._add_empty_paragraph("empty_after_header")
        if block.blocks:
            self._render_from_ast(Document(blocks=block.blocks))
        self._rendered_body_blocks = True

    def _render_table_of_contents(self, block):
        """Insert a ``СОДЕРЖАНИЕ`` heading and a Word TOC field.

        ``python-docx`` does not support TOCs natively, so we emit raw OOXML
        ``w:fldChar`` / ``w:instrText`` elements that Word recognises and
        updates on open (or via Ctrl+A, F9).
        """

        self.doc.add_page_break()

        heading_para = self.doc.add_paragraph()
        heading_run = heading_para.add_run((block.title or "СОДЕРЖАНИЕ").upper())
        self._set_paragraph_format(heading_para, "structural_section")
        heading_run.underline = False
        self._apply_word_heading_style(heading_para, "Heading 1")

        self._add_empty_paragraph("empty_after_header")

        toc_para = self.doc.add_paragraph()
        toc_para.paragraph_format.first_line_indent = Cm(0)
        begin_run = toc_para.add_run()
        self._set_run_style(begin_run, bold=False)
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        begin_run._element.append(fld_begin)

        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = f' TOC \\o "1-{block.levels}" \\h \\z \\u '
        begin_run._element.append(instr)

        fld_separate = OxmlElement("w:fldChar")
        fld_separate.set(qn("w:fldCharType"), "separate")
        begin_run._element.append(fld_separate)

        placeholder_run = toc_para.add_run("Обновите оглавление (Ctrl+A, F9)")
        self._set_run_style(placeholder_run, bold=False)

        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        placeholder_run._element.append(fld_end)

        self._rendered_body_blocks = True

    def _apply_word_heading_style(self, paragraph, style_name):
        """Attach a built-in heading style so the TOC field can find the entry.

        We only assign ``pStyle``; the formatting parameters from the registry
        already win because ``_set_paragraph_format`` overrides spacing,
        alignment, and run properties after the style is applied.
        """

        if self.doc is None:
            return
        try:
            paragraph.style = self.doc.styles[style_name]
        except KeyError:
            return

    def _render_paragraph(self, block):
        para = self.doc.add_paragraph()
        for text_run in block.runs:
            para.add_run(text_run.text)
        self._set_paragraph_format(para, "normal")
        for docx_run, text_run in zip(para.runs, block.runs, strict=False):
            self._set_run_style(
                docx_run,
                bold=text_run.bold,
                italic=text_run.italic,
            )
        self._rendered_body_blocks = True

    def _render_text_block(self, text):
        p = self.doc.add_paragraph(text)
        self._set_paragraph_format(p, "normal")
        self._rendered_body_blocks = True

    def _render_formula(self, block):
        """Render a formula on its own line with right-aligned auto-number."""

        if block.number == "auto" or block.number is None:
            self._formula_counter += 1
            number_text = str(self._formula_counter)
        else:
            number_text = str(block.number)

        self._add_empty_paragraph("empty_before_formula")

        para = self.doc.add_paragraph()
        self._set_paragraph_format(para, "formula")
        # Replace the placeholder run created by _set_paragraph_format with
        # explicit content + tab + number runs so styling stays consistent.
        for run in list(para.runs):
            run._element.getparent().remove(run._element)

        content_run = para.add_run(block.content or "")
        self._set_run_style(content_run, bold=False)

        number_run = para.add_run(f"\t({number_text})")
        self._set_run_style(number_run, bold=False)

        self._set_formula_number_tab(para)

        if block.explanation:
            expl_para = self.doc.add_paragraph(block.explanation)
            self._set_paragraph_format(expl_para, "formula_explanation")

        self._add_empty_paragraph("empty_after_formula")
        self._rendered_body_blocks = True

    def _set_formula_number_tab(self, para):
        """Add a right-aligned tab stop so ``\\t(N)`` lands at the right margin."""

        tab_pos = self.config.FORMULA["number_tab_pos"]
        ppr = para._p.get_or_add_pPr()
        existing = ppr.find(qn("w:tabs"))
        if existing is not None:
            ppr.remove(existing)

        tab_stops = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:pos"), str(int(tab_pos.emu / 635)))
        tab_stops.append(tab)
        ppr.append(tab_stops)

    def _render_bibliography_entry(self, block):
        """Render a single source list entry with hanging-paragraph layout."""

        text = f"{block.number} {block.text}"
        para = self.doc.add_paragraph(text)
        self._set_paragraph_format(para, "bibliography_entry")
        self._rendered_body_blocks = True

    def _render_list(self, block):
        for index, item in enumerate(block.items):
            text = self._list_item_text(
                list_type=block.list_type,
                index=index,
                item_text=item.text,
                is_last=index == len(block.items) - 1,
            )
            p = self.doc.add_paragraph(text)
            self._set_paragraph_format(p, "list_item")
        if block.items:
            self._rendered_body_blocks = True

    def _list_item_text(self, list_type, index, item_text, is_last):
        text = _normalize_list_item_punctuation(
            item_text,
            list_type=list_type,
            is_last=is_last,
        )
        if list_type is ListType.BULLET:
            return f"- {text}"
        if list_type is ListType.LETTERED:
            return f"{_russian_list_letter(index)}) {text}"
        if list_type is ListType.NUMBERED:
            return f"{index + 1}) {text}"
        raise ValueError(f"Unsupported list type: {list_type}")

    def _resolve_image_path(self, image_path):
        path = Path(image_path)
        if path.is_absolute():
            return path
        return self.base_dir / PathConfig.IMAGES_DIR / path

    def _resolve_template_path(self, template_path):
        path = Path(template_path)
        if path.is_absolute():
            return path

        for candidate in (
            self.base_dir / PathConfig.TEMPLATES_DIR / path,
            self.base_dir / path,
        ):
            if candidate.exists():
                return candidate
        return self.base_dir / PathConfig.TEMPLATES_DIR / path


def _normalize_list_item_punctuation(
    text: str,
    *,
    list_type: ListType,
    is_last: bool,
) -> str:
    stripped = text.strip()
    if not stripped or stripped.endswith((".", ";")):
        return stripped

    ending = "." if list_type is ListType.NUMBERED or is_last else ";"
    return f"{stripped}{ending}"


def _russian_list_letter(index: int) -> str:
    if index < len(_RUSSIAN_LIST_LETTERS):
        return _RUSSIAN_LIST_LETTERS[index]
    return str(index + 1)


def _normalize_caption_dashes(text: str) -> str:
    """Replace ASCII hyphens used as dash separators with em-dash (U+2014)."""

    return re.sub(r"\s[-–]\s", " — ", text)
