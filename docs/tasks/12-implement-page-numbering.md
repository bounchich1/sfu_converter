# Task 12: Implement Standards-Compliant Page Numbering

## Priority: High
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.2 (p. 14): pages numbered with sequential Arabic numerals, bottom
  centre, no first-line indent, Times New Roman 14 pt.
- §7.2: title page is **counted** but the number is not printed.
- §5.6: Form А (ВКР assignment) is excluded from numbering.
- §7.1.3: ДП/КП framed sheets place the page number in graph 7 of the
  main inscription, not in the footer.
- Audit row "common.page.numbering" — `validator_status = NOT_SUPPORTED`.

## Affected files
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/page_numbering.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_page_numbering.py` *(new)*
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

The renderer already adds a bottom-centred page-number field. There is no
control over which pages display the number (title page hides it but Form
А — which is now produced by Task 11 — also needs to hide it). Framed-sheet
profiles cannot redirect numbering into the title block. The validator
skips `common.page.numbering` entirely.

## Implementation

1. Replace the inline footer mutation with `page_numbering.configure(...)`.
   It accepts a list of section descriptors:

   ```python
   @dataclass
   class PageNumberingSection:
       start_at: int | None
       hide_first_page: bool
       suppress_in_section: bool
       location: Location  # FOOTER_CENTER | FRAME_FIELD_7
   ```

2. The renderer maps the document into sections:
   - section 1: title page — `hide_first_page=True`, `start_at=1`,
     `location=FOOTER_CENTER`.
   - section 2 (ВКР only): Form А — `suppress_in_section=True`,
     `start_at=2` (or whatever the title page final number is) —
     numbering does not render in this section, but the global counter
     keeps incrementing for the remainder.
   - section 3 onwards: body — `location=FOOTER_CENTER` for normal
     profiles, `FRAME_FIELD_7` for framed coursework / diploma profiles.
3. The `FRAME_FIELD_7` branch wires the number into the title block field
   delivered by Task 24. Until that lands the renderer falls back to
   `FOOTER_CENTER` and the registry rule keeps `IMPLEMENTED` for the
   footer location while `coursework.title_block.field_7_page_number`
   stays `NOT_SUPPORTED`.
4. Validator implementation:
   - Walk every DOCX section. Look up `<w:pgNumType>` and
     `<w:titlePg/>` elements.
   - Confirm Times New Roman 14 pt, no first-line indent, centred (or, for
     framed profiles, that field 7 contains the `PAGE` field).
   - Emit `common.page.numbering` diagnostics when any check fails.
5. Flip `common.page.numbering` →
   `validator_status=IMPLEMENTED`.

## Tests

- A converted document hides the page number on the title page only; pages
  2+ display Arabic numerals starting at 2.
- ВКР conversion yields no number on the two assignment pages and
  resumes numbering on the реферат at the appropriate value.
- A coursework conversion places the number inside the frame's field 7
  (Task 24 delivers the frame; this test asserts that when the frame is
  present, the validator accepts the embedded number).
- The validator reports a diagnostic when the centred field uses a
  non-TNR font.
- The validator reports `common.page.numbering` if the title page's
  `<w:titlePg/>` flag is missing.

## Verification

```bash
python -m pytest tests/test_page_numbering.py tests/test_docx_renderer.py tests/test_docx_validator.py
```

## Notes / dependencies

- Pair with Task 11 (Form А) and Task 24 (framed sheets).
