from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.ast_nodes import (
    Document,
    HeadingLevel,
    HeadingNode,
    ParagraphNode,
    TableCell,
    TableNode,
    TableRow,
    TextRun,
)
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.infrastructure.docx_renderer import DocxRenderer
from sfu_converter.ports.renderer import RendererPort


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


def test_docx_renderer_implements_renderer_port():
    assert issubclass(DocxRenderer, RendererPort)
