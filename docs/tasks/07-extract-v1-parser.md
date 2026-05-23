# Task 07: Extract V1 Compatibility Parser

## Priority: High
## Phase: Phase 2 (Domain AST and compatibility parser)
## Affected files: NEW `src/sfu_converter/parser/`, MODIFY `src/sfu_converter/converter.py`
## References: `docs/technical requirements/04_txt_syntax.md`

## Summary

Extract the parsing logic from `converter.py:_render_lines()` into a standalone parser module that produces the domain AST. The parser must handle all v1 syntax (H1, H2, H3, IMAGE, TABLE_START/END, TABLE_CAPTION, plain text) and emit structured `Diagnostic` objects for any issues.

## Current State

`converter.py:_render_lines()` (starts ~line 224) iterates over lines and directly creates `python-docx` paragraphs. It contains:
- `line.startswith('[H1]')` → creates heading paragraph
- `line.startswith('[H2]')` → creates heading paragraph  
- `line.startswith('[H3]')` → creates heading paragraph
- `line.startswith('[IMAGE=')` → extracts path, looks ahead for caption
- `line.startswith('[TABLE_START]')` → enters table accumulation mode
- `line.startswith('[TABLE_CAPTION]')` → captures table caption
- `line.startswith('[TABLE_END]')` → creates table
- Pipe-delimited rows → accumulates table data
- Default → creates normal paragraph

All of this must be extracted into a pure function that returns `Document` AST + `list[Diagnostic]`.

## Detailed Implementation

### 1. Create parser directory

```
src/sfu_converter/parser/
├── __init__.py
├── v1_parser.py      # V1 syntax parser
└── base.py           # Abstract parser interface
```

### 2. `src/sfu_converter/parser/base.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from ..domain.ast_nodes import Document
from ..domain.diagnostics import Diagnostic


class ParserResult:
    def __init__(self, document: Document, diagnostics: list[Diagnostic]):
        self.document = document
        self.diagnostics = diagnostics

    @property
    def has_errors(self) -> bool:
        from ..domain.diagnostics import Severity
        return any(d.severity in (Severity.ERROR, Severity.FATAL) for d in self.diagnostics)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, source: str, filename: str | None = None) -> ParserResult:
        """Parse TXT source into a Document AST."""
        ...
```

### 3. `src/sfu_converter/parser/v1_parser.py`

Extract and refactor the parsing logic from `converter.py:_render_lines()`:

```python
import re
from ..domain.ast_nodes import (
    Document, ParagraphNode, HeadingNode, HeadingLevel,
    TableNode, TableRow, TableCell, FigureNode,
    TextRun, SourceSpan,
)
from ..domain.diagnostics import Diagnostic, Severity, DiagnosticCodes
from .base import BaseParser, ParserResult


# Cyrillic lookalike detection
_CYRILLIC_LATIN_MAP = {
    'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
    'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T',
    'Х': 'X',
}
_CYRILLIC_RE = re.compile('[' + ''.join(_CYRILLIC_LATIN_MAP.keys()) + ']')


class V1Parser(BaseParser):
    """Parser for README v1 TXT syntax."""

    def parse(self, source: str, filename: str | None = None) -> ParserResult:
        lines = source.splitlines()
        blocks = []
        diagnostics = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            span = SourceSpan(line_start=i + 1, line_end=i + 1, filename=filename)

            # Check for Cyrillic in markers
            if stripped.startswith('['):
                self._check_cyrillic(stripped, span, diagnostics)

            if stripped.startswith('[H1]'):
                text = stripped.replace('[H1]', '').strip()
                blocks.append(HeadingNode(level=HeadingLevel.H1, text=text, source=span))

            elif stripped.startswith('[H2]'):
                text = stripped.replace('[H2]', '').strip()
                blocks.append(HeadingNode(level=HeadingLevel.H2, text=text, source=span))

            elif stripped.startswith('[H3]'):
                text = stripped.replace('[H3]', '').strip()
                blocks.append(HeadingNode(level=HeadingLevel.H3, text=text, source=span))

            elif stripped.startswith('[IMAGE='):
                # Extract image path
                match = re.match(r'\[IMAGE=(.+?)\]', stripped)
                if match:
                    src = match.group(1)
                    # Look ahead for caption
                    caption = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('Рисунок') or next_line.startswith('Figure'):
                            caption = next_line
                            i += 1
                    blocks.append(FigureNode(src=src, caption=caption, source=span))
                else:
                    diagnostics.append(Diagnostic(
                        code=DiagnosticCodes.TXT_MALFORMED_ATTRIBUTE,
                        message=f"Malformed IMAGE tag: {stripped}",
                        severity=Severity.ERROR,
                        source=span,
                    ))

            elif stripped.startswith('[TABLE_START]'):
                # Accumulate table rows
                table_rows = []
                table_caption = None
                i += 1
                table_start_span = span
                while i < len(lines):
                    tline = lines[i].strip()
                    if tline.startswith('[TABLE_END]'):
                        break
                    elif tline.startswith('[TABLE_CAPTION]'):
                        table_caption = tline.replace('[TABLE_CAPTION]', '').strip()
                    elif tline.startswith('|'):
                        cells = [c.strip() for c in tline.strip('|').split('|')]
                        table_rows.append(TableRow(cells=tuple(TableCell(text=c) for c in cells)))
                    i += 1
                else:
                    diagnostics.append(Diagnostic(
                        code=DiagnosticCodes.TXT_MISSING_BLOCK_END,
                        message="TABLE_START without matching TABLE_END",
                        severity=Severity.ERROR,
                        source=table_start_span,
                    ))
                
                if table_rows:
                    end_span = SourceSpan(line_start=table_start_span.line_start, line_end=i + 1, filename=filename)
                    blocks.append(TableNode(
                        rows=tuple(table_rows),
                        caption=table_caption,
                        source=end_span,
                    ))

            elif stripped and not stripped.startswith('['):
                # Normal paragraph
                blocks.append(ParagraphNode(
                    runs=(TextRun(text=stripped),),
                    source=span,
                ))

            elif stripped.startswith('[') and not any(
                stripped.startswith(k) for k in ['[H1]', '[H2]', '[H3]', '[IMAGE=', '[TABLE_START]', '[TABLE_END]', '[TABLE_CAPTION]']
            ):
                diagnostics.append(Diagnostic(
                    code=DiagnosticCodes.TXT_UNKNOWN_MARKER,
                    message=f"Unknown marker: {stripped}",
                    severity=Severity.WARNING,
                    source=span,
                ))

            i += 1

        document = Document(
            blocks=tuple(blocks),
            syntax_version=1,
            source_file=filename,
        )
        return ParserResult(document=document, diagnostics=diagnostics)

    def _check_cyrillic(self, text: str, span: SourceSpan, diagnostics: list[Diagnostic]):
        """Check for Cyrillic lookalike characters in marker names."""
        bracket_end = text.find(']')
        if bracket_end == -1:
            return
        marker_text = text[1:bracket_end]
        if _CYRILLIC_RE.search(marker_text):
            diagnostics.append(Diagnostic(
                code=DiagnosticCodes.TXT_CYRILLIC_IN_MARKER,
                message=f"Cyrillic characters detected in marker: [{marker_text}]",
                severity=Severity.ERROR,
                source=span,
                suggestion="Replace Cyrillic lookalike characters with Latin equivalents",
            ))
```

### 4. Update `converter.py`

Modify `_render_lines` to accept either raw lines or a pre-parsed `Document` AST. During migration, keep both paths working:

```python
def _render_from_ast(self, document: Document):
    """Render a Document AST to the current DOCX document."""
    for block in document.blocks:
        if isinstance(block, HeadingNode):
            self._render_heading(block)
        elif isinstance(block, ParagraphNode):
            self._render_paragraph(block)
        elif isinstance(block, TableNode):
            self._render_table(block)
        elif isinstance(block, FigureNode):
            self._render_figure(block)
        # ... etc
```

## Tests to write

Create `tests/test_v1_parser.py`:
- Parse each marker type: H1, H2, H3, IMAGE, TABLE, plain text
- Parse complete document with mixed block types
- Test Cyrillic detection in markers
- Test unknown marker warning
- Test TABLE_START without TABLE_END produces error diagnostic
- Test IMAGE without caption
- Test IMAGE with caption lookahead
- Test empty input
- Test malformed IMAGE tag
- Golden AST tests using `tests/test_input.txt` and example files

## Verification

1. `python -m pytest tests/test_v1_parser.py` passes
2. Parser produces identical logical output as `_render_lines()` for all example files
3. No `python-docx` imports in parser module
4. Diagnostics include line numbers
