from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.ast_nodes import (
    Document,
    HeadingLevel,
    HeadingNode,
    ParagraphNode,
    StructuralSectionNode,
    StructuralSectionType,
    TableCell,
    TableNode,
    TableRow,
    TextRun,
)
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.infrastructure.docx_renderer import DocxRenderer
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
        "Table 1",
    ]
    assert doc.paragraphs[0].paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert len(doc.tables) == 1
    assert doc.tables[0].rows[1].cells[1].text == "2"


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
