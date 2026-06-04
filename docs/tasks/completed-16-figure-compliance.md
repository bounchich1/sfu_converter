# Task 16: Implement Figure Compliance (Placement, Explanatory Data, Multi-Sheet, References)

## Priority: High
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.8 (p. 25–26).
- Audit *7.8 Иллюстрации* — placement after first reference, section/appendix
  numbering, explanatory data, multi-sheet labels are all MISSING.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/attributes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/figure_layout.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_figure_layout.py` *(new)*
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

Figures render image + caption (`Рисунок N — Name`, centred), with optional
ID, max width 15 cm. Placement, explanatory data, multi-sheet support, and
`Рисунок A.1` numbering are missing.

## Implementation

1. Extend `FigureNode` with `explanatory_data: tuple[str, ...] | None`,
   `sheet: int | None`, `total_sheets: int | None`.
2. V2 syntax extension:
   ```
   [FIGURE id=f1 src="diagram.png" caption="Архитектура" explanatory="
       1 — модуль ввода
       2 — модуль обработки" sheet=1 total_sheets=3]
   ```
3. Render order:
   - blank-line-before paragraph (style `SFUFigureSpacingBefore`);
   - centred image (max width 15 cm);
   - explanatory data lines (12 pt, centred, `SFUFigureExplanatory`);
   - caption paragraph: `Рисунок N — Name` for sheet 1, or
     `Рисунок N, лист K` for subsequent sheets.
4. Section/appendix numbering pulls from Task 09's numbering context.
5. Placement rule:
   - The renderer emits a `FIGURE_PLACEMENT_NEXT_PAGE` info diagnostic
     when the first reference target is more than three paragraphs after
     the figure (heuristic for "place after first reference").
   - When the figure has no reference at all, emit
     `FIGURE_NEVER_REFERENCED` (warning) under
     `common.reference.figure_table_formula`.
6. Validator:
   - explanatory data paragraphs must be 12 pt and use the
     `SFUFigureExplanatory` style;
   - missing image flag remains an `INFO` diagnostic but does not violate
     body-text rules (Task 05 ensures correct routing);
   - multi-sheet captions must include `, лист K` for sheet ≥ 2.
7. Flip rules to `IMPLEMENTED`:
   - `common.figure.section_numbering`,
   - `common.figure.appendix_numbering`,
   - `common.figure.placement_after_reference` (renderer/info),
   - `common.figure.explanatory_data`,
   - `common.figure.multi_sheet_label`,
   - `common.figure.image`.

## Tests

- A figure inside `[APPENDIX letter=А]` renders `Рисунок А.1 — …`.
- A figure with `sheet=2 total_sheets=3` renders
  `Рисунок 5, лист 2`.
- A figure with explanatory data emits one centred 12 pt paragraph above
  the caption.
- A figure that is never referenced triggers
  `FIGURE_NEVER_REFERENCED`.
- A figure placed before its first reference triggers
  `FIGURE_PLACEMENT_NEXT_PAGE` info diagnostic.

## Verification

```bash
python -m pytest tests/test_figure_layout.py tests/test_v2_parser.py \
                 tests/test_docx_renderer.py tests/test_docx_validator.py
```

## Notes / dependencies

- Depends on Task 09 (numbering) and Task 20 (reference graph). The
  reference checks here delegate to the graph built in Task 20.
