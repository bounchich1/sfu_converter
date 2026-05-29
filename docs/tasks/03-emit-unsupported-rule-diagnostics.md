# Task 03: Emit `FORMAT_RULE_NOT_SUPPORTED` Diagnostics for Renderer and Validator Gaps

## Priority: Critical (traceability + agent self-discovery)
## Phase: Phase 4/5 (Diagnostics)
## Standard reference
- Audit summary "Validator coverage at a glance": 18 of 31 common rules are
  `validator_status=NOT_SUPPORTED`. Conversion and validation today silently
  skip these rules, hiding the gap from the operator.
- `docs/technical requirements/05_formatting_traceability.md` — every rule
  must surface its current support status to consumers.

## Affected files
- `src/sfu_converter/domain/diagnostics.py`
- `src/sfu_converter/domain/formatting.py`
- `src/sfu_converter/application/convert.py`
- `src/sfu_converter/application/profile_support.py` *(new)*
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/cli.py`
- `tests/test_application_convert.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`
- `tests/test_profile_support.py` *(new)*

## Current state

`FormattingRule.renderer_status` and `FormattingRule.validator_status` already
exist, but neither the application layer nor the validator inspects them. The
conversion succeeds silently even when the chosen profile relies on rules with
`renderer_status=NOT_SUPPORTED`.

## Implementation

1. Add a stable code `FORMAT_RULE_NOT_SUPPORTED` to
   `domain/diagnostics.py`, with severity `WARNING`. Include `ruleId`,
   `source` (the rule's `source_doc` + `source_section`), and `target`
   (`renderer` or `validator`).
2. Create `application/profile_support.py` exposing:
   - `unsupported_renderer_rules(profile) -> tuple[FormattingRule, ...]`
   - `unsupported_validator_rules(profile) -> tuple[FormattingRule, ...]`
   - `support_diagnostics(profile, *, target) -> list[Diagnostic]`
3. In `ConvertTextToDocx.execute(...)` (or the orchestrator), call
   `support_diagnostics(profile, target="renderer")` immediately after profile
   resolution; append its output to the result diagnostics list. Do not block
   rendering unless `--strict` promotes warnings.
4. In `DocxValidator.validate(...)`, prepend
   `support_diagnostics(profile, target="validator")` to the diagnostics so
   the user sees the full set of rules that will not be checked.
5. Re-use the same helper inside `cmd_lint` so agents can discover the gaps
   without writing a DOCX.
6. JSON serialization of each diagnostic must include the seven fields:
   `code`, `severity`, `message`, `ruleId`, `source`, `target`, `data`.
7. `--strict` must reuse the existing strict-promotion path: every
   `FORMAT_RULE_NOT_SUPPORTED` warning becomes an error and the process exits
   with the strict-warning code already used elsewhere.
8. Messages template (English; the project is otherwise English-only in code):
   `Rule {rule_id} is not supported by the {target}` — keep the template in a
   single constant for testability.

## Tests

- A synthetic profile with one unsupported renderer rule produces exactly one
  `FORMAT_RULE_NOT_SUPPORTED` diagnostic during conversion.
- `DocxValidator(get_profile("common")).validate(...)` reports exactly the 18
  unsupported validator rule IDs documented in the audit. The set is asserted
  against a frozen fixture so the count cannot drift silently.
- The diagnostic objects round-trip through `diagnostic_to_json()` without
  losing `target` or `source`.
- `--strict` flips at least one of these warnings into the strict exit code in
  `tests/test_cli.py`.
- `cmd_lint --profile coursework` emits the same diagnostics without rendering.
- `unsupported_renderer_rules(get_profile("coursework"))` includes
  `coursework.frame.course_project_explanatory_note` and
  `coursework.title_page.form_i` until those tasks land.

## Verification

```bash
python -m pytest tests/test_profile_support.py tests/test_application_convert.py \
                 tests/test_docx_renderer.py tests/test_docx_validator.py \
                 tests/test_cli.py
```

## Notes / dependencies

- Depends on Task 01 (profile plumbing) so that the unsupported set is
  computed against the chosen profile, not `common`.
- Task 02 (`lint`) consumes the support diagnostics; do not duplicate the
  enumeration there.
