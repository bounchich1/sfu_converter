"""Idempotent custom paragraph styles used by the renderer (Task 06).

The validator (Task 05) reads ``paragraph.style.name`` to classify each
paragraph. Without distinct styles for figure captions, formula bodies,
bibliography entries, etc., classification has to fall back to brittle text
heuristics. ``register_styles`` attaches the SFU-prefixed styles to a document
once; subsequent calls are no-ops.
"""

from __future__ import annotations

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor

from sfu_converter.config import SIBFUConfig


STRUCTURAL_HEADING = "SFUStructuralHeading"
TABLE_CAPTION = "SFUTableCaption"
TABLE_UNIT = "SFUTableUnit"
TABLE = "SFUTable"
ABBREVIATIONS_TABLE = "SFUAbbreviationsTable"
FIGURE_CAPTION = "SFUFigureCaption"
FIGURE_EXPLANATORY = "SFUFigureExplanatory"
FIGURE_PLACEHOLDER = "SFUFigurePlaceholder"
FORMULA_BODY = "SFUFormulaBody"
FORMULA_EXPLANATION = "SFUFormulaExplanation"
BIBLIOGRAPHY_ENTRY = "SFUBibliographyEntry"
LIST_ITEM = "SFUListItem"
TOC_HEADING = "SFUTOCHeading"
APPENDIX_HEADING = "SFUAppendixHeading"
FRAME_MAIN_INSCRIPTION = "SFUFrameMainInscription"

ALL_SFU_STYLES: tuple[str, ...] = (
    STRUCTURAL_HEADING,
    TABLE_CAPTION,
    TABLE_UNIT,
    TABLE,
    ABBREVIATIONS_TABLE,
    FIGURE_CAPTION,
    FIGURE_EXPLANATORY,
    FIGURE_PLACEHOLDER,
    FORMULA_BODY,
    FORMULA_EXPLANATION,
    BIBLIOGRAPHY_ENTRY,
    LIST_ITEM,
    TOC_HEADING,
    APPENDIX_HEADING,
    FRAME_MAIN_INSCRIPTION,
)


def register_styles(document) -> None:
    """Attach SFU paragraph styles to ``document``; safe to call repeatedly."""

    _register(document, STRUCTURAL_HEADING, base="Normal", bold=True, all_caps=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(0),
              outline_level=0)
    _register(document, TABLE_CAPTION, base="Caption",
              alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(0))
    _register(document, TABLE_UNIT, base="Normal", size=Pt(12),
              alignment=WD_ALIGN_PARAGRAPH.RIGHT, first_line_indent=Cm(0))
    _register_table(document, TABLE)
    _register_table(document, ABBREVIATIONS_TABLE)
    _register(document, FIGURE_CAPTION, base="Caption",
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(0))
    _register(document, FIGURE_EXPLANATORY, base="Normal", size=Pt(12),
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(0))
    _register(document, FIGURE_PLACEHOLDER, base="Normal", italic=True,
              first_line_indent=Cm(0))
    _register(document, FORMULA_BODY, base="Normal",
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(1.25),
              right_tab_pos=SIBFUConfig.FORMULA["number_tab_pos"])
    _register(document, FORMULA_EXPLANATION, base="Normal",
              alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(0))
    _register(document, BIBLIOGRAPHY_ENTRY, base="Normal",
              alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_indent=Cm(1.25))
    _register(document, LIST_ITEM, base="Normal",
              alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_indent=Cm(1.25))
    _register(document, TOC_HEADING, base=STRUCTURAL_HEADING, bold=True, all_caps=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(0))
    _register(document, APPENDIX_HEADING, base="Normal", bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=Cm(0),
              outline_level=0)
    _register(document, FRAME_MAIN_INSCRIPTION, base="Normal")


def apply_word_heading_style(document, paragraph, style_name: str) -> None:
    """Attach a built-in Word heading style when the template provides it."""

    try:
        paragraph.style = document.styles[style_name]
    except KeyError:
        return


def _register(
    document,
    name: str,
    *,
    base: str = "Normal",
    bold: bool = False,
    italic: bool = False,
    all_caps: bool = False,
    alignment=None,
    first_line_indent=None,
    size=None,
    right_tab_pos=None,
    outline_level: int | None = None,
) -> None:
    styles = document.styles
    if name in [s.name for s in styles]:
        return

    style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    if base in [s.name for s in styles]:
        style.base_style = styles[base]

    font = style.font
    font.name = "Times New Roman"
    font.size = size or Pt(14)
    font.bold = bold
    font.italic = italic
    font.color.rgb = RGBColor(0, 0, 0)
    if all_caps:
        font.all_caps = True

    pf = style.paragraph_format
    if alignment is not None:
        pf.alignment = alignment
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent
    if right_tab_pos is not None:
        pf.tab_stops.add_tab_stop(Emu(int(right_tab_pos)), WD_TAB_ALIGNMENT.RIGHT)
    if outline_level is not None:
        _set_outline_level(style, outline_level)


def _register_table(document, name: str) -> None:
    styles = document.styles
    if name in [s.name for s in styles]:
        return

    style = styles.add_style(name, WD_STYLE_TYPE.TABLE)
    font = style.font
    font.name = "Times New Roman"
    font.color.rgb = RGBColor(0, 0, 0)


def _set_outline_level(style, level: int) -> None:
    p_pr = style.element.get_or_add_pPr()
    existing = p_pr.find(qn("w:outlineLvl"))
    if existing is not None:
        p_pr.remove(existing)

    outline = OxmlElement("w:outlineLvl")
    outline.set(qn("w:val"), str(level))
    p_pr.append(outline)
