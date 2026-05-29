from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .ast_nodes import SourceSpan


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True)
class Diagnostic:
    """A structured diagnostic message."""

    code: str
    message: str
    severity: Severity
    source: SourceSpan | None = None
    rule_id: str | None = None
    suggestion: str | None = None
    target: str | None = None
    data: Mapping[str, Any] | None = None


class DiagnosticCodes:
    MISSING_PROFILE = "MISSING_PROFILE"
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
    FORMAT_MARGIN_TOP = "FORMAT_MARGIN_TOP"
    FORMAT_MARGIN_BOTTOM = "FORMAT_MARGIN_BOTTOM"
    FORMAT_FONT_NAME = "FORMAT_FONT_NAME"
    FORMAT_FONT_SIZE = "FORMAT_FONT_SIZE"
    FORMAT_FONT_COLOR = "FORMAT_FONT_COLOR"
    FORMAT_LINE_SPACING = "FORMAT_LINE_SPACING"
    FORMAT_INDENT = "FORMAT_INDENT"
    FORMAT_ALIGNMENT = "FORMAT_ALIGNMENT"
    FORMAT_PARAGRAPH_SPACING = "FORMAT_PARAGRAPH_SPACING"
    FORMAT_HEADING_BOLD = "FORMAT_HEADING_BOLD"
    FORMAT_HEADING_NO_PERIOD = "FORMAT_HEADING_NO_PERIOD"
    FORMAT_TABLE_FONT_SIZE = "FORMAT_TABLE_FONT_SIZE"
    FORMAT_RULE_NOT_SUPPORTED = "FORMAT_RULE_NOT_SUPPORTED"
