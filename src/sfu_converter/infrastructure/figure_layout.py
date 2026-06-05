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
from sfu_converter.domain.reference_graph import ReferenceGraph, ReferenceTargetKind, build_reference_graph


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


def figure_reference_diagnostics(
    document: Document,
    graph: ReferenceGraph | None = None,
) -> list[Diagnostic]:
    graph = graph or build_reference_graph(document)
    diagnostics: list[Diagnostic] = []
    figure_blocks = _figure_blocks_by_canonical(document, graph)
    for definition in graph.definitions:
        if definition.kind is not ReferenceTargetKind.FIGURE:
            continue
        reference_position = graph.first_reference_position(ReferenceTargetKind.FIGURE, definition.canonical)
        block = figure_blocks.get(definition.canonical)
        if reference_position is None:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.FIGURE_NEVER_REFERENCED,
                    message=f"Figure '{definition.canonical}' is never referenced",
                    severity=Severity.WARNING,
                    rule_id="common.reference.figure_table_formula",
                    source=definition.source,
                    target=definition.canonical,
                )
            )
            continue

        if reference_position - definition.position > 3:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.FIGURE_PLACEMENT_NEXT_PAGE,
                    message=(
                        f"Figure '{definition.canonical}' appears more than three paragraphs "
                        "before its first reference"
                    ),
                    severity=Severity.INFO,
                    rule_id="common.figure.placement_after_reference",
                    source=block.source if block is not None else definition.source,
                    target=definition.canonical,
                )
            )
    return diagnostics


def _figure_blocks_by_canonical(document: Document, graph: ReferenceGraph) -> dict[str, FigureNode]:
    figures = [block for block in _walk_reference_blocks(document.blocks) if isinstance(block, FigureNode)]
    by_canonical: dict[str, FigureNode] = {}
    for definition in graph.definitions:
        if definition.kind is not ReferenceTargetKind.FIGURE:
            continue
        match = next((block for block in figures if block.source == definition.source), None)
        if match is not None:
            by_canonical[definition.canonical] = match
    return by_canonical


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
