from __future__ import annotations

import re
from collections.abc import Iterable

from sfu_converter.domain.ast_nodes import (
    AppendixNode,
    Document,
    FigureNode,
    HeadingNode,
    ParagraphNode,
    RawBlockNode,
    ReferenceNode,
    StructuralSectionNode,
    TableCaptionNode,
)
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity


def figure_caption_text(block: FigureNode, number: str) -> str | None:
    if block.sheet is not None and block.sheet >= 2:
        return f"Рисунок {number}, лист {block.sheet}"

    caption = (block.caption or "").strip()
    if not caption:
        return None
    if caption.startswith("Рисунок"):
        return normalize_caption_dashes(caption)
    return f"Рисунок {number} — {caption}"


def normalize_caption_dashes(text: str) -> str:
    return re.sub(r"\s[-–]\s", " — ", text)


def figure_reference_diagnostics(document: Document) -> list[Diagnostic]:
    figures: dict[str, tuple[int, FigureNode]] = {}
    references: dict[str, int] = {}
    for position, block in enumerate(_walk_reference_blocks(document.blocks), start=1):
        if isinstance(block, FigureNode) and block.id:
            figures.setdefault(block.id, (position, block))
        elif isinstance(block, ReferenceNode):
            references.setdefault(block.target, position)

    diagnostics: list[Diagnostic] = []
    for figure_id, (figure_position, block) in figures.items():
        reference_position = references.get(figure_id)
        if reference_position is None:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.FIGURE_NEVER_REFERENCED,
                    message=f"Figure '{figure_id}' is never referenced",
                    severity=Severity.WARNING,
                    rule_id="common.reference.figure_table_formula",
                    source=block.source,
                    target=figure_id,
                )
            )
            continue

        if reference_position - figure_position > 3:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.FIGURE_PLACEMENT_NEXT_PAGE,
                    message=(
                        f"Figure '{figure_id}' appears more than three paragraphs "
                        "before its first reference"
                    ),
                    severity=Severity.INFO,
                    rule_id="common.figure.placement_after_reference",
                    source=block.source,
                    target=figure_id,
                )
            )
    return diagnostics


def _walk_reference_blocks(blocks: Iterable) -> Iterable:
    for block in blocks:
        if isinstance(
            block,
            (
                FigureNode,
                HeadingNode,
                ParagraphNode,
                RawBlockNode,
                ReferenceNode,
                StructuralSectionNode,
                TableCaptionNode,
            ),
        ):
            yield block
        elif isinstance(block, AppendixNode):
            yield from _walk_reference_blocks(block.blocks)
        else:
            yield block
