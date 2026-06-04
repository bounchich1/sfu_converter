# Task 06: Apply Custom Paragraph Styles in the DOCX Renderer

## Priority: High (paired with Task 05)
## Phase: Phase 5 (Renderer)
## Standard reference
- Audit "Validator coverage at a glance" — without distinct paragraph styles
  the validator must guess paragraph roles from text, which is brittle.
- PDF §6.4 (Содержание with Word heading styles) and §7.5 (heading styles).

## Affected files
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_styles.py` *(new)*
- `tests/test_docx_renderer.py`
- `tests/test_paragraph_roles.py`
- `tests/test_template_adapter.py`

## Current state

`_apply_word_heading_style` attaches `Heading 1/2/3` for H1-H3 so Word's TOC
field can see headings. Other paragraph types use ad-hoc inline runs without
any style. The validator therefore cannot tell a figure caption from body
text by looking at `paragraph.style.name`.

## Implementation

1. Create `infrastructure/docx_styles.py` with constants and a
   `register_styles(document)` helper that idempotently registers:
   - `SFUStructuralHeading` based on `Normal`, centered, bold, uppercase, no
     first-line indent.
   - `SFUTableCaption` based on `Caption`, left-aligned, no first-line indent.
   - `SFUFigureCaption` based on `Caption`, centered, no first-line indent.
   - `SFUFigureExplanatory` based on `Normal`, centered, 12 pt.
   - `SFUFigurePlaceholder` based on `Normal`, italic, no indent.
   - `SFUFormulaBody` based on `Normal`, centered, indent 1.25 cm, with the
     right-aligned tab stop for the formula number.
   - `SFUFormulaExplanation` based on `Normal`, left-aligned, no indent.
   - `SFUBibliographyEntry` based on `Normal`, justified, indent 1.25 cm.
   - `SFUListItem` based on `Normal`, justified, indent 1.25 cm.
   - `SFUTOCHeading` based on `SFUStructuralHeading` for the contents page.
   - `SFUAppendixHeading` based on `Normal`, centered, bold.
   - `SFUFrameMainInscription` (placeholder for Task 28).
2. Apply the right style at every renderer call site:
   - `_render_structural_section` → `SFUStructuralHeading`.
   - `_format_table_caption` → `SFUTableCaption`.
   - `_format_figure_caption` → `SFUFigureCaption`.
   - `_render_figure` (placeholder branch) → `SFUFigurePlaceholder`.
   - `_render_formula` body → `SFUFormulaBody`; explanation lines →
     `SFUFormulaExplanation`.
   - `_render_bibliography_entry` → `SFUBibliographyEntry`.
   - `_render_list_item` → `SFUListItem`.
   - `_render_table_of_contents` heading → `SFUTOCHeading`.
   - `_render_appendix` heading → `SFUAppendixHeading`.
3. Move `Heading 1/2/3` style application into the same module and add
   `Heading 4` for Task 08.
4. Keep direct paragraph formatting (alignment, spacing) so Word users can
   reformat without losing the SFU style — the style supplies defaults, the
   direct format wins.
5. Make sure the `template_adapter` does not strip the new styles when a
   template is loaded; tests must cover that the style names survive
   round-tripping through `template_adapter.merge`.

## Tests

- After rendering, the resulting DOCX exposes `Styles[<each>]` via
  `document.styles[name]` for every name above.
- The first paragraph of each test fixture has the expected style name.
- Re-rendering with `--template <existing.docx>` preserves the style names.
- `paragraph_roles.classify` returns the matching `ParagraphRole` for each
  emitted paragraph (golden fixture).

## Verification

```bash
python -m pytest tests/test_docx_renderer.py tests/test_paragraph_roles.py tests/test_template_adapter.py
```

## Notes / dependencies

- Required for Task 05 to drop its regex fallbacks for production validation.
- Subsequent tasks rely on style-based classification rather than text
  pattern guessing.
