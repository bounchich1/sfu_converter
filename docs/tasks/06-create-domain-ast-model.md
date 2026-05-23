# Task 06: Create Domain AST Model

## Priority: High
## Phase: Phase 2 (Domain AST and compatibility parser)
## Affected files: NEW `src/sfu_converter/domain/` directory
## References: `docs/technical requirements/02_clean_architecture.md`

## Summary

Create the domain layer with immutable data classes representing the document Abstract Syntax Tree (AST). This is the core data model that decouples parsing from rendering.

## Detailed Implementation

### 1. Create directory structure

```
src/sfu_converter/domain/
├── __init__.py
├── ast_nodes.py      # Document AST node types
├── diagnostics.py    # Diagnostic and severity types
├── formatting.py     # FormattingRule, FormattingProfile
└── values.py         # Value objects (Spacing, Margin, etc.)
```

### 2. `src/sfu_converter/domain/ast_nodes.py`

Use Python `dataclasses` with `frozen=True` for immutability:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class BlockType(Enum):
    DOCUMENT = auto()
    PARAGRAPH = auto()
    HEADING = auto()
    TABLE = auto()
    FIGURE = auto()
    FORMULA = auto()
    LIST = auto()
    LIST_ITEM = auto()
    PAGE_BREAK = auto()
    APPENDIX = auto()
    BIBLIOGRAPHY_ENTRY = auto()
    RAW_BLOCK = auto()
    TABLE_CAPTION = auto()
    FIGURE_CAPTION = auto()
    METADATA = auto()


class HeadingLevel(Enum):
    H1 = 1
    H2 = 2
    H3 = 3


class ListType(Enum):
    BULLET = auto()
    NUMBERED = auto()
    LETTERED = auto()


@dataclass(frozen=True)
class SourceSpan:
    """Location in the source TXT file."""
    line_start: int
    line_end: int
    col_start: int = 0
    col_end: int = 0
    filename: Optional[str] = None


@dataclass(frozen=True)
class TextRun:
    """A run of text with optional inline formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class ParagraphNode:
    """A normal text paragraph."""
    runs: tuple[TextRun, ...]
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class HeadingNode:
    """A heading (H1, H2, H3)."""
    level: HeadingLevel
    text: str
    number: Optional[str] = None  # e.g. "1", "1.1", "1.1.1"
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class TableCell:
    text: str


@dataclass(frozen=True)
class TableRow:
    cells: tuple[TableCell, ...]


@dataclass(frozen=True)
class TableNode:
    """A table block."""
    rows: tuple[TableRow, ...]
    caption: Optional[str] = None
    id: Optional[str] = None
    header_row_count: int = 1
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class FigureNode:
    """An image/figure block."""
    src: str  # relative path to image
    caption: Optional[str] = None
    id: Optional[str] = None
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class FormulaNode:
    """A formula block."""
    content: str
    id: Optional[str] = None
    number: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class ListItemNode:
    text: str
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class ListNode:
    list_type: ListType
    items: tuple[ListItemNode, ...]
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class PageBreakNode:
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class AppendixNode:
    title: str
    id: Optional[str] = None
    blocks: tuple = ()  # child blocks
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class BibliographyEntryNode:
    number: int
    text: str
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class RawBlockNode:
    """Literal/escaped text that should not be parsed."""
    text: str
    source: Optional[SourceSpan] = None


@dataclass(frozen=True)
class MetadataNode:
    key: str
    value: str
    source: Optional[SourceSpan] = None


# Union type for all block nodes
BlockNode = (
    ParagraphNode | HeadingNode | TableNode | FigureNode |
    FormulaNode | ListNode | PageBreakNode | AppendixNode |
    BibliographyEntryNode | RawBlockNode | MetadataNode
)


@dataclass(frozen=True)
class Document:
    """Root AST node representing a complete document."""
    blocks: tuple[BlockNode, ...]
    syntax_version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)
    source_file: Optional[str] = None
```

### 3. `src/sfu_converter/domain/diagnostics.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from .ast_nodes import SourceSpan


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True)
class Diagnostic:
    """A structured diagnostic message."""
    code: str                         # e.g. "TXT_UNKNOWN_MARKER"
    message: str
    severity: Severity
    source: Optional[SourceSpan] = None
    rule_id: Optional[str] = None     # e.g. "common.page.margins.portrait"
    suggestion: Optional[str] = None


# Standard diagnostic codes
class DiagnosticCodes:
    TXT_UNKNOWN_MARKER = "TXT_UNKNOWN_MARKER"
    TXT_CYRILLIC_IN_MARKER = "TXT_CYRILLIC_IN_MARKER"
    TXT_DUPLICATE_ID = "TXT_DUPLICATE_ID"
    TXT_MISSING_BLOCK_END = "TXT_MISSING_BLOCK_END"
    TXT_MALFORMED_ATTRIBUTE = "TXT_MALFORMED_ATTRIBUTE"
    TXT_INVALID_TABLE_SHAPE = "TXT_INVALID_TABLE_SHAPE"
    TXT_IMAGE_NOT_FOUND = "TXT_IMAGE_NOT_FOUND"
    TXT_IMAGE_OUTSIDE_ROOT = "TXT_IMAGE_OUTSIDE_ROOT"
    TXT_UNSUPPORTED_SYNTAX = "TXT_UNSUPPORTED_SYNTAX"
    FORMAT_MARGIN_LEFT = "FORMAT_MARGIN_LEFT"
    FORMAT_MARGIN_RIGHT = "FORMAT_MARGIN_RIGHT"
    FORMAT_FONT_NAME = "FORMAT_FONT_NAME"
    FORMAT_FONT_SIZE = "FORMAT_FONT_SIZE"
    FORMAT_LINE_SPACING = "FORMAT_LINE_SPACING"
    FORMAT_INDENT = "FORMAT_INDENT"
    FORMAT_ALIGNMENT = "FORMAT_ALIGNMENT"
```

### 4. `src/sfu_converter/domain/formatting.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class RuleSeverity(Enum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    ADVISORY = "advisory"


class RuleStatus(Enum):
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_SUPPORTED = "not_supported"


@dataclass(frozen=True)
class FormattingRule:
    """A single formatting rule linked to the SFU standard."""
    id: str                           # e.g. "common.page.margins.portrait"
    source_doc: str                   # e.g. "docs/formatting requirements/common.md"
    source_section: str               # e.g. "Page and paper setup"
    severity: RuleSeverity
    parameters: dict = field(default_factory=dict)
    renderer_status: RuleStatus = RuleStatus.NOT_SUPPORTED
    validator_status: RuleStatus = RuleStatus.NOT_SUPPORTED
    description: str = ""


@dataclass(frozen=True)
class FormattingProfile:
    """A collection of rules for a specific document type."""
    name: str                         # e.g. "lab_practical_project_reports"
    display_name: str
    source_docs: tuple[str, ...]
    rules: tuple[FormattingRule, ...] = ()
```

## Tests to write

Create `tests/test_domain_ast.py`:
- Test that all AST nodes are immutable (frozen dataclass)
- Test `Document` creation with various block types
- Test `Diagnostic` creation with all severity levels
- Test `FormattingRule` and `FormattingProfile` creation
- Test `SourceSpan` with line/column info
- Test that `BlockNode` union type accepts all valid block types

## Verification

1. `python -m pytest tests/test_domain_ast.py` passes
2. All node types can be instantiated and are immutable
3. No imports from `python-docx` or infrastructure in domain layer
