# Task 13: Generate ВКР Реферат (Form П) With Auto-Counted Document Statistics

## Priority: High
## Phase: Phase 5 (Renderer)
## Standard reference
- PDF §6.3 (p. 11): the реферат lists тема, страницы, рисунки, таблицы,
  формулы, приложения, источники, графический материал, then up to 15
  ключевые слова (uppercase, comma-separated, nominative case), then
  цели/задачи/актуальность/новизна/выводы, on **no more than one page**.
- PDF Приложение П (p. 56): exact layout example.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/referat.py` *(new)*
- `src/sfu_converter/registry/rules.py`
- `tests/test_referat.py` *(new)*
- `tests/test_docx_validator.py`

## Current state

`РЕФЕРАТ` is recognized as a structural heading but the converter does not
generate the statistics block or validate keyword formatting.

## Implementation

1. Add a `ReferatNode` AST block with fields `keywords`, `goal`,
   `tasks`, `relevance`, `novelty`, `conclusions`. Counts are computed at
   render time from the rest of the document.
2. V2 parser supports
   `[REFERAT keywords="A, B, C" goal="..." tasks="..." relevance="..."
            novelty="..." conclusions="..."]`.
3. V1 parser supports a multiline block:
   ```
   [REFERAT]
   keywords: A, B, C
   goal: ...
   tasks: ...
   ...
   [/REFERAT]
   ```
4. `referat.render(node, document, ctx) -> Sequence[Paragraph]` produces a
   single page. It calls `ctx.statistics()` to fetch
   `pages_total, figures, tables, formulas, appendices, sources` from the
   numbering context populated during the main render pass.
5. Counts: pages from `ctx.last_rendered_page`; figures/tables/formulas
   from the numbering context counters; appendices from
   `document.blocks` iteration; sources from
   `len([b for b in document.blocks if isinstance(b, BibliographyEntryNode)])`.
6. Two-pass render: do a layout pass first to collect counts, then a
   second pass that injects the реферат page **after** the title page (and
   after Form А for ВКР).
7. Validator rules added:
   - `common.referat.keywords_uppercase`: every keyword must be uppercase
     and separated by commas; max 15.
   - `common.referat.template`: the generated paragraph counts must match
     the document state computed at render time (otherwise a stale
     reference was rendered).
   - `common.referat.length`: ≤ 1 page — emit warning if the rendered
     реферат span overflows.
8. Flip the matching registry rules to
   `renderer_status=IMPLEMENTED`/`validator_status=IMPLEMENTED`.

## Tests

- A document with two appendices, three figures, four tables, five
  formulas, six sources produces a реферат with `Рисунков 3. Таблиц 4.
  Формул 5. Приложений 2. Источников 6.`
- Sixteen keywords trigger `common.referat.keywords_uppercase` with
  `KEYWORDS_TOO_MANY` (`data.maximum=15`, `data.actual=16`).
- Lower-case keyword triggers a diagnostic citing the offending word.
- A реферат that overflows one page logs a length warning.

## Verification

```bash
python -m pytest tests/test_referat.py tests/test_docx_validator.py
```

## Notes / dependencies

- Requires Task 09 (numbering context) for accurate counts.
- ВКР composition validator (Task 07) consumes `requires_referat=True`.
