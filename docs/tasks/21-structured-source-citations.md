# Task 21: Implement Structured Source Citation Parser

## Priority: Medium
## Phase: Phase 3 (Parser)
## Standard reference
- PDF §7.9 (p. 26): citation formats include
  `[20]`, `[20, с. 29]`, `[18, т. 1, с. 75]`, and grouped citations
  `[59; 67, с. 40–46; 82]`. Footnote-style references are covered by Task 19.

## Affected files
- `src/sfu_converter/parser/citations.py` *(new)*
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `tests/test_citations.py` *(new)*
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`

## Current state

`[N]` markers stay as literal text inside paragraph runs; structured forms
like `[20, с. 29]` are not parsed and cannot feed into the reference graph
(Task 20).

## Implementation

1. Add `CitationNode(citations: tuple[Citation, ...])` where

   ```python
   @dataclass(frozen=True)
   class Citation:
       number: int
       volume: int | None = None
       pages: PageRange | None = None  # int or (start, end)
   ```

2. Parser regex (run on body text inside paragraph runs):
   ```
   \[                       # opening bracket
   (?P<inner>
       \d+
       (?:\s*,\s*т\.\s*\d+)?
       (?:\s*,\s*с\.\s*\d+(?:[-–—]\d+)?)?
       (?:\s*;\s*\d+
           (?:\s*,\s*т\.\s*\d+)?
           (?:\s*,\s*с\.\s*\d+(?:[-–—]\d+)?)?
       )*
   )
   \]
   ```
3. Convert the matched substring into a `CitationNode`, replace the literal
   text in the run, keep the original `SourceSpan`.
4. Diagnostics:
   - `CITATION_MALFORMED` when the inner string cannot be parsed by the
     stricter Citation grammar (e.g. `[20, p. 29]`);
   - `CITATION_PAGE_RANGE_REVERSED` when start > end;
   - `CITATION_NUMBER_DUPLICATED` when the same number appears twice in a
     single grouped citation.
5. Renderer: emit `[N]`, `[N, с. M]`, `[N, т. T, с. M]`, joining with
   `; ` exactly as the standard requires (em dash for page ranges).

## Tests

- `[20]`, `[20, с. 29]`, `[18, т. 1, с. 75]`, `[59; 67, с. 40-46; 82]`
  parse into expected `Citation` lists.
- `[20, p. 29]` produces `CITATION_MALFORMED`.
- `[10, с. 50-30]` produces `CITATION_PAGE_RANGE_REVERSED`.
- Round-trip: rendered output matches the original spelling, except
  `40-46` is normalised to `40–46` (en-dash).

## Verification

```bash
python -m pytest tests/test_citations.py tests/test_v1_parser.py tests/test_v2_parser.py
```

## Notes / dependencies

- Feeds Task 20 (reference graph) and Task 18 (per-source page checks).
