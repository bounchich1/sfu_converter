# Task 30: Validate Profile Metadata Requirements (`*.metadata.required`)

## Priority: Medium
## Phase: Phase 5 (Validator)
## Standard reference
- PDF §6.2 (title pages); §6.3 (реферат); §9 (project designations). Every
  form lists required metadata fields. The audit row "6.2.2 Required fields
  validation per form" notes the rules exist but are never validated.

## Affected files
- `src/sfu_converter/application/metadata_check.py` *(new)*
- `src/sfu_converter/application/convert.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_metadata_check.py` *(new)*
- `tests/test_docx_validator.py`

## Current state

`*.metadata.required` rule records list the required and optional keys per
profile, but neither the renderer nor the validator inspects the document's
`metadata` dictionary.

## Implementation

1. Add `metadata_check.run(document, profile) -> list[Diagnostic]`.
2. For each rule whose ID ends with `.metadata.required`:
   - read `required_metadata` and `optional_metadata` from
     `rule.parameters`;
   - compute missing keys vs the document's `metadata` MappingProxy;
   - emit `TXT_MISSING_METADATA` (warning) with `data.profile`,
     `data.missing`, `data.ruleId`.
3. Also walk every `*.title_page.form_*` rule whose `form` parameter
   matches the form Task 10 picked for the document, and merge its
   `required_metadata` so the union is checked.
4. Run during the application pass; results land in both the convert
   diagnostics and the lint diagnostics.
5. Independent DOCX validation: when a DOCX is fed back through
   `validate-docx`, harvest metadata from
   `core_properties` and from any `SFUMetadata` style paragraph that the
   renderer leaves behind, so the check also runs against finished
   DOCX files (with `WARNING` severity when fields cannot be recovered).
6. Flip every `*.metadata.required` rule's `validator_status` to
   `IMPLEMENTED`.

## Tests

- Coursework profile with missing `supervisor` produces
  `TXT_MISSING_METADATA` (`data.missing=["supervisor"]`).
- VKR profile with missing `direction_code` produces a diagnostic
  referencing `graduation_qualification_work.title_page.form_b`.
- A document supplying all required keys produces no diagnostic.
- `validate-docx --profile coursework` over a DOCX missing the embedded
  metadata produces `TXT_MISSING_METADATA` with severity `WARNING`.

## Verification

```bash
python -m pytest tests/test_metadata_check.py tests/test_docx_validator.py
```

## Notes / dependencies

- Pair with Task 10 (title page forms) — the union check assumes the
  selected form is known.
