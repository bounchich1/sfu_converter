from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from types import MappingProxyType
from typing import Mapping


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
    STRUCTURAL_SECTION = auto()
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


class StructuralSectionType(Enum):
    ABSTRACT = "РЕФЕРАТ"
    ANNOTATION = "АННОТАЦИЯ"
    CONTENTS = "СОДЕРЖАНИЕ"
    INTRODUCTION = "ВВЕДЕНИЕ"
    CONCLUSION = "ЗАКЛЮЧЕНИЕ"
    ABBREVIATIONS = "СПИСОК СОКРАЩЕНИЙ"
    SOURCES = "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"
    APPENDIX = "ПРИЛОЖЕНИЕ"


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
    filename: str | None = None


@dataclass(frozen=True)
class TextRun:
    """A run of text with optional inline formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    source: SourceSpan | None = None


@dataclass(frozen=True)
class ParagraphNode:
    """A normal text paragraph."""

    runs: tuple[TextRun, ...]
    source: SourceSpan | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "runs", tuple(self.runs))


@dataclass(frozen=True)
class HeadingNode:
    """A heading block."""

    level: HeadingLevel
    text: str
    number: str | None = None
    source: SourceSpan | None = None


@dataclass(frozen=True)
class StructuralSectionNode:
    """A standard structural section heading such as introduction or sources."""

    section_type: StructuralSectionType
    title: str
    source: SourceSpan | None = None


@dataclass(frozen=True)
class TableCell:
    text: str


@dataclass(frozen=True)
class TableRow:
    cells: tuple[TableCell, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))


@dataclass(frozen=True)
class TableNode:
    """A table block."""

    rows: tuple[TableRow, ...]
    caption: str | None = None
    id: str | None = None
    header_row_count: int = 1
    source: SourceSpan | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))


@dataclass(frozen=True)
class TableCaptionNode:
    """A standalone table caption block."""

    text: str
    source: SourceSpan | None = None


@dataclass(frozen=True)
class FigureNode:
    """An image/figure block."""

    src: str | None = None
    caption: str | None = None
    id: str | None = None
    source: SourceSpan | None = None


@dataclass(frozen=True)
class FormulaNode:
    """A formula block."""

    content: str
    id: str | None = None
    number: str | None = None
    explanation: str | None = None
    source: SourceSpan | None = None


@dataclass(frozen=True)
class ListItemNode:
    text: str
    source: SourceSpan | None = None


@dataclass(frozen=True)
class ListNode:
    list_type: ListType
    items: tuple[ListItemNode, ...]
    source: SourceSpan | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))


@dataclass(frozen=True)
class PageBreakNode:
    source: SourceSpan | None = None


@dataclass(frozen=True)
class AppendixNode:
    title: str
    id: str | None = None
    blocks: tuple = ()
    source: SourceSpan | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocks", tuple(self.blocks))


@dataclass(frozen=True)
class BibliographyEntryNode:
    number: int
    text: str
    source: SourceSpan | None = None


@dataclass(frozen=True)
class RawBlockNode:
    """Literal/escaped text that should not be parsed."""

    text: str
    source: SourceSpan | None = None


@dataclass(frozen=True)
class MetadataNode:
    key: str
    value: str
    source: SourceSpan | None = None


BlockNode = (
    ParagraphNode
    | HeadingNode
    | TableNode
    | TableCaptionNode
    | FigureNode
    | FormulaNode
    | ListNode
    | PageBreakNode
    | StructuralSectionNode
    | AppendixNode
    | BibliographyEntryNode
    | RawBlockNode
    | MetadataNode
)


@dataclass(frozen=True)
class Document:
    """Root AST node representing a complete document."""

    blocks: tuple[BlockNode, ...]
    syntax_version: int = 1
    metadata: Mapping[str, str] = field(default_factory=dict)
    source_file: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocks", tuple(self.blocks))
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
