# Task 22: Implement Full Содержание (TOC) Compliance and Form Т Generator

## Priority: Medium
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §6.4 (p. 12): `СОДЕРЖАНИЕ` is omitted for documents shorter than 24
  pages; subsection entries indent ≈ 2 chars from sections; point entries
  indent ≈ 2 chars from subsections; second-line continuations align with
  the heading text; appendix entries grouped as `Приложения А–Т ……58–74`;
  TOC entries must reflect actual headings.
- PDF Приложение Т (p. 57): example СОДЕРЖАНИЕ for КР (course work).
- Audit *6.4 Содержание* — most rows MISSING.

## Affected files
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/toc.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_toc.py` *(new)*
- `tests/test_docx_renderer.py`

## Current state

The renderer inserts a Word TOC field; Word fills it on open. There is no
length check (24-page rule), no indent control, no appendix grouping, no
verification that TOC entries match real headings.

## Implementation

1. Add `toc.build_toc_field(document, *, profile, total_pages)`. It
   computes layout strings independently of Word's runtime field so the
   validator can compare expected entries with whatever Word produced.
2. 24-page rule: when total pages < 24 and the profile is not
   `graduation_qualification_work`, emit
   `TOC_NOT_REQUIRED_FOR_SHORT_DOCUMENT` (info) and skip TOC insertion
   unless the AST contains an explicit `TableOfContentsNode`.
3. Layout:
   - section entries (H1) — flush left, no indent;
   - subsection entries (H2) — indent ~ 2 characters (≈ 0.5 cm);
   - point entries (H3) — additional 2 characters (≈ 1 cm);
   - subpoint entries (H4) — additional 2 characters (≈ 1.5 cm);
   - continuation lines align with heading text via hanging indent;
   - appendix entries collapsed into a single grouped line
     `Приложения А–Т …………… 58–74` when more than two contiguous
     appendices exist; otherwise listed individually.
4. Form Т generator: when `profile == "coursework"` and metadata
   `course_work=true`, render the TOC using the Form Т example as the
   layout reference.
5. Validator additions:
   - `common.toc.indent_levels`: confirm the indents above;
   - `common.toc.matches_headings`: walk Word's TOC entries (after
     unfreezing) and ensure each matches a heading in the document;
   - `common.toc.appendix_grouping`: when ≥ 3 contiguous appendices,
     ensure the grouped line is present.

## Tests

- A 12-page document without explicit TOC node skips the TOC and emits
  the info diagnostic.
- A 30-page document inserts the TOC field with section entries flush
  left and subsection entries indented 0.5 cm.
- Coursework with `course_work=true` triggers the Form Т layout.
- Three appendices А, Б, В collapse into the grouped entry.
- Mismatching TOC entry vs heading text triggers
  `common.toc.matches_headings`.

## Verification

```bash
python -m pytest tests/test_toc.py tests/test_docx_renderer.py
```

## Notes / dependencies

- Depends on Task 09 (numbering) and Task 24 (sheet/page count for the
  24-page rule).
