# Testing and 100% coverage requirements

## Coverage policy

Production code must maintain 100% statement coverage and 100% branch coverage. The coverage gate must run in CI and locally.

No production line may be excluded from coverage to satisfy the metric. If code is hard to cover, it must be refactored behind a testable port or moved out of production code.

Required command:

```bash
python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing --cov-fail-under=100
```

The project must add the required coverage tooling to development dependencies.

## Current baseline

The current repository virtual environment runs the existing suite successfully:

```bash
.venv\Scripts\python.exe -m pytest -q
```

Observed result: `28 passed`.

Coverage cannot currently be measured because `coverage` and `pytest-cov` are not installed.

## Required test categories

- Domain unit tests for AST models, formatting rule models, diagnostics, and value objects.
- Parser tests for every valid and invalid syntax block.
- Golden AST tests for existing README syntax examples.
- Lint tests for unknown markers, Cyrillic marker lookalikes, malformed tables, invalid paths, duplicate IDs, and missing block endings.
- Renderer unit tests using fake ports where possible.
- DOCX integration tests that inspect generated document XML and `python-docx` objects.
- Validator tests for every implemented formatting rule ID.
- CLI tests for arguments, stdout/stderr separation, JSON output, text output, and exit codes.
- Compatibility tests proving version 1 syntax maps to the same AST as version 2 equivalents.
- Regression tests for every bug fix before the fix is implemented.

## Test fixture requirements

- Fixtures must not rely on global `examples/`, `results/`, or `templates/` directories unless the test explicitly verifies compatibility behavior.
- Tests must use isolated temporary directories.
- Tests must not write persistent artifacts into `tests/` during collection.
- Example reports in `examples/` must be reusable as golden fixtures through read-only tests.
- Image tests must include PNG, JPEG, transparency, missing file, and oversized image cases.
- Template tests must include appending after page 1, appending after page 2, inserting at a bookmark, preserving existing title-page formatting, excluding preserved pages from generated-content validation, and failing cleanly for missing insertion points.

## Quality gates

Before a change is complete, these checks must pass:

```bash
python -m pytest
python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing --cov-fail-under=100
sfu-converter lint --input examples/report_10_full.txt --profile research_reports --format json
sfu-converter convert --input examples/report_10_full.txt --output .tmp/report_10_full.docx --profile research_reports --validate-output --format json
```

The exact command paths may change during migration, but equivalent gates are mandatory.

## CI requirements

CI must run on Windows and Linux because path handling is core behavior. CI artifacts must include:

- coverage XML and HTML reports;
- generated DOCX samples from golden fixtures;
- JSON diagnostic output for failed lint or validation checks.
