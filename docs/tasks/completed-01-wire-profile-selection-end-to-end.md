# Task 01: Wire `--profile` Selection End-to-End Through Converter and Validator

## Priority: Critical (blocks every profile-specific feature)
## Phase: Phase 4 (Profiles / orchestration)
## Standard reference
- PDF §1 "Область применения" (p. 4) — each document type carries its own
  rule set; the converter cannot diverge for ВКР, КП/КР, practice reports, etc.
  while every conversion silently falls back to the `common` profile.
- Audit row "Profile per document type" (PARTIAL) and the *CLI and orchestration
  gaps* table line "`--profile` plumbed into conversion → MISSING".

## Affected files
- `src/sfu_converter/cli.py`
- `src/sfu_converter/converter.py`
- `src/sfu_converter/application/convert.py`
- `src/sfu_converter/validator.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/registry/__init__.py`
- `tests/test_cli.py`
- `tests/test_application_convert.py`
- `tests/test_converter.py`
- `tests/test_validator.py`
- `tests/test_docx_validator.py`

## Current state

`converter.py:108` calls `get_profile("common")` unconditionally, and
`StyleValidator` constructs `DocxValidator(get_profile("common"))` regardless of
the CLI flag. The CLI already accepts `--profile`, but the resolved profile is
only echoed back in JSON output; the renderer, validator, and AST checks never
see it.

## Implementation

1. Add a `_resolve_profile(name: str) -> FormattingProfile` helper in
   `cli.py` that looks up the profile via `sfu_converter.registry.get_profile()`
   and raises a `ProfileNotFoundError` (subclass of `CliError`) when the name is
   unknown.
2. In every command handler (`cmd_convert`, `cmd_validate_docx`, `cmd_lint`,
   `cmd_parse`, `cmd_list_profiles`, `cmd_export_schema`), resolve the profile
   before dispatching. Unknown profile → exit code `3` with structured
   diagnostic `{"code": "MISSING_PROFILE", "ruleId": null, ...}`.
3. Change `TextToDocxConverter.convert_file(...)` to require a `profile:
   FormattingProfile` argument (no default). Drop `_default_profile()` from the
   converter; keep it only as a thin CLI-side fallback that resolves to
   `common`.
4. Plumb the same profile object into `ConvertTextToDocx.execute(...)` and
   `DocxRenderer.render_to_file(..., profile=...)`. The renderer must store it
   on `self._profile` so every helper (`_render_title_page`, `_render_appendix`,
   `_render_table_caption`, `_render_figure_caption`, `_render_formula_body`)
   can branch on profile-specific rules.
5. Update `StyleValidator` to accept either a `profile_name: str` or a
   pre-resolved `FormattingProfile` and forward it to `DocxValidator`. Remove
   the hard-coded `get_profile("common")` call.
6. Persist the selected profile name in every JSON result envelope under the
   `profile` key. For `validate-docx`, include it next to `diagnostics`.
7. Update README CLI examples so each profile shows the correct flag.

## Tests

- `cmd_convert(["--profile", "research_reports", ...])` invokes the converter
  with `profile.name == "research_reports"`.
- `cmd_convert(["--profile", "no_such_profile", ...])` exits `3` and writes a
  `MISSING_PROFILE` diagnostic to stdout.
- `cmd_validate_docx(["--profile", "coursework", ...])` creates a `DocxValidator`
  whose profile is the coursework profile.
- `ConvertTextToDocx.execute(...)` raises `TypeError` when called without a
  profile argument (signature change is intentional).
- `DocxRenderer.render_to_file(...)` records the profile name in
  `self._profile.name` and uses it to select profile-specific layout branches
  (asserted by spying on a helper).
- Every JSON result includes `"profile": "<name>"`.
- The CLI `--format text` output prints `Profile: <display_name>` on the first
  line of `convert` and `validate-docx`.

## Verification

```bash
python -m pytest tests/test_cli.py tests/test_application_convert.py \
                 tests/test_converter.py tests/test_validator.py \
                 tests/test_docx_validator.py
python -m sfu_converter convert --profile coursework --input examples/coursework.txt --output build/coursework.docx --format json
python -m sfu_converter validate-docx --profile coursework --input build/coursework.docx --format json
```

The `convert` JSON must contain `"profile": "coursework"`; `validate-docx` JSON
must contain `"profile": "coursework"` and produce diagnostics that reference
`coursework.*` or `common.*` rule IDs only — not `research_reports.*`.

## Notes / dependencies

- Without this task, every subsequent profile-specific task (title pages,
  framed sheets, project designations, structural composition) is dead code.
- Task 03 (unsupported-rule diagnostics) consumes this plumbing; it cannot be
  completed first.
