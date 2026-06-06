# Task 08: Add Subpoints (H4) to Parser, AST, and Renderer

## Priority: High
## Phase: Phase 3/5 (Parser, renderer)
## Standard reference
- PDF §7.4 — sections (`1`), subsections (`1.1`), points (`1.1.1`), and
  **subpoints (`1.1.1.1`)** are all permitted in the main part. Audit row
  "Subpoints 1.1.1.1 → MISSING".

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/syntax_spec.py`
- `src/sfu_converter/parser/attributes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_styles.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_syntax_metadata.py`

## Current state

`HeadingLevel` only contains H1, H2, H3. The renderer auto-numbers
`{section}.{subsection}.{point}`. Anything deeper is rejected by the parser
or silently flattened.

## Implementation

1. Extend `HeadingLevel` with `H4 = 4`. Update every `match`/`if` ladder that
   maps level to renderer styling.
2. V1 parser: accept `[H4] …` as a subpoint marker. Keep `[H1]`/`[H2]`/`[H3]`
   behavior unchanged. Reject `[H5]` and higher with
   `INVALID_HEADING_LEVEL`.
3. V2 parser: accept `[HEADING level=4 text="…"]`. `syntax_spec.py` must list
   the new level. `attributes.py` must validate `level in {1,2,3,4}`.
4. Renderer numbering context tracks a 4-tuple `(section, subsection, point,
   subpoint)`. Numbers reset when a higher level increments.
5. The renderer applies a new `Heading 4` Word style (added by Task 06) so
   Word's TOC includes subpoints.
6. The validator routes H4 paragraphs to a new `common.heading.h4` rule
   record (added by Task 04).
7. `parse` JSON output must carry `level: 4`.

## Tests

- V1 input
  ```
  [H1] One
  [H2] One.One
  [H3] One.One.One
  [H4] One.One.One.One
  ```
  renders headings numbered `1`, `1.1`, `1.1.1`, `1.1.1.1`.
- V2 `[HEADING level=4 text="Sub"]` round-trips through `parse`.
- Numbering resets: `[H1] Two` after the above produces `2`, then
  `2.1.1.1` once a deeper heading appears.
- A missing intermediate level (`H1` then `H4`) produces
  `HEADING_LEVEL_SKIPPED` warning.
- The Word `Heading 4` style exists in the output.

## Verification

```bash
python -m pytest tests/test_v1_parser.py tests/test_v2_parser.py \
                 tests/test_docx_renderer.py tests/test_syntax_metadata.py
```

## Notes / dependencies

- Pairs with Task 10 for section-based numbering of tables/figures/formulas
  (the same numbering context is reused there).
