# Task 14: Implement Two-Column `СПИСОК СОКРАЩЕНИЙ` Generator

## Priority: Medium
## Phase: Phase 5 (Renderer)
## Standard reference
- PDF §6.8 (p. 13): `СПИСОК СОКРАЩЕНИЙ` is a two-column list with
  abbreviations on the left (alphabetical) and expansions on the right.
- PDF §7.3 (p. 14): abbreviations are introduced at first use in body
  text (`информационно-аналитический комплекс (ИАК)`).

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/abbreviations.py` *(new)*
- `src/sfu_converter/registry/rules.py`
- `tests/test_abbreviations.py` *(new)*
- `tests/test_docx_renderer.py`

## Current state

`СПИСОК СОКРАЩЕНИЙ` is recognized as a structural section heading, but the
renderer outputs nothing under it. Abbreviation introductions in body text
are not detected.

## Implementation

1. Add `AbbreviationEntryNode(short, long)` and `AbbreviationsListNode`
   (optional, when the author wants to override automatic detection).
2. Detect abbreviations in body text using a regex
   `\b([А-ЯA-Z]{2,})\b\s*\(([^)]+)\)` plus a hand-curated exclusion list
   (`ГОСТ`, `СТУ`, `СП`, `ВКР`, `ДП`, `КР`, `КП`, etc. handled by Task 04
   style rules).
3. On a second pass, collect all `(short, long)` pairs in order of first
   use, sort alphabetically by `short`, deduplicate.
4. When rendering the `СПИСОК СОКРАЩЕНИЙ` section, build a two-column
   borderless table:
   - column widths roughly 40 mm / 130 mm;
   - font 14 pt TNR;
   - rows in alphabetical order;
   - separator dash between columns (`ИАК   —   информационно-аналитический
     комплекс`) inside the right cell preceded by an em-dash.
5. If `AbbreviationsListNode` is present, render its entries verbatim
   instead of the auto-collected set; otherwise emit
   `common.abbreviations.auto_detected` informational diagnostics.
6. Flip `common.abbreviations.two_column_layout` →
   `renderer_status=IMPLEMENTED`. Validator status becomes
   `IMPLEMENTED` once the validator can recognise the table layout via
   the `SFUAbbreviationsTable` style (Task 06 extension).

## Tests

- Body containing `… информационно-аналитический комплекс (ИАК) …` and
  `… центр обработки данных (ЦОД) …` generates a two-row table inside
  `СПИСОК СОКРАЩЕНИЙ`, sorted ИАК, ЦОД.
- Repeated occurrences of `(ИАК)` produce a single row.
- `AbbreviationsListNode` overrides detection: only its entries appear.
- Validator confirms the table has the expected width and font.

## Verification

```bash
python -m pytest tests/test_abbreviations.py tests/test_docx_renderer.py
```

## Notes / dependencies

- Pair with Task 26 (style checks) which flags abbreviations in headings.
