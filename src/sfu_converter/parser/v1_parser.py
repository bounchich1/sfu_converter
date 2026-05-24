from __future__ import annotations

import re

from sfu_converter.domain.ast_nodes import (
    Document,
    FigureNode,
    HeadingLevel,
    HeadingNode,
    ListItemNode,
    ListNode,
    ListType,
    ParagraphNode,
    SourceSpan,
    StructuralSectionNode,
    StructuralSectionType,
    TableCaptionNode,
    TableCell,
    TableNode,
    TableRow,
    TextRun,
)
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.parser.base import BaseParser, ParserResult

_IMAGE_RE = re.compile(r"\[IMAGE(?:=([^\]]+))?\]")
_ATTR_RE = re.compile(r'(\w+)=(?:"([^"]*)"|([^\s\]]+))')
_INLINE_FORMATTING_RE = re.compile(
    r"\*\*\*(\S(?:.*?\S)?)\*\*\*"
    r"|\*\*(\S(?:.*?\S)?)\*\*"
    r"|\*(\S(?:[^*]*?\S)?)\*"
)
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
    "[LIST",
    "[LIST_END]",
    "[SECTION",
    "[STRUCTURAL",
    "[TABLE_START]",
    "[TABLE_END]",
    "[TABLE_CAPTION]",
)
_STRUCTURAL_SECTIONS_BY_TITLE = {
    section_type.value: section_type for section_type in StructuralSectionType
}
_STRUCTURAL_TYPE_ALIASES = {
    "abstract": StructuralSectionType.ABSTRACT,
    "referat": StructuralSectionType.ABSTRACT,
    "annotation": StructuralSectionType.ANNOTATION,
    "contents": StructuralSectionType.CONTENTS,
    "content": StructuralSectionType.CONTENTS,
    "introduction": StructuralSectionType.INTRODUCTION,
    "intro": StructuralSectionType.INTRODUCTION,
    "conclusion": StructuralSectionType.CONCLUSION,
    "abbreviations": StructuralSectionType.ABBREVIATIONS,
    "sources": StructuralSectionType.SOURCES,
    "bibliography": StructuralSectionType.SOURCES,
    "appendix": StructuralSectionType.APPENDIX,
}
_LIST_TYPE_ALIASES = {
    "bullet": ListType.BULLET,
    "letter": ListType.LETTERED,
    "lettered": ListType.LETTERED,
    "number": ListType.NUMBERED,
    "numbered": ListType.NUMBERED,
}
_EXPLICIT_LIST_ITEM_RE = re.compile(r"^\[(?:-|[^\]]+\))\]\s*(.*)$")


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
                title = stripped.replace("[H1]", "", 1).strip()
                structural = _structural_section_from_title(title, span)
                if structural is not None:
                    blocks.append(structural)
                else:
                    blocks.append(
                        HeadingNode(
                            level=HeadingLevel.H1,
                            text=title,
                            number="auto",
                            source=span,
                        )
                    )
            elif stripped.startswith("[H2]"):
                blocks.append(
                    HeadingNode(
                        level=HeadingLevel.H2,
                        text=stripped.replace("[H2]", "", 1).strip(),
                        number="auto",
                        source=span,
                    )
                )
            elif stripped.startswith("[H3]"):
                blocks.append(
                    HeadingNode(
                        level=HeadingLevel.H3,
                        text=stripped.replace("[H3]", "", 1).strip(),
                        number="auto",
                        source=span,
                    )
                )
            elif _is_list_start(stripped):
                list_node, list_diagnostics, end_index = self._parse_explicit_list(
                    lines,
                    i,
                    filename,
                )
                diagnostics.extend(list_diagnostics)
                if list_node is not None:
                    blocks.append(list_node)
                i = end_index
            elif stripped.startswith("[IMAGE"):
                figure = self._parse_image(stripped, span, diagnostics)
                if figure is not None:
                    caption, consumed = _caption_after_image(lines, i)
                    if caption is not None:
                        figure = FigureNode(src=figure.src, caption=caption, source=span)
                        i += consumed
                    blocks.append(figure)
            elif stripped.startswith("[SECTION"):
                structural = _parse_section_marker(stripped, span, diagnostics)
                if structural is not None:
                    blocks.append(structural)
            elif stripped.startswith("[STRUCTURAL"):
                structural = _parse_structural_marker(stripped, span, diagnostics)
                if structural is not None:
                    blocks.append(structural)
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
                if stripped.startswith("- "):
                    list_node, end_index = _parse_dash_list(lines, i, filename)
                    blocks.append(list_node)
                    i = end_index
                else:
                    blocks.append(
                        ParagraphNode(
                            runs=_parse_inline_formatting(stripped),
                            source=span,
                        )
                    )

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

    def _parse_explicit_list(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[ListNode | None, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        list_start_span = _span_for_line(lines[start_index], start_index, filename)
        attrs = _parse_attributes(lines[start_index].strip())
        list_type_name = attrs.get("type", "bullet").strip().lower()
        list_type = _LIST_TYPE_ALIASES.get(list_type_name)

        if list_type is None:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message=f"Unknown list type: {list_type_name or '<empty>'}",
                    severity=Severity.ERROR,
                    source=list_start_span,
                )
            )
            return None, diagnostics, start_index

        items: list[ListItemNode] = []
        i = start_index + 1
        found_end = False

        while i < len(lines):
            stripped = lines[i].strip()
            span = _span_for_line(lines[i], i, filename)

            if stripped.startswith("["):
                self._check_cyrillic(stripped, span, diagnostics)

            if stripped.startswith("[LIST_END]"):
                found_end = True
                break

            match = _EXPLICIT_LIST_ITEM_RE.fullmatch(stripped)
            if match is not None:
                items.append(ListItemNode(text=match.group(1).strip(), source=span))
            elif stripped:
                diagnostics.append(
                    Diagnostic(
                        code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                        message=f"Malformed list item: {stripped}",
                        severity=Severity.ERROR,
                        source=span,
                    )
                )
            i += 1

        if not found_end:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                    message="LIST without matching LIST_END",
                    severity=Severity.ERROR,
                    source=list_start_span,
                )
            )

        line_end = i + 1 if found_end else len(lines)
        return (
            ListNode(
                list_type=list_type,
                items=tuple(items),
                source=SourceSpan(
                    line_start=list_start_span.line_start,
                    line_end=line_end,
                    filename=filename,
                ),
            ),
            diagnostics,
            i,
        )

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
        marker_text = re.split(r"[\s=]", marker_text, maxsplit=1)[0]

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


def _parse_dash_list(
    lines: list[str],
    start_index: int,
    filename: str | None,
) -> tuple[ListNode, int]:
    items: list[ListItemNode] = []
    i = start_index

    while i < len(lines) and lines[i].strip().startswith("- "):
        stripped = lines[i].strip()
        items.append(
            ListItemNode(
                text=stripped[2:].strip(),
                source=_span_for_line(lines[i], i, filename),
            )
        )
        i += 1

    return (
        ListNode(
            list_type=ListType.BULLET,
            items=tuple(items),
            source=SourceSpan(
                line_start=start_index + 1,
                line_end=i,
                filename=filename,
            ),
        ),
        i - 1,
    )


def _is_list_start(stripped: str) -> bool:
    return stripped == "[LIST]" or stripped.startswith("[LIST ")


def _parse_attributes(text: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2) if match.group(2) is not None else match.group(3)
        for match in _ATTR_RE.finditer(text)
    }


def _parse_section_marker(
    stripped: str,
    span: SourceSpan,
    diagnostics: list[Diagnostic],
) -> StructuralSectionNode | None:
    attrs = _parse_attributes(stripped)
    section_type_name = attrs.get("type", "").strip().lower()
    section_type = _STRUCTURAL_TYPE_ALIASES.get(section_type_name)
    if section_type is None:
        diagnostics.append(
            Diagnostic(
                code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                message=(
                    "Unknown structural section type: "
                    f"{section_type_name or '<empty>'}"
                ),
                severity=Severity.ERROR,
                source=span,
            )
        )
        return None
    return StructuralSectionNode(
        section_type=section_type,
        title=section_type.value,
        source=span,
    )


def _parse_structural_marker(
    stripped: str,
    span: SourceSpan,
    diagnostics: list[Diagnostic],
) -> StructuralSectionNode | None:
    attrs = _parse_attributes(stripped)
    title = attrs.get("title", "").strip()
    structural = _structural_section_from_title(title, span)
    if structural is None:
        diagnostics.append(
            Diagnostic(
                code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                message=f"Unknown structural section title: {title or '<empty>'}",
                severity=Severity.ERROR,
                source=span,
            )
        )
    return structural


def _structural_section_from_title(
    title: str,
    span: SourceSpan,
) -> StructuralSectionNode | None:
    normalized = _normalize_structural_title(title)
    section_type = _STRUCTURAL_SECTIONS_BY_TITLE.get(normalized)
    if section_type is None:
        return None
    return StructuralSectionNode(
        section_type=section_type,
        title=title.strip(),
        source=span,
    )


def _normalize_structural_title(title: str) -> str:
    return " ".join(title.strip().upper().split())


def _caption_after_image(lines: list[str], image_index: int) -> tuple[str | None, int]:
    if image_index + 1 >= len(lines):
        return None, 0
    next_line = lines[image_index + 1].strip()
    if next_line.startswith("Рисунок") or next_line.startswith("Figure"):
        return next_line, 1
    return None, 0


def _parse_inline_formatting(text: str) -> tuple[TextRun, ...]:
    """Split text into TextRuns by ``***bi***``, ``**bold**``, ``*italic*``."""

    runs: list[TextRun] = []
    cursor = 0
    for match in _INLINE_FORMATTING_RE.finditer(text):
        start, end = match.span()
        if start > cursor:
            runs.append(TextRun(text=text[cursor:start]))
        bi, bold, italic = match.group(1), match.group(2), match.group(3)
        if bi is not None:
            runs.append(TextRun(text=bi, bold=True, italic=True))
        elif bold is not None:
            runs.append(TextRun(text=bold, bold=True))
        else:
            runs.append(TextRun(text=italic, italic=True))
        cursor = end
    if cursor < len(text):
        runs.append(TextRun(text=text[cursor:]))
    if not runs:
        return (TextRun(text=text),)
    return tuple(runs)
