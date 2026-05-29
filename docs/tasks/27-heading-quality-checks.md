# Task 27: Implement Heading Quality Checks (Two-Sentence Separator, No Hyphenation, Point Requires Subpoints, Spacing)

## Priority: Medium
## Phase: Phase 5 (Validator)
## Standard reference
- PDF §7.5 (p. 19): headings must use capital first letter, must not end
  with a period, must not break words across lines, must be separated from
  body by one blank line, two-sentence headings are separated by a period
  with the second sentence written without a final period. Points appear
  only if a subsection has two or more subpoints.
- Audit *7.5 Заголовки* — most rows MISSING.

## Affected files
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/application/heading_checks.py` *(new)*
- `src/sfu_converter/registry/rules.py`
- `tests/test_heading_checks.py` *(new)*
- `tests/test_docx_validator.py`

## Current state

The validator enforces the no-period rule and basic alignment/bold/spacing
of H1-H3. Hyphenation, multi-sentence separation, spacing before/after,
and the "point requires subpoints" structural rule are MISSING.

## Implementation

1. `application/heading_checks.run(document, profile)` walks heading nodes
   and emits diagnostics:
   - `HEADING_HYPHENATION`: detect soft hyphens (`­`) and explicit
     `-\n` line breaks in heading text; reject under
     `common.heading.no_hyphenation`.
   - `HEADING_TWO_SENTENCE`: when the heading contains a period not at the
     end, the second sentence must not have a trailing period and the
     first sentence must end with a period followed by a single space
     (rule `common.heading.two_sentence_separator`).
   - `HEADING_POINT_REQUIRES_SUBPOINTS`: an H3 must have at least two
     direct H4 children (only enforced when the section contains any
     H4 — single-H3 sections are accepted as-is).
   - `HEADING_LEVEL_SKIPPED`: H1 followed by H3 (Task 08 already emits
     this; deduplicate).
2. Validator side: spacing-before / spacing-after rules
   (`common.heading.spacing_before`, `common.heading.spacing_after`) are
   confirmed by counting empty paragraphs around the heading. Flip both
   `validator_status` to `IMPLEMENTED`.
3. Apply the new rule IDs from Task 04:
   - `common.heading.no_hyphenation`,
   - `common.heading.two_sentence_separator`,
   - `common.heading.point_requires_subpoints`.

## Tests

- Heading `Первая часть. Вторая часть` accepted; heading
  `Первая часть. Вторая часть.` triggers
  `HEADING_TWO_SENTENCE` because the second sentence ends with a period.
- Heading containing `­` triggers `HEADING_HYPHENATION`.
- An H3 with one H4 child does not trigger
  `HEADING_POINT_REQUIRES_SUBPOINTS`; the same H3 with one H4 and one H4
  sibling skipped triggers it.
- Spacing-before / spacing-after rules report mismatches at
  paragraph-level granularity.

## Verification

```bash
python -m pytest tests/test_heading_checks.py tests/test_docx_validator.py
```

## Notes / dependencies

- Depends on Task 05 (paragraph roles) so heading paragraphs are reliably
  identifiable.
