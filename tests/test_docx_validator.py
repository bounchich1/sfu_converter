from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.infrastructure.docx_validator import (
    DocxValidator,
    _pt_value,
    _slug,
    _spacing_value,
    diagnostic_to_json,
)
from sfu_converter.registry import get_profile


def _save_doc(tmp_path, doc, name="document.docx"):
    path = tmp_path / name
    doc.save(str(path))
    return path


def _body_paragraph(doc, text="Body"):
    paragraph = doc.add_paragraph(text)
    paragraph.paragraph_format.first_line_indent = Cm(1.25)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.runs[0]
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    return paragraph


def test_docx_validator_returns_structured_margin_diagnostic_with_rule_id(tmp_path):
    doc = Document()
    section = doc.sections[0]
    section.left_margin = Cm(2)
    section.right_margin = Cm(1)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    _body_paragraph(doc)
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))

    diagnostic = next(
        diag for diag in diagnostics if diag.code == DiagnosticCodes.FORMAT_MARGIN_LEFT
    )
    assert diagnostic.rule_id == "common.page.margins.portrait"

    payload = diagnostic_to_json(diagnostic)
    assert payload["code"] == "FORMAT_MARGIN_LEFT"
    assert payload["severity"] == "error"
    assert payload["ruleId"] == "common.page.margins.portrait"
    assert payload["source"].startswith("docs/formatting requirements/common.md#")


def test_docx_validator_reports_common_unsupported_validator_rules(tmp_path):
    doc = Document()
    _body_paragraph(doc)
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))
    unsupported = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.code == DiagnosticCodes.FORMAT_RULE_NOT_SUPPORTED
    ]

    assert len(unsupported) == 18
    assert all(diagnostic.severity is Severity.WARNING for diagnostic in unsupported)
    assert all("not supported by the validator" in diagnostic.message for diagnostic in unsupported)

    payload = diagnostic_to_json(unsupported[0])
    assert payload["ruleId"] == unsupported[0].rule_id
    assert payload["source"].startswith("docs/formatting requirements/common.md#")


def test_docx_validator_checks_line_spacing_regression(tmp_path):
    doc = Document()
    paragraph = _body_paragraph(doc)
    paragraph.paragraph_format.line_spacing = 1.0
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))

    assert any(
        diagnostic.code == DiagnosticCodes.FORMAT_LINE_SPACING
        and diagnostic.rule_id == "common.text.line_spacing"
        for diagnostic in diagnostics
    )


def test_docx_validator_checks_every_run_in_paragraph(tmp_path):
    doc = Document()
    paragraph = _body_paragraph(doc, "Good")
    bad_run = paragraph.add_run(" bad")
    bad_run.font.name = "Arial"
    bad_run.font.size = Pt(14)
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))

    assert any(
        diagnostic.code == DiagnosticCodes.FORMAT_FONT_NAME
        and "run 2" in diagnostic.message
        for diagnostic in diagnostics
    )


def test_docx_validator_heading_detection_uses_style_or_bold_centering():
    validator = DocxValidator(get_profile("common"))
    doc = Document()

    centered_caption = doc.add_paragraph("Рисунок 1 - Caption")
    centered_caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    centered_caption.runs[0].bold = False

    heading_style = doc.add_paragraph("Heading")
    heading_style.style = doc.styles["Heading 1"]

    centered_bold = doc.add_paragraph("Centered bold")
    centered_bold.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    centered_bold.runs[0].bold = True

    assert validator._is_heading_paragraph(centered_caption) is False
    assert validator._is_heading_paragraph(heading_style) is True
    assert validator._is_heading_paragraph(centered_bold) is True


def test_docx_validator_checks_table_font_size_range(tmp_path):
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    run = table.cell(0, 0).paragraphs[0].add_run("oversized")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))

    assert any(
        diagnostic.code == DiagnosticCodes.FORMAT_TABLE_FONT_SIZE
        and diagnostic.rule_id == "common.table.font.size"
        for diagnostic in diagnostics
    )


def test_docx_validator_rejects_heading_period(tmp_path):
    doc = Document()
    heading = doc.add_paragraph("Heading.")
    heading.style = doc.styles["Heading 1"]
    heading.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.line_spacing = 1.0
    heading.runs[0].font.name = "Times New Roman"
    heading.runs[0].font.size = Pt(14)
    heading.runs[0].bold = True
    path = _save_doc(tmp_path, doc)

    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))

    assert any(
        diagnostic.code == DiagnosticCodes.FORMAT_HEADING_NO_PERIOD
        and diagnostic.rule_id == "common.heading.no_period"
        for diagnostic in diagnostics
    )


def test_docx_validator_reports_missing_and_unopenable_files(tmp_path):
    validator = DocxValidator(get_profile("common"))

    missing = validator.validate_file(str(tmp_path / "missing.docx"))
    assert missing[0].code == "DOCX_FILE_NOT_FOUND"

    invalid = tmp_path / "invalid.docx"
    invalid.write_text("not a docx", encoding="utf-8")
    failed = validator.validate_file(str(invalid))
    assert failed[0].code == "DOCX_OPEN_FAILED"


def test_docx_validator_covers_heading_variants_and_format_errors(tmp_path):
    doc = Document()
    h2 = doc.add_paragraph("Heading 2")
    h2.style = doc.styles["Heading 2"]
    h2.paragraph_format.first_line_indent = Cm(1)
    h2.paragraph_format.line_spacing = 2.0
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    h2.runs[0].font.name = "Arial"
    h2.runs[0].font.size = Pt(16)
    h2.runs[0].font.color.rgb = RGBColor(255, 0, 0)
    h2.runs[0].bold = False

    h3 = doc.add_paragraph("Heading 3")
    h3.style = doc.styles["Heading 3"]
    h3.paragraph_format.first_line_indent = Cm(0)
    h3.paragraph_format.line_spacing = 1.0
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h3.paragraph_format.space_before = Pt(2)
    h3.paragraph_format.space_after = Pt(2)
    h3.runs[0].font.name = "Times New Roman"
    h3.runs[0].font.size = Pt(14)

    path = _save_doc(tmp_path, doc)
    diagnostics = DocxValidator(get_profile("common")).validate_file(str(path))
    codes = {diagnostic.code for diagnostic in diagnostics}

    assert DiagnosticCodes.FORMAT_FONT_NAME in codes
    assert DiagnosticCodes.FORMAT_FONT_SIZE in codes
    assert DiagnosticCodes.FORMAT_FONT_COLOR in codes
    assert DiagnosticCodes.FORMAT_INDENT in codes
    assert DiagnosticCodes.FORMAT_ALIGNMENT in codes
    assert DiagnosticCodes.FORMAT_HEADING_BOLD in codes
    assert DiagnosticCodes.FORMAT_PARAGRAPH_SPACING in codes


def test_docx_validator_helpers_cover_optional_json_fields():
    diagnostic = Diagnostic(
        code="CODE",
        message="Message",
        severity=Severity.WARNING,
        rule_id="common.text.font.name",
        suggestion="Suggestion",
    )

    payload = diagnostic_to_json(diagnostic)
    assert payload["suggestion"] == "Suggestion"
    assert payload["source"].startswith("docs/formatting requirements/common.md#")
    assert _pt_value(None) == 0
    assert _pt_value(2.5) == 2.5
    assert _spacing_value(Pt(12)) == 12
    assert _spacing_value(1.5) == 1.5
    assert _slug(" Section Name ") == "section-name"

    without_rule = diagnostic_to_json(
        Diagnostic(code="NO_RULE", message="Message", severity=Severity.ERROR)
    )
    assert "ruleId" not in without_rule

    assert (
        DocxValidator(FormattingProfile("empty", "Empty", ()))._rule(
            "common.text.font.name"
        ).id
        == "common.text.font.name"
    )

