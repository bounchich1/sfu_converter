"""Legacy ``SIBFUConfig`` compatibility layer over the formatting registry.

The class attributes are populated from the registry at import time. New code
should reach for ``sfu_converter.registry`` directly; this module remains so
existing callers (renderer, validator, image utils) keep working unchanged.
"""

from __future__ import annotations

from sfu_converter.registry.loader import build_legacy_config

_LEGACY_CONFIG = build_legacy_config()


class SIBFUConfig:
    """Конфигурация стандартов оформления СФУ.

    Compatibility shim. Values come from the rule registry under
    ``sfu_converter.registry``; do not edit constants here.
    """

    FONT_NAME = _LEGACY_CONFIG["FONT_NAME"]
    FONT_SIZE = _LEGACY_CONFIG["FONT_SIZE"]
    FONT_COLOR_RGB = _LEGACY_CONFIG["FONT_COLOR_RGB"]
    LINE_SPACING_NORMAL = _LEGACY_CONFIG["LINE_SPACING_NORMAL"]
    ALIGNMENT = _LEGACY_CONFIG["ALIGNMENT"]
    FIRST_LINE_INDENT = _LEGACY_CONFIG["FIRST_LINE_INDENT"]

    H1 = _LEGACY_CONFIG["H1"]
    H2 = _LEGACY_CONFIG["H2"]
    H3 = _LEGACY_CONFIG["H3"]

    CAPTION_IMAGE = _LEGACY_CONFIG["CAPTION_IMAGE"]
    CAPTION_TABLE = _LEGACY_CONFIG["CAPTION_TABLE"]

    EMPTY_BEFORE_HEADER = _LEGACY_CONFIG["EMPTY_BEFORE_HEADER"]
    EMPTY_AFTER_HEADER = _LEGACY_CONFIG["EMPTY_AFTER_HEADER"]
    EMPTY_BEFORE_IMAGE = _LEGACY_CONFIG["EMPTY_BEFORE_IMAGE"]
    EMPTY_AFTER_IMAGE = _LEGACY_CONFIG["EMPTY_AFTER_IMAGE"]
    EMPTY_BEFORE_TABLE = _LEGACY_CONFIG["EMPTY_BEFORE_TABLE"]
    EMPTY_AFTER_TABLE = _LEGACY_CONFIG["EMPTY_AFTER_TABLE"]

    MARGINS = _LEGACY_CONFIG["MARGINS"]
    IMAGE = _LEGACY_CONFIG["IMAGE"]
    TABLE_CELL_PADDING = _LEGACY_CONFIG["TABLE_CELL_PADDING"]
