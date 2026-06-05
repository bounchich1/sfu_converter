# Task 20: Build a Document-Wide Reference Graph and Cross-Reference Validator

## Priority: High
## Phase: Phase 5 (Validator + lint)
## Standard reference
- PDF §7.6 (formula references), §7.7 (table references), §7.8 (figure
  references), §7.9 (in-text source references), §7.11 (appendix
  references), §6.4 (TOC must match real headings).
- Audit *7.9 Библиографические ссылки* (PARTIAL/MISSING) and the per-type
  rows "Reference checking: every figure/table referenced in text".

## Affected files
- `src/sfu_converter/domain/reference_graph.py` *(new)*
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/application/convert.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_reference_graph.py` *(new)*
- `tests/test_docx_validator.py`

## Current state

`ReferenceNode` exists with a `target` string; the parser leaves in-text
`[N]` markers untouched in body runs. There is no graph linking
figures/tables/formulas/appendices/sources to their referers, so the
"every figure must be referenced" rule cannot be enforced.

## Implementation

1. Add `ReferenceTargetKind` enum: `FIGURE, TABLE, FORMULA, APPENDIX,
   SOURCE, FOOTNOTE, SECTION, FORM`.
2. Build `ReferenceGraph` during the application pass. Collect:
   - definition sites: `FigureNode.id`, `TableNode.id`,
     `FormulaNode.id`, `AppendixNode.letter`, `SourceRecordNode.number`,
     headings with `id`.
   - reference sites: scan body runs and explicit
     `[REF target=figure:f1]` markers for tokens:
     - `[N]`, `[N, с. M]`, `[N, т. T, с. M]`, `[59; 67, с. 40-46; 82]`
       (source references — see Task 21);
     - `(рисунок N)`, `(таблица N)`, `(формула (N))`, `(приложение Х)`
       (case-insensitive, accept `рис.`, `табл.`, `прил.`);
     - `(см. таблицу N)` and `(см. рисунок N)`.
3. Resolve references against the graph. Produce diagnostics:
   - `REFERENCE_UNRESOLVED` (severity `ERROR`) when the target does not
     exist;
   - `REFERENCE_AMBIGUOUS` when multiple definitions share an id;
   - `REFERENCE_OBJECT_UNUSED` (severity `WARNING`) for figures/tables/
     formulas without any inbound reference;
   - `REFERENCE_BIBLIOGRAPHY_UNUSED` (`WARNING`) for source records that
     no `[N]` cites;
   - `REFERENCE_APPENDIX_UNUSED` (`WARNING`) for appendices nothing
     refers to.
4. Expose `ReferenceGraph` to the renderer so figures/tables/formulas can
   emit the appropriate hyperlinks / number look-ups, and so Task 16's
   placement diagnostic can read "first reference paragraph index".
5. Flip rules to `IMPLEMENTED`:
   - `common.reference.cross_check`,
   - `common.reference.figure_table_formula`,
   - `common.appendix.in_text_reference`.

## Tests

- `[FIGURE id=f1]` followed by `(рисунок 1)` resolves cleanly.
- `(рисунок 99)` produces `REFERENCE_UNRESOLVED` citing the missing id.
- A figure with no referencing token produces
  `REFERENCE_OBJECT_UNUSED`.
- Two `[FIGURE id=f1]` definitions produce
  `REFERENCE_AMBIGUOUS`.
- `(см. приложение А)` resolves to the appendix and adds an "appendix
  used" edge in the graph.
- A source record numbered `[7]` with no `[7]` reference triggers
  `REFERENCE_BIBLIOGRAPHY_UNUSED`.

## Verification

```bash
python -m pytest tests/test_reference_graph.py tests/test_docx_validator.py
```

## Notes / dependencies

- Task 21 (citation parser) supplies the structured `[N, с. M]` tokens
  consumed here.
- Task 16/15/17 rely on this graph for placement and "never referenced"
  warnings.
