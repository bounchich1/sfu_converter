from pathlib import Path

from docx import Document as DocxDocument

from sfu_converter.converter import TextToDocxConverter
from sfu_converter.domain.ast_nodes import (
    FigureNode,
    HeadingLevel,
    HeadingNode,
    ListNode,
    ListType,
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
    assert regular.number == "auto"


def test_parser_marks_regular_headings_for_auto_numbering():
    result = V1Parser().parse(
        "\n".join(
            [
                "[H1] Раздел",
                "[H2] Подраздел",
                "[H3] Пункт",
            ]
        )
    )

    assert result.diagnostics == []
    assert [
        (block.level, block.text, block.number)
        for block in result.document.blocks
    ] == [
        (HeadingLevel.H1, "Раздел", "auto"),
        (HeadingLevel.H2, "Подраздел", "auto"),
        (HeadingLevel.H3, "Пункт", "auto"),
    ]


def test_parser_groups_consecutive_dash_lines_into_bullet_list():
    result = V1Parser().parse(
        "\n".join(
            [
                "Перед списком",
                "- первый элемент",
                "- второй элемент;",
                "- третий элемент.",
                "После списка",
            ]
        ),
        filename="list.txt",
    )

    assert result.diagnostics == []
    before, list_block, after = result.document.blocks
    assert before.runs[0].text == "Перед списком"
    assert after.runs[0].text == "После списка"
    assert isinstance(list_block, ListNode)
    assert list_block.list_type is ListType.BULLET
    assert [item.text for item in list_block.items] == [
        "первый элемент",
        "второй элемент;",
        "третий элемент.",
    ]
    assert list_block.source.line_start == 2
    assert list_block.source.line_end == 4


def test_parser_parses_explicit_lettered_and_numbered_lists():
    result = V1Parser().parse(
        "\n".join(
            [
                "[LIST type=letter]",
                "[а)] первый элемент",
                "[б)] второй элемент",
                "[LIST_END]",
                "[LIST type=number]",
                "[1)] первый подпункт",
                "[2)] второй подпункт",
                "[LIST_END]",
            ]
        )
    )

    assert result.diagnostics == []
    lettered, numbered = result.document.blocks
    assert lettered.list_type is ListType.LETTERED
    assert [item.text for item in lettered.items] == [
        "первый элемент",
        "второй элемент",
    ]
    assert numbered.list_type is ListType.NUMBERED
    assert [item.text for item in numbered.items] == [
        "первый подпункт",
        "второй подпункт",
    ]


def test_parser_accepts_empty_explicit_list():
    result = V1Parser().parse("[LIST type=bullet]\n[LIST_END]")

    assert result.diagnostics == []
    (list_block,) = result.document.blocks
    assert isinstance(list_block, ListNode)
    assert list_block.list_type is ListType.BULLET
    assert list_block.items == ()


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


def test_parser_splits_paragraph_into_bold_italic_runs():
    result = V1Parser().parse(
        "Hello **bold** and *italic* and ***bold italic*** done."
    )

    assert result.diagnostics == []
    (paragraph,) = result.document.blocks
    assert isinstance(paragraph, ParagraphNode)
    assert [
        (run.text, run.bold, run.italic) for run in paragraph.runs
    ] == [
        ("Hello ", False, False),
        ("bold", True, False),
        (" and ", False, False),
        ("italic", False, True),
        (" and ", False, False),
        ("bold italic", True, True),
        (" done.", False, False),
    ]


def test_parser_returns_single_run_when_no_inline_formatting():
    result = V1Parser().parse("Просто обычный текст без форматирования.")

    (paragraph,) = result.document.blocks
    assert len(paragraph.runs) == 1
    assert paragraph.runs[0].text == "Просто обычный текст без форматирования."
    assert paragraph.runs[0].bold is False
    assert paragraph.runs[0].italic is False


def test_parser_treats_unmatched_asterisks_as_literal_text():
    result = V1Parser().parse("Простой * одиночный знак и **незакрытый текст")

    (paragraph,) = result.document.blocks
    rendered = "".join(run.text for run in paragraph.runs)
    assert rendered == "Простой * одиночный знак и **незакрытый текст"
    assert all(run.bold is False and run.italic is False for run in paragraph.runs)


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
        "1 Заголовок",
        "Абзац",
    ]
    assert doc.tables[0].rows[1].cells[1].text == "D"
