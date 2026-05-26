from __future__ import annotations

from copy import deepcopy

_SYNTAX_SPECS = {
    1: {
        "syntaxVersion": 1,
        "blocks": [
            {
                "name": "heading",
                "marker": "[H1] Title",
                "node": "HeadingNode",
                "description": "Create a numbered heading. [H2] and [H3] create lower levels.",
                "example": "[H1] Introduction",
            },
            {
                "name": "paragraph",
                "marker": "Plain text",
                "node": "ParagraphNode",
                "description": "Any non-marker text line becomes a body paragraph.",
                "example": "This is a paragraph.",
            },
            {
                "name": "figure",
                "marker": "[IMAGE=diagram.png]",
                "node": "FigureNode",
                "description": "Insert an image and optionally use the following caption line.",
                "example": "[IMAGE=diagram.png]",
            },
            {
                "name": "table",
                "marker": "[TABLE_START]",
                "node": "TableNode",
                "description": "Parse pipe-delimited rows until [TABLE_END].",
                "example": "[TABLE_START]\n| A | B |\n[TABLE_END]",
            },
            {
                "name": "list",
                "marker": "[LIST type=bullet]",
                "node": "ListNode",
                "description": "Parse explicit list items until [LIST_END].",
                "example": "[LIST type=bullet]\n[-] item\n[LIST_END]",
            },
            {
                "name": "formula",
                "marker": "[FORMULA]",
                "node": "FormulaNode",
                "description": "Parse formula content until [FORMULA_END].",
                "example": "[FORMULA]\nE = mc^2\n[FORMULA_END]",
            },
            {
                "name": "metadata",
                "marker": "[META key=value]",
                "node": "MetadataNode",
                "description": "Attach document metadata for renderers and templates.",
                "example": "[META title=Report]",
            },
            {
                "name": "table_of_contents",
                "marker": "[TOC]",
                "node": "TableOfContentsNode",
                "description": "Insert a generated table-of-contents placeholder.",
                "example": "[TOC]",
            },
            {
                "name": "title_page",
                "marker": "[TITLE_PAGE]",
                "node": "TitlePageNode",
                "description": "Insert a generated title-page placeholder.",
                "example": "[TITLE_PAGE]",
            },
        ],
    },
    2: {
        "syntaxVersion": 2,
        "blocks": [
            {
                "name": "document",
                "marker": "[DOC syntax=2 profile=common language=ru]",
                "node": "Document",
                "description": "Declare syntax version and document-level metadata.",
                "example": "[DOC syntax=2 profile=lab_practical_project_reports language=ru]",
            },
            {
                "name": "metadata",
                "marker": '[META key=title value="..."]',
                "node": "MetadataNode",
                "description": "Attach a key/value metadata field to the document.",
                "example": '[META key=title value="Report title"]',
            },
            {
                "name": "heading",
                "marker": '[H level=1 title="..." number=auto]',
                "node": "HeadingNode",
                "description": "Create a heading with explicit level, title, and numbering mode.",
                "example": '[H level=1 title="Introduction" number=auto]',
            },
            {
                "name": "paragraph",
                "marker": "[P]",
                "node": "ParagraphNode",
                "description": "Create a normal paragraph from explicit text.",
                "example": "[P] Body text.",
            },
            {
                "name": "figure",
                "marker": '[FIGURE src="..." caption="..." id=fig:id number=auto]',
                "node": "FigureNode",
                "description": "Insert a figure with optional caption and reference id.",
                "example": '[FIGURE src="diagram.png" caption="Overview" id=fig:overview]',
            },
            {
                "name": "table",
                "marker": '[TABLE caption="..." id=tbl:id number=auto]',
                "node": "TableNode",
                "description": "Parse pipe-delimited rows until [TABLE_END].",
                "example": '[TABLE caption="Data"]\n| A | B |\n[TABLE_END]',
            },
            {
                "name": "list",
                "marker": "[LIST type=bullet]",
                "node": "ListNode",
                "description": "Parse explicit list items until [LIST_END].",
                "example": "[LIST type=bullet]\n[-] item\n[LIST_END]",
            },
            {
                "name": "formula",
                "marker": "[FORMULA id=eq:id number=auto]",
                "node": "FormulaNode",
                "description": "Parse formula content until [FORMULA_END].",
                "example": "[FORMULA id=eq:main number=auto]\nE = mc^2\n[FORMULA_END]",
            },
            {
                "name": "reference",
                "marker": "[REF target=id]",
                "node": "ReferenceNode",
                "description": "Insert a reference to a figure, table, formula, or appendix id.",
                "example": "[REF target=fig:overview]",
            },
            {
                "name": "source",
                "marker": "[SOURCE number=1]",
                "node": "BibliographyEntryNode",
                "description": "Add a numbered bibliography/source entry.",
                "example": "[SOURCE number=1] Author. Title. Year.",
            },
            {
                "name": "page_break",
                "marker": "[PAGE_BREAK]",
                "node": "PageBreakNode",
                "description": "Force a page break in the rendered document.",
                "example": "[PAGE_BREAK]",
            },
            {
                "name": "appendix",
                "marker": '[APPENDIX id=app:a title="..."]',
                "node": "AppendixNode",
                "description": "Start an appendix section with optional id and title.",
                "example": '[APPENDIX id=app:a title="Data"]',
            },
            {
                "name": "raw",
                "marker": "[RAW]",
                "node": "RawBlockNode",
                "description": "Escape marker-like text until [RAW_END].",
                "example": "[RAW]\n[This is literal]\n[RAW_END]",
            },
        ],
    },
}


def get_syntax_spec(syntax_version: int) -> dict:
    """Return parser-owned syntax metadata for CLI help and docs."""

    try:
        return deepcopy(_SYNTAX_SPECS[syntax_version])
    except KeyError as exc:
        raise ValueError(f"Unsupported syntax version: {syntax_version}") from exc
