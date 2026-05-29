from __future__ import annotations

from sfu_converter.domain.ast_nodes import (
    AppendixNode,
    BibliographyEntryNode,
    Document,
    FigureNode,
    FormulaNode,
    HeadingLevel,
    HeadingNode,
    ListItemNode,
    ListNode,
    ListType,
    MetadataNode,
    PageBreakNode,
    ParagraphNode,
    RawBlockNode,
    ReferenceNode,
    SourceSpan,
    TableNode,
)
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.parser.attributes import parse_attributes
from sfu_converter.parser.base import BaseParser, ParserResult
from sfu_converter.parser.v1_parser import (
    _EXPLICIT_LIST_ITEM_RE,
    _LIST_TYPE_ALIASES,
    V1Parser,
    _parse_inline_formatting,
    _parse_table_row,
    _span_for_line,
    _structural_section_from_title,
)

_KNOWN_V2_MARKERS = (
    "[APPENDIX",
    "[DOC",
    "[FIGURE",
    "[FORMULA",
    "[FORMULA_END]",
    "[H",
    "[LIST",
    "[LIST_END]",
    "[META",
    "[P]",
    "[PAGE_BREAK]",
    "[RAW]",
    "[RAW_END]",
    "[REF",
    "[SOURCE",
    "[TABLE",
    "[TABLE_END]",
)


class V2Parser(BaseParser):
    """Parser for explicit, line-oriented version 2 TXT syntax."""

    def __init__(self, *, strict: bool = False):
        self.strict = strict
        self._v1_compat = V1Parser()

    def parse(self, source: str, filename: str | None = None) -> ParserResult:
        lines = source.splitlines()
        blocks = []
        diagnostics: list[Diagnostic] = []
        metadata: dict[str, str] = {}
        seen_ids: dict[str, SourceSpan] = {}
        i = 0

        while i < len(lines):
            stripped = lines[i].strip()
            span = _span_for_line(lines[i], i, filename)

            if not stripped:
                i += 1
                continue

            if stripped.startswith("["):
                self._v1_compat._check_cyrillic(stripped, span, diagnostics)

            if stripped.startswith("[DOC"):
                self._parse_doc(stripped, span, metadata, diagnostics)
            elif stripped.startswith("[META"):
                metadata_node = self._parse_metadata(stripped, span, diagnostics)
                if metadata_node is not None:
                    metadata[metadata_node.key] = metadata_node.value
                    blocks.append(metadata_node)
            elif stripped.startswith("[H "):
                heading = self._parse_heading(stripped, span, diagnostics)
                if heading is not None:
                    structural = _structural_section_from_title(heading.text, span)
                    blocks.append(structural if structural is not None else heading)
            elif stripped.startswith("[P]"):
                text = stripped.removeprefix("[P]").strip()
                blocks.append(
                    ParagraphNode(
                        runs=_parse_inline_formatting(text),
                        source=span,
                    )
                )
            elif stripped.startswith("[FIGURE"):
                figure = self._parse_figure(stripped, span)
                self._remember_id(figure.id, span, seen_ids, diagnostics)
                blocks.append(figure)
            elif stripped.startswith("[TABLE"):
                table, table_diagnostics, end_index = self._parse_table(
                    lines,
                    i,
                    filename,
                )
                diagnostics.extend(table_diagnostics)
                if table is not None:
                    self._remember_id(table.id, span, seen_ids, diagnostics)
                    blocks.append(table)
                i = end_index
            elif stripped.startswith("[LIST"):
                list_node, list_diagnostics, end_index = self._parse_list(
                    lines,
                    i,
                    filename,
                )
                diagnostics.extend(list_diagnostics)
                if list_node is not None:
                    blocks.append(list_node)
                i = end_index
            elif stripped.startswith("[FORMULA"):
                formula, formula_diagnostics, end_index = self._parse_formula(
                    lines,
                    i,
                    filename,
                )
                diagnostics.extend(formula_diagnostics)
                self._remember_id(formula.id, span, seen_ids, diagnostics)
                blocks.append(formula)
                i = end_index
            elif stripped.startswith("[REF"):
                reference = self._parse_reference(stripped, span, diagnostics)
                if reference is not None:
                    blocks.append(reference)
            elif stripped.startswith("[SOURCE"):
                source_node = self._parse_source(stripped, span, diagnostics)
                if source_node is not None:
                    blocks.append(source_node)
            elif stripped == "[PAGE_BREAK]":
                blocks.append(PageBreakNode(source=span))
            elif stripped.startswith("[APPENDIX"):
                appendix = self._parse_appendix(stripped, span)
                self._remember_id(appendix.id, span, seen_ids, diagnostics)
                blocks.append(appendix)
            elif stripped == "[RAW]":
                raw, raw_diagnostics, end_index = self._parse_raw(lines, i, filename)
                diagnostics.extend(raw_diagnostics)
                blocks.append(raw)
                i = end_index
            elif stripped.startswith("[") and not stripped.startswith(_KNOWN_V2_MARKERS):
                diagnostics.append(self._unknown_marker(stripped, span))
            elif not stripped.startswith("["):
                diagnostics.append(
                    Diagnostic(
                        code=DiagnosticCodes.TXT_UNKNOWN_MARKER,
                        message=f"Plain text must be wrapped in [P]: {stripped}",
                        severity=Severity.ERROR if self.strict else Severity.WARNING,
                        source=span,
                    )
                )

            i += 1

        document = Document(
            blocks=tuple(blocks),
            syntax_version=2,
            metadata=metadata,
            source_file=filename,
        )
        return ParserResult(document=document, diagnostics=diagnostics)

    def _parse_attributes(self, text: str) -> dict[str, str]:
        return parse_attributes(text)

    def _parse_doc(
        self,
        stripped: str,
        span: SourceSpan,
        metadata: dict[str, str],
        diagnostics: list[Diagnostic],
    ) -> None:
        attrs = self._parse_attributes(stripped)
        syntax = attrs.get("syntax")
        if syntax is not None and syntax != "2":
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_UNSUPPORTED_SYNTAX,
                    message=f"Unsupported V2 DOC syntax version: {syntax}",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
        for key, value in attrs.items():
            if key != "syntax":
                metadata[key] = value

    def _parse_metadata(
        self,
        stripped: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> MetadataNode | None:
        attrs = self._parse_attributes(stripped)
        key = attrs.get("key", "").strip()
        if not key:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message="META marker missing required 'key' attribute",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None
        return MetadataNode(key=key, value=attrs.get("value", ""), source=span)

    def _parse_heading(
        self,
        stripped: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> HeadingNode | None:
        attrs = self._parse_attributes(stripped)
        raw_level = attrs.get("level", "1")
        try:
            level_value = int(raw_level)
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message=f"Invalid heading level: {raw_level}",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None
        try:
            level = HeadingLevel(level_value)
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.INVALID_HEADING_LEVEL,
                    message=f"Heading level {level_value} is not allowed (max H4)",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None
        return HeadingNode(
            level=level,
            text=attrs.get("title", ""),
            number=attrs.get("number"),
            source=span,
        )

    def _parse_figure(self, stripped: str, span: SourceSpan) -> FigureNode:
        attrs = self._parse_attributes(stripped)
        return FigureNode(
            src=attrs.get("src"),
            caption=attrs.get("caption"),
            id=attrs.get("id"),
            source=span,
        )

    def _parse_table(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[TableNode | None, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        attrs = self._parse_attributes(lines[start_index].strip())
        rows = []
        expected_cell_count: int | None = None
        table_start_span = _span_for_line(lines[start_index], start_index, filename)
        i = start_index + 1
        found_end = False

        while i < len(lines):
            stripped = lines[i].strip()
            span = _span_for_line(lines[i], i, filename)
            if stripped.startswith("["):
                self._v1_compat._check_cyrillic(stripped, span, diagnostics)
            if stripped.startswith("[TABLE_END]"):
                found_end = True
                break
            if stripped.startswith("|"):
                row = _parse_table_row(stripped)
                cell_count = len(row.cells)
                if expected_cell_count is None:
                    expected_cell_count = cell_count
                elif cell_count != expected_cell_count:
                    diagnostics.append(
                        Diagnostic(
                            code=DiagnosticCodes.TXT_INVALID_TABLE_SHAPE,
                            message=(f"Table row has {cell_count} cells, expected {expected_cell_count}"),
                            severity=Severity.ERROR,
                            source=span,
                        )
                    )
                rows.append(row)
            elif stripped:
                diagnostics.append(self._unknown_marker(stripped, span))
            i += 1

        if not found_end:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                    message="TABLE without matching TABLE_END",
                    severity=Severity.ERROR,
                    source=table_start_span,
                )
            )

        if not rows:
            return None, diagnostics, i

        header_row_count = 0 if attrs.get("header", "true").lower() == "false" else 1
        return (
            TableNode(
                rows=tuple(rows),
                caption=attrs.get("caption"),
                id=attrs.get("id"),
                header_row_count=header_row_count,
                source=SourceSpan(
                    line_start=table_start_span.line_start,
                    line_end=i + 1 if found_end else len(lines),
                    filename=filename,
                ),
            ),
            diagnostics,
            i,
        )

    def _parse_list(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[ListNode | None, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        attrs = self._parse_attributes(lines[start_index].strip())
        list_start_span = _span_for_line(lines[start_index], start_index, filename)
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

        return (
            ListNode(
                list_type=list_type or ListType.BULLET,
                items=tuple(items),
                source=SourceSpan(
                    line_start=list_start_span.line_start,
                    line_end=i + 1 if found_end else len(lines),
                    filename=filename,
                ),
            ),
            diagnostics,
            i,
        )

    def _parse_formula(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[FormulaNode | None, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        attrs = self._parse_attributes(lines[start_index].strip())
        start_span = _span_for_line(lines[start_index], start_index, filename)
        formula_lines: list[str] = []
        i = start_index + 1
        found_end = False

        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith("[FORMULA_END]"):
                found_end = True
                break
            formula_lines.append(lines[i])
            i += 1

        if not found_end:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                    message="FORMULA without matching FORMULA_END",
                    severity=Severity.ERROR,
                    source=start_span,
                )
            )

        explanation = None
        end_index = i
        next_index = i + 1
        if next_index < len(lines):
            next_line = lines[next_index].strip()
            if next_line.startswith("[FORMULA_EXPLANATION]"):
                explanation = next_line.replace("[FORMULA_EXPLANATION]", "", 1).strip()
                end_index = next_index

        return (
            FormulaNode(
                content="\n".join(formula_lines).strip("\n"),
                id=attrs.get("id"),
                number=attrs.get("number"),
                explanation=explanation,
                source=SourceSpan(
                    line_start=start_span.line_start,
                    line_end=end_index + 1 if found_end else len(lines),
                    filename=filename,
                ),
            ),
            diagnostics,
            end_index,
        )

    def _parse_reference(
        self,
        stripped: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> ReferenceNode | None:
        attrs = self._parse_attributes(stripped)
        target = attrs.get("target", "").strip()
        if not target:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message="REF marker missing required 'target' attribute",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None
        return ReferenceNode(target=target, source=span)

    def _parse_source(
        self,
        stripped: str,
        span: SourceSpan,
        diagnostics: list[Diagnostic],
    ) -> BibliographyEntryNode | None:
        marker, _, text = stripped.partition("]")
        attrs = self._parse_attributes(f"{marker}]")
        try:
            number = int(attrs.get("number", ""))
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                    message=f"Invalid SOURCE number: {attrs.get('number', '<missing>')}",
                    severity=Severity.ERROR,
                    source=span,
                )
            )
            return None
        return BibliographyEntryNode(number=number, text=text.strip(), source=span)

    def _parse_appendix(self, stripped: str, span: SourceSpan) -> AppendixNode:
        attrs = self._parse_attributes(stripped)
        return AppendixNode(
            title=attrs.get("title", "ПРИЛОЖЕНИЕ"),
            id=attrs.get("id"),
            source=span,
        )

    def _parse_raw(
        self,
        lines: list[str],
        start_index: int,
        filename: str | None,
    ) -> tuple[RawBlockNode, list[Diagnostic], int]:
        diagnostics: list[Diagnostic] = []
        raw_lines: list[str] = []
        start_span = _span_for_line(lines[start_index], start_index, filename)
        i = start_index + 1
        found_end = False
        while i < len(lines):
            if lines[i].strip() == "[RAW_END]":
                found_end = True
                break
            raw_lines.append(lines[i])
            i += 1
        if not found_end:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                    message="RAW without matching RAW_END",
                    severity=Severity.ERROR,
                    source=start_span,
                )
            )
        return (
            RawBlockNode(
                text="\n".join(raw_lines),
                source=SourceSpan(
                    line_start=start_span.line_start,
                    line_end=i + 1 if found_end else len(lines),
                    filename=filename,
                ),
            ),
            diagnostics,
            i,
        )

    def _remember_id(
        self,
        identifier: str | None,
        span: SourceSpan,
        seen_ids: dict[str, SourceSpan],
        diagnostics: list[Diagnostic],
    ) -> None:
        if not identifier:
            return
        if identifier in seen_ids:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCodes.TXT_DUPLICATE_ID,
                    message=f"Duplicate id: {identifier}",
                    severity=Severity.ERROR,
                    source=span,
                    suggestion="Use a unique id for every referenceable block",
                )
            )
            return
        seen_ids[identifier] = span

    def _unknown_marker(self, stripped: str, span: SourceSpan) -> Diagnostic:
        return Diagnostic(
            code=DiagnosticCodes.TXT_UNKNOWN_MARKER,
            message=f"Unknown marker: {stripped}",
            severity=Severity.ERROR if self.strict else Severity.WARNING,
            source=span,
        )
