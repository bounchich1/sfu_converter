from __future__ import annotations

from sfu_converter.application import composition
from sfu_converter.domain.diagnostics import Diagnostic
from sfu_converter.domain.formatting import FormattingProfile, unsupported_rule_diagnostics
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
        diagnostics.extend(unsupported_rule_diagnostics(profile, component="renderer"))
        diagnostics.extend(composition.validate(result.document, profile))
        render_diagnostics = self._renderer.render_to_file(
            result.document,
            profile,
            output_path,
            template_path,
            template_mode,
        )
        diagnostics.extend(_without_existing_support_diagnostics(diagnostics, render_diagnostics))
        return diagnostics


def _without_existing_support_diagnostics(
    existing: list[Diagnostic],
    candidates: list[Diagnostic],
) -> list[Diagnostic]:
    seen = {
        (diagnostic.code, diagnostic.rule_id, diagnostic.message)
        for diagnostic in existing
    }
    return [
        diagnostic
        for diagnostic in candidates
        if (diagnostic.code, diagnostic.rule_id, diagnostic.message) not in seen
    ]
