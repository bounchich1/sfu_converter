from pathlib import Path

from docx import Document as DocxDocument

from sfu_converter.converter import TextToDocxConverter
from sfu_converter.domain.ast_nodes import (
    FigureNode,
    HeadingLevel,
    HeadingNode,
    ParagraphNode,
    StructuralSectionNode,
    StructuralSectionType,
    TableNode,
)
from sfu_converter.domain.diagnostics import DiagnosticCodes, Severity
from sfu_converter.parser.v1_parser import V1Parser


def test_parse_v1_headings_plain_text_image_and_table():
    source = "\n".join(
        [
            "[H1] Введение",
            "Обычный текст",
            "[H2] Глава 1",
            "[H3] Подраздел",
            "[IMAGE=diagram.png]",
            "Рисунок 1 - Схема",
            "[TABLE_START]",
            "[TABLE_CAPTION] Таблица 1 - Данные",
            "| A | B |",
            "| C | D |",
            "[TABLE_END]",
        ]
    )

    result = V1Parser().parse(source, filename="report.txt")

    assert result.diagnostics == []
    assert result.document.syntax_version == 1
    assert result.document.source_file == "report.txt"
    assert [type(block) for block in result.document.blocks] == [
        StructuralSectionNode,
        ParagraphNode,
        HeadingNode,
        HeadingNode,
        FigureNode,
        TableNode,
    ]
    assert result.document.blocks[0].section_type is StructuralSectionType.INTRODUCTION
    assert result.document.blocks[1].runs[0].text == "Обычный текст"
    assert result.document.blocks[4].src == "diagram.png"
    assert result.document.blocks[4].caption == "Рисунок 1 - Схема"
    assert result.document.blocks[5].caption == "Таблица 1 - Данные"
    assert result.document.blocks[5].rows[1].cells[1].text == "D"


def test_parse_complete_fixture_file_to_expected_logical_blocks():
    source = Path("tests/test_input.txt").read_text(encoding="utf-8")

    result = V1Parser().parse(source, filename="tests/test_input.txt")

    assert result.diagnostics == []
    assert len(result.document.blocks) == 12
    assert [type(block).__name__ for block in result.document.blocks] == [
        "StructuralSectionNode",
        "ParagraphNode",
        "HeadingNode",
        "ParagraphNode",
        "ParagraphNode",
        "FigureNode",
        "ParagraphNode",
        "TableNode",
        "ParagraphNode",
        "ParagraphNode",
        "HeadingNode",
        "ParagraphNode",
    ]


def test_parser_converts_known_h1_to_structural_section():
    result = V1Parser().parse("[H1] введение\n[H1] Обычный раздел")

    assert result.diagnostics == []
    structural, regular = result.document.blocks
    assert isinstance(structural, StructuralSectionNode)
    assert structural.section_type is StructuralSectionType.INTRODUCTION
    assert structural.title == "введение"
    assert isinstance(regular, HeadingNode)
    assert regular.level is HeadingLevel.H1
    assert regular.text == "Обычный раздел"


def test_parser_recognizes_explicit_structural_markers():
    result = V1Parser().parse(
        "\n".join(
            [
                "[SECTION type=conclusion]",
                '[STRUCTURAL title="СПИСОК СОКРАЩЕНИЙ"]',
            ]
        )
    )

    assert result.diagnostics == []
    first, second = result.document.blocks
    assert first == StructuralSectionNode(
        section_type=StructuralSectionType.CONCLUSION,
        title="ЗАКЛЮЧЕНИЕ",
        source=first.source,
    )
    assert second == StructuralSectionNode(
        section_type=StructuralSectionType.ABBREVIATIONS,
        title="СПИСОК СОКРАЩЕНИЙ",
        source=second.source,
    )


def test_parser_reports_cyrillic_marker_lookalikes_with_line_numbers():
    result = V1Parser().parse("[Н1] Wrong marker", filename="bad.txt")

    assert any(
        diagnostic.code == DiagnosticCodes.TXT_CYRILLIC_IN_MARKER
        and diagnostic.severity is Severity.ERROR
        and diagnostic.source.line_start == 1
        and diagnostic.source.filename == "bad.txt"
        for diagnostic in result.diagnostics
    )
    assert result.has_errors is True


def test_parser_reports_unknown_marker_warning():
    result = V1Parser().parse("[UNKNOWN] value")

    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == DiagnosticCodes.TXT_UNKNOWN_MARKER
    assert diagnostic.severity is Severity.WARNING
    assert diagnostic.source.line_start == 1
    assert result.has_errors is False


def test_parser_reports_missing_table_end_and_preserves_rows():
    result = V1Parser().parse(
        "\n".join(
            [
                "Before",
                "[TABLE_START]",
                "| A | B |",
                "| C | D |",
            ]
        )
    )

    assert result.document.blocks[1].rows[0].cells[0].text == "A"
    assert result.diagnostics[0].code == DiagnosticCodes.TXT_MISSING_BLOCK_END
    assert result.diagnostics[0].severity is Severity.ERROR
    assert result.diagnostics[0].source.line_start == 2
    assert result.has_errors is True


def test_parser_reports_invalid_table_shape():
    result = V1Parser().parse(
        "\n".join(
            [
                "[TABLE_START]",
                "| A | B |",
                "| C |",
                "[TABLE_END]",
            ]
        )
    )

    assert result.diagnostics[0].code == DiagnosticCodes.TXT_INVALID_TABLE_SHAPE
    assert result.diagnostics[0].source.line_start == 3
    assert result.has_errors is True


def test_image_without_caption_and_empty_image_marker():
    result = V1Parser().parse("[IMAGE=chart.png]\n\n[IMAGE]")

    first, second = result.document.blocks
    assert first.src == "chart.png"
    assert first.caption is None
    assert first.source.line_start == 1
    assert second.src is None
    assert second.caption is None
    assert second.source.line_start == 3


def test_parser_reports_malformed_image_tag():
    result = V1Parser().parse("[IMAGE=chart.png")

    assert result.document.blocks == ()
    assert result.diagnostics[0].code == DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE
    assert result.diagnostics[0].severity is Severity.ERROR
    assert result.diagnostics[0].source.line_start == 1


def test_empty_input_returns_empty_document_without_diagnostics():
    result = V1Parser().parse("")

    assert result.document.blocks == ()
    assert result.document.syntax_version == 1
    assert result.diagnostics == []
    assert result.has_errors is False


def test_parser_module_is_independent_from_python_docx():
    parser_source = Path("src/sfu_converter/parser/v1_parser.py").read_text(encoding="utf-8")

    assert "docx" not in parser_source.lower()


def test_converter_renders_preparsed_ast(tmp_path):
    parser_result = V1Parser().parse(
        "\n".join(
            [
                "[H1] Заголовок",
                "Абзац",
                "[TABLE_START]",
                "| A | B |",
                "| C | D |",
                "[TABLE_END]",
            ]
        )
    )
    output_file = tmp_path / "ast.docx"
    converter = TextToDocxConverter(base_dir=tmp_path)
    converter._initialize_document()

    converter._render_lines(parser_result.document)
    converter.doc.save(str(output_file))

    doc = DocxDocument(str(output_file))
    assert [paragraph.text for paragraph in doc.paragraphs if paragraph.text] == [
        "Заголовок",
        "Абзац",
    ]
    assert doc.tables[0].rows[1].cells[1].text == "D"
