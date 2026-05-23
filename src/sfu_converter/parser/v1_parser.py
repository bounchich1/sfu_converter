from __future__ import annotations

import re

from sfu_converter.domain.ast_nodes import (
    Document,
    FigureNode,
    HeadingLevel,
    HeadingNode,
    ParagraphNode,
    SourceSpan,
    TableCaptionNode,
    TableCell,
    TableNode,
    TableRow,
    TextRun,
)
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.parser.base import BaseParser, ParserResult

_IMAGE_RE = re.compile(r"\[IMAGE(?:=([^\]]+))?\]")
_CYRILLIC_LATIN_MAP = {
    "А": "A",
    "В": "B",
    "С": "C",
    "Е": "E",
    "Н": "H",
    "К": "K",
    "М": "M",
    "О": "O",
    "Р": "P",
    "Т": "T",
    "Х": "X",
}
_CYRILLIC_RE = re.compile("[" + "".join(_CYRILLIC_LATIN_MAP.keys()) + "]")
_KNOWN_MARKERS = (
    "[H1]",
    "[H2]",
    "[H3]",
    "[IMAGE",
    "[TABLE_START]",
    "[TABLE_END]",
    "[TABLE_CAPTION]",
)


class V1Parser(BaseParser):
    """Parser for v1 TXT syntax."""

    def parse(self, source: str, filename: str | None = None) -> ParserResult:
        lines = source.splitlines()
        blocks = []
        diagnostics: list[Diagnostic] = []
        i = 0

        while i < len(lines):
            stripped = lines[i].strip()
            span = _span_for_line(lines[i], i, filename)

            if not stripped:
                i += 1
                continue

            if stripped.startswith("["):
                self._check_cyrillic(stripped, span, diagnostics)

            if stripped.startswith("[H1]"):
                blocks.append(
                    HeadingNode(
                        level=HeadingLevel.H1,
                        text=stripped.replace("[H1]", "", 1).strip(),
                        source=span,
                    )
                )
            elif stripped.startswith("[H2]"):
                blocks.append(
                    HeadingNode(
                        level=HeadingLevel.H2,
                        text=stripped.replace("[H2]", "", 1).strip(),
                        source=span,
                    )
                )
            elif stripped.startswith("[H3]"):
                blocks.append(
                    HeadingNode(
                        level=HeadingLevel.H3,
                        text=stripped.replace("[H3]", "", 1).strip(),
                        source=span,
                    )
                )
            elif stripped.startswith("[IMAGE"):
                figure = self._parse_image(stripped, span, diagnostics)
                if figure is not None:
                    caption, consumed = _caption_after_image(lines, i)
                    if caption is not None:
                        figure = FigureNode(src=figure.src, caption=caption, source=span)
                        i += consumed
                    blocks.append(figure)
            elif stripped.startswith("[TABLE_START]"):
                table, table_diagnostics, end_index = self._parse_table(lines, i, filename)
                diagnostics.extend(table_diagnostics)
                if table is not None:
                    blocks.append(table)
                i = end_index
            elif stripped.startswith("[TABLE_CAPTION]"):
                blocks.append(
                    TableCaptionNode(
                        text=stripped.replace("[TABLE_CAPTION]", "", 1).strip(),
                        source=span,
                    )
                )
            elif stripped.startswith("[") and not stripped.startswith(_KNOWN_MARKERS):
                diagnostics.append(
                    Diagnostic(
                        code=DiagnosticCodes.TXT_UNKNOWN_MARKER,
                        message=f"Unknown marker: {stripped}",
                        severity=Severity.WARNING,
                        source=span,
                    )
                )
            elif not stripped.startswith("["):
                blocks.append(ParagraphNode(runs=(TextRun(text=stripped),), source=span))

            i += 1

        return ParserResult(
            document=Document(
                blocks=tuple(blocks),
                syntax_version=1,
                source_file=filename,
            ),
            diagnostics=diagnostics,
        )

    def _parse_image(
        self,
        stripped: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> FigureNode | None:
        match = _IMAGE_RE.fullmatch(stripped)
        if match is None:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message=f"Malformed IMAGE tag: {stripped}",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None

        image_path = match.group(1).strip() if match.group(1) else None
        return FigureNode(src=image_path, source=span)

    def _parse_table(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[TableNode | None, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        rows: list[TableRow] = []
        expected_cell_count: int | None = None
        caption = None
        table_start_span = _span_for_line(lines[start_index], start_index, filename)
        i = start_index + 1
        found_end = False

        while i < len(lines):
            stripped = lines[i].strip()
            span = _span_for_line(lines[i], i, filename)

            if stripped.startswith("["):
                self._check_cyrillic(stripped, span, diagnostics)

            if stripped.startswith("[TABLE_END]"):
                found_end = True
                break
            if stripped.startswith("[TABLE_CAPTION]"):
                caption = stripped.replace("[TABLE_CAPTION]", "", 1).strip()
            elif stripped.startswith("|"):
                row = _parse_table_row(stripped)
                if row is not None:
                    cell_count = len(row.cells)
                    if expected_cell_count is None:
                        expected_cell_count = cell_count
                    elif cell_count != expected_cell_count:
                        diagnostics.append(
                            Diagnostic(
                                code=DiagnosticCodes.TXT_INVALID_TABLE_SHAPE,
                                message=(
                                    "Table row has "
                                    f"{cell_count} cells, expected {expected_cell_count}"
                                ),
                                severity=Severity.ERROR,
                                source=span,
                            )
                        )
                    rows.append(row)
            elif stripped.startswith("[") and not stripped.startswith(_KNOWN_MARKERS):
                diagnostics.append(
                    Diagnostic(
                        code=DiagnosticCodes.TXT_UNKNOWN_MARKER,
                        message=f"Unknown marker inside table: {stripped}",
                        severity=Severity.WARNING,
                        source=span,
                    )
                )
            i += 1

        if not found_end:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                    message="TABLE_START without matching TABLE_END",
                    severity=Severity.ERROR,
                    source=table_start_span,
                )
            )

        line_end = i + 1 if found_end else len(lines)
        table = None
        if rows:
            table = TableNode(
                rows=tuple(rows),
                caption=caption,
                source=SourceSpan(
                    line_start=table_start_span.line_start,
                    line_end=line_end,
                    filename=filename,
                ),
            )
        return table, diagnostics, i

    def _check_cyrillic(
        self,
        text: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> None:
        bracket_end = text.find("]")
        if bracket_end == -1:
            marker_text = text[1:]
        else:
            marker_text = text[1:bracket_end]

        if _CYRILLIC_RE.search(marker_text):
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_CYRILLIC_IN_MARKER,
                    message=f"Cyrillic characters detected in marker: [{marker_text}]",
                    severity=Severity.ERROR,
                    source=span,
                    suggestion="Replace Cyrillic lookalike characters with Latin equivalents",
                )
            )


def _span_for_line(line: str, index: int, filename: str | None) -> SourceSpan:
    return SourceSpan(
        line_start=index + 1,
        line_end=index + 1,
        col_start=1 if line else 0,
        col_end=len(line),
        filename=filename,
    )


def _parse_table_row(stripped: str) -> TableRow | None:
    if not stripped.startswith("|"):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if not cells:
        return None
    return TableRow(cells=tuple(TableCell(text=cell) for cell in cells))


def _caption_after_image(lines: list[str], image_index: int) -> tuple[str | None, int]:
    if image_index + 1 >= len(lines):
        return None, 0
    next_line = lines[image_index + 1].strip()
    if next_line.startswith("Рисунок") or next_line.startswith("Figure"):
        return next_line, 1
    return None, 0
