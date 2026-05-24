from __future__ import annotations

from sfu_converter.domain.diagnostics import Diagnostic
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.parser.base import BaseParser
from sfu_converter.ports.renderer import RendererPort


class ConvertTextToDocx:
    def __init__(self, parser: BaseParser, renderer: RendererPort):
        self._parser = parser
        self._renderer = renderer

    def execute(
        self,
        source: str,
        profile: FormattingProfile,
        output_path: str,
        template_path: str | None = None,
        template_mode: str = "append",
        filename: str | None = None,
    ) -> list[Diagnostic]:
        result = self._parser.parse(source, filename)
        diagnostics = list(result.diagnostics)
        diagnostics.extend(
            self._renderer.render_to_file(
                result.document,
                profile,
                output_path,
                template_path,
                template_mode,
            )
        )
        return diagnostics
