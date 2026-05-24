from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.ast_nodes import (
    Document,
    HeadingLevel,
    HeadingNode,
    ListItemNode,
    ListNode,
    ListType,
    ParagraphNode,
    StructuralSectionNode,
    StructuralSectionType,
    TableCell,
    TableNode,
    TableRow,
    TextRun,
)
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.infrastructure.docx_renderer import DocxRenderer, SectionNumberer
from sfu_converter.ports.renderer import RendererPort


def assert_close(actual, expected) -> None:
    assert abs(actual - expected) < 1000


def test_docx_renderer_renders_ast_to_file(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            HeadingNode(level=HeadingLevel.H1, text="Title"),
            ParagraphNode(runs=(TextRun("Body"),)),
            TableNode(
                caption="Table 1",
                rows=(
                    TableRow(cells=(TableCell("A"), TableCell("B"))),
                    TableRow(cells=(TableCell("1"), TableCell("2"))),
                ),
            ),
        )
    )
    output_path = tmp_path / "rendered.docx"

    diagnostics = renderer.render_to_file(ast, profile, str(output_path))

    assert diagnostics == []
    assert output_path.exists()

    doc = DocxDocument(str(output_path))
    assert [para.text for para in doc.paragraphs if para.text] == [
        "Title",
        "Body",
        "Таблица 1 — Table 1",
    ]
    assert doc.paragraphs[0].paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert len(doc.tables) == 1
    assert doc.tables[0].rows[1].cells[1].text == "2"


def test_section_numberer_tracks_hierarchical_numbers():
    numberer = SectionNumberer()

    assert numberer.next_number(1) == "1"
    assert numberer.next_number(2) == "1.1"
    assert numberer.next_number(2) == "1.2"
    assert numberer.next_number(3) == "1.2.1"
    assert numberer.next_number(1) == "2"
    assert numberer.next_number(2) == "2.1"

    numberer.reset()

    assert numberer.next_number(1) == "1"


def test_docx_renderer_renders_auto_numbered_headings_without_trailing_period(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            HeadingNode(level=HeadingLevel.H1, text="Первый раздел", number="auto"),
            HeadingNode(level=HeadingLevel.H2, text="Первый подраздел", number="auto"),
            HeadingNode(level=HeadingLevel.H3, text="Первый пункт", number="auto"),
            HeadingNode(level=HeadingLevel.H1, text="Второй раздел", number="auto"),
            HeadingNode(level=HeadingLevel.H2, text="Новый подраздел", number="auto"),
        )
    )
    output_path = tmp_path / "numbered.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    assert [paragraph.text for paragraph in doc.paragraphs if paragraph.text] == [
        "1 Первый раздел",
        "1.1 Первый подраздел",
        "1.1.1 Первый пункт",
        "2 Второй раздел",
        "2.1 Новый подраздел",
    ]


def test_docx_renderer_renders_list_items_with_sfu_markers_and_formatting(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            ListNode(
                list_type=ListType.BULLET,
                items=(
                    ListItemNode("первый элемент"),
                    ListItemNode("второй элемент"),
                ),
            ),
            ListNode(
                list_type=ListType.LETTERED,
                items=(
                    ListItemNode("первый вариант"),
                    ListItemNode("второй вариант"),
                ),
            ),
            ListNode(
                list_type=ListType.NUMBERED,
                items=(
                    ListItemNode("подпункт один"),
                    ListItemNode("подпункт два"),
                ),
            ),
        )
    )
    output_path = tmp_path / "lists.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    paragraphs = [paragraph for paragraph in doc.paragraphs if paragraph.text]
    assert [paragraph.text for paragraph in paragraphs] == [
        "- первый элемент;",
        "- второй элемент.",
        "а) первый вариант;",
        "б) второй вариант.",
        "1) подпункт один.",
        "2) подпункт два.",
    ]
    for paragraph in paragraphs:
        assert paragraph.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
        assert_close(paragraph.paragraph_format.first_line_indent, Cm(1.25))
        assert paragraph.paragraph_format.line_spacing == 1.5


def test_docx_renderer_adds_page_numbering_to_default_footer(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)

    renderer._initialize_document()

    section = renderer.doc.sections[0]
    assert section.different_first_page_header_footer is True

    footer = section.footer
    assert footer.is_linked_to_previous is False
    assert " PAGE " in footer._element.xml

    paragraph = footer.paragraphs[0]
    assert paragraph.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert_close(paragraph.paragraph_format.first_line_indent, Cm(0))

    run = paragraph.runs[0]
    assert run.font.name == SIBFUConfig.FONT_NAME
    assert run.font.size == Pt(14)
    assert run.font.color.rgb == RGBColor(0, 0, 0)

    first_page_footer = section.first_page_footer
    assert first_page_footer.paragraphs[0].text == ""
    assert " PAGE " not in first_page_footer._element.xml


def test_docx_renderer_renders_structural_sections_with_special_formatting(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            StructuralSectionNode(
                section_type=StructuralSectionType.INTRODUCTION,
                title="введение",
            ),
            ParagraphNode(runs=(TextRun("Body"),)),
        )
    )
    output_path = tmp_path / "structural.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    texts = [paragraph.text for paragraph in doc.paragraphs]
    heading_index = texts.index("ВВЕДЕНИЕ")
    heading = doc.paragraphs[heading_index]

    assert heading_index > 0
    assert 'w:type="page"' in doc.paragraphs[heading_index - 1]._p.xml
    assert doc.paragraphs[heading_index + 1].text == ""
    assert "Body" in texts

    assert heading.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert_close(heading.paragraph_format.first_line_indent, Cm(0))
    assert heading.paragraph_format.line_spacing == 1.0
    assert heading.runs[0].bold is True
    assert heading.runs[0].underline is False


def test_docx_renderer_implements_renderer_port():
    assert issubclass(DocxRenderer, RendererPort)


def test_docx_renderer_renders_paragraph_with_bold_and_italic_runs(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            ParagraphNode(
                runs=(
                    TextRun(text="Plain "),
                    TextRun(text="bold", bold=True),
                    TextRun(text=" and "),
                    TextRun(text="italic", italic=True),
                    TextRun(text=" and "),
                    TextRun(text="both", bold=True, italic=True),
                    TextRun(text="."),
                ),
            ),
        )
    )
    output_path = tmp_path / "inline.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    paragraph = next(p for p in doc.paragraphs if p.text)
    assert paragraph.text == "Plain bold and italic and both."
    assert [
        (run.text, bool(run.bold), bool(run.font.italic))
        for run in paragraph.runs
    ] == [
        ("Plain ", False, False),
        ("bold", True, False),
        (" and ", False, False),
        ("italic", False, True),
        (" and ", False, False),
        ("both", True, True),
        (".", False, False),
    ]


def test_docx_renderer_paragraph_runs_share_font_settings(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            ParagraphNode(
                runs=(
                    TextRun(text="Жирный фрагмент", bold=True),
                    TextRun(text=" и обычный текст."),
                ),
            ),
        )
    )
    output_path = tmp_path / "inline_font.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    paragraph = next(p for p in doc.paragraphs if p.text)
    for run in paragraph.runs:
        assert run.font.name == SIBFUConfig.FONT_NAME
        assert run.font.size == SIBFUConfig.FONT_SIZE
        assert run.font.color.rgb == RGBColor(*SIBFUConfig.FONT_COLOR_RGB)


def test_docx_renderer_table_uses_configured_font_size_and_header_bold(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            TableNode(
                rows=(
                    TableRow(cells=(TableCell("H1"), TableCell("H2"))),
                    TableRow(cells=(TableCell("A"), TableCell("B"))),
                ),
            ),
        )
    )
    output_path = tmp_path / "table_font.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    table = doc.tables[0]
    header_run = table.rows[0].cells[0].paragraphs[0].runs[0]
    body_run = table.rows[1].cells[0].paragraphs[0].runs[0]

    assert header_run.font.size == SIBFUConfig.TABLE["font_size"]
    assert body_run.font.size == SIBFUConfig.TABLE["font_size"]
    assert header_run.bold is True
    assert body_run.bold is False
    assert header_run.font.italic is not True
    body_para = table.rows[1].cells[0].paragraphs[0]
    assert body_para.paragraph_format.line_spacing == SIBFUConfig.TABLE["line_spacing"]


def test_docx_renderer_table_caption_normalizes_to_em_dash(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            TableNode(
                caption="Данные",
                rows=(TableRow(cells=(TableCell("A"),)),),
            ),
            TableNode(
                caption="Таблица 7 - Существующая",
                rows=(TableRow(cells=(TableCell("B"),)),),
            ),
        )
    )
    output_path = tmp_path / "captions.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    captions = [p.text for p in doc.paragraphs if p.text.startswith("Таблица")]
    assert captions == [
        "Таблица 1 — Данные",
        "Таблица 7 — Существующая",
    ]


def test_docx_renderer_sets_repeat_header_row_property_on_tables(tmp_path):
    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    ast = Document(
        blocks=(
            TableNode(
                rows=(
                    TableRow(cells=(TableCell("H1"), TableCell("H2"))),
                    TableRow(cells=(TableCell("A"), TableCell("B"))),
                ),
            ),
        )
    )
    output_path = tmp_path / "repeat_header.docx"

    renderer.render_to_file(ast, profile, str(output_path))

    doc = DocxDocument(str(output_path))
    header_row = doc.tables[0].rows[0]
    assert "tblHeader" in header_row._tr.xml
    body_row = doc.tables[0].rows[1]
    assert "tblHeader" not in body_row._tr.xml
