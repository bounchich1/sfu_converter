from sfu_converter.application.convert import ConvertTextToDocx
from sfu_converter.domain.ast_nodes import Document, ParagraphNode, TextRun
from sfu_converter.domain.diagnostics import Diagnostic, Severity
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.parser.base import ParserResult


class FakeParser:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def parse(self, source, filename=None):
        self.calls.append((source, filename))
        return self.result


class FakeRenderer:
    def __init__(self, diagnostics=None):
        self.diagnostics = diagnostics or []
        self.calls = []

    def render(self, document, profile, template_path=None):
        return b"unused"

    def render_to_file(self, document, profile, output_path, template_path=None):
        self.calls.append((document, profile, output_path, template_path))
        return self.diagnostics


def test_convert_text_to_docx_parses_source_and_renders_document():
    document = Document(blocks=(ParagraphNode(runs=(TextRun("Body"),)),))
    parse_diagnostic = Diagnostic("TXT_WARNING", "warning", Severity.WARNING)
    render_diagnostic = Diagnostic("RENDER_WARNING", "warning", Severity.WARNING)
    parser = FakeParser(ParserResult(document, [parse_diagnostic]))
    renderer = FakeRenderer([render_diagnostic])
    profile = FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )
    use_case = ConvertTextToDocx(parser, renderer)

    diagnostics = use_case.execute(
        "source text",
        profile,
        "out.docx",
        template_path="template.docx",
        filename="input.txt",
    )

    assert parser.calls == [("source text", "input.txt")]
    assert renderer.calls == [(document, profile, "out.docx", "template.docx")]
    assert diagnostics == [parse_diagnostic, render_diagnostic]
