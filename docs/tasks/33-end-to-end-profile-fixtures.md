# Task 33: Add End-to-End Profile Fixtures and Round-Trip Verification

## Priority: Medium (locks every previous task in place)
## Phase: Phase 7 (Testing infrastructure)
## Standard reference
- All previous tasks; this is the integration layer.

## Affected files
- `tests/fixtures/profiles/<profile>/input.txt` *(new)*
- `tests/fixtures/profiles/<profile>/expected_diagnostics.json` *(new)*
- `tests/fixtures/profiles/<profile>/expected_first_page.txt` *(new)*
- `tests/test_profile_e2e.py` *(new)*
- `src/sfu_converter/infrastructure/docx_inspector.py` *(new helper)*

## Current state

`tests/test_input.txt` covers the `common` profile only. There is no
end-to-end fixture per profile that exercises title page generation,
composition validation, numbering, references, and bibliography together.

## Implementation

1. For each implemented profile after Tasks 01–32, add a fixture:
   - `input.txt`: realistic TXT covering title page metadata, structural
     sections, headings up to H4, tables (with continuation, unit label,
     footnote), figures (with explanatory data + multi-sheet), formulas
     (with section/appendix numbering), bibliography (mix of GOST
     record types), appendices (auto-letter + independent-document
     variant when applicable), citations, footnotes, abbreviations.
   - `expected_diagnostics.json`: ordered list of diagnostics with
     stable codes (matches `export-schema --schema diagnostics`).
   - `expected_first_page.txt`: text dump of the title page used for
     golden comparison.
2. `docx_inspector.dump(document) -> str` returns a deterministic
   plain-text representation: section index, paragraph text, paragraph
   style, run formatting, table cell contents, image alt text.
3. `tests/test_profile_e2e.py` for every fixture:
   - runs `cmd_convert` with the profile, captures the rendered DOCX in
     a tmp dir;
   - asserts `dump(document_section_one) == expected_first_page.txt`;
   - asserts diagnostics match `expected_diagnostics.json`;
   - runs `cmd_validate_docx` over the output and asserts it produces
     only `INFO` diagnostics (i.e. no warnings or errors for the
     reference fixture).
4. Add a `tox`/`pytest` mark `e2e` so devs can opt in/out; CI runs
   them with `-m "not slow"` excluded.

## Tests

- E2E for `coursework`, `graduation_qualification_work`,
  `practice_reports`, `research_reports`,
  `lab_practical_project_reports`, `small_written_works`,
  `graphic_and_demonstration_materials`, `project_designations`,
  `common`.
- Failing fixture: missing a required metadata field flips the expected
  diagnostics — drop the field and assert the new diagnostic appears in
  the diff.

## Verification

```bash
python -m pytest tests/test_profile_e2e.py -m e2e
```

## Notes / dependencies

- Requires every previous task. New fixtures must be regenerated when
  the renderer output changes intentionally — the golden helper writes
  the new expected file when `--update-fixtures` flag is set
  (`pytest --update-fixtures`).
