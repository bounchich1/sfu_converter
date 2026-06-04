# Task 02: Implement Remaining Agent CLI Commands (`parse`, `lint`, `list-profiles`, `export-schema`)

## Priority: Critical (every other task assumes machine-readable diagnostics)
## Phase: Phase 3 (Agent CLI)
## Standard reference
- Audit *CLI and orchestration gaps*: `parse`, `lint`, `list-profiles`,
  `export-schema` are stubs that return *Not yet implemented*. Without them,
  agents cannot inspect parser output, profile coverage, or diagnostic schemas
  before running a full conversion.

## Affected files
- `src/sfu_converter/cli.py`
- `src/sfu_converter/parser/__init__.py`
- `src/sfu_converter/parser/syntax_spec.py`
- `src/sfu_converter/registry/profiles.py`
- `src/sfu_converter/registry/loader.py`
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/domain/diagnostics.py`
- `src/sfu_converter/domain/formatting.py`
- `tests/test_cli.py`
- `tests/test_syntax_metadata.py`
- `tests/test_registry.py`

## Current state

`explain-syntax` is implemented from parser metadata. `parse`, `lint`,
`list-profiles`, and `export-schema` route to `cmd_not_implemented()` and exit
with code `4`. The CLI already accepts `--format json|text`, `--workdir`,
`--strict`, and `--profile` for these commands but ignores them.

## Implementation

### `parse`

1. Resolve `--input` against `--workdir`.
2. Choose a parser via `get_parser(args.syntax_version)`. Validate that the
   requested syntax version exists; unknown versions emit
   `UNKNOWN_SYNTAX_VERSION` and exit `3`.
3. Parse the file. Collect parser diagnostics.
4. Serialize the canonical AST to JSON via a deterministic
   `ast_to_json(document)` helper that:
   - emits node `type` strings matching `BlockType` names (`PARAGRAPH`,
     `HEADING`, …);
   - serializes `SourceSpan` as `{"line_start": …, "line_end": …, "col_start":
     …, "col_end": …, "filename": …}`;
   - emits enums (`HeadingLevel`, `StructuralSectionType`, `ListType`) by their
     value/name pair;
   - emits nested blocks recursively for `AppendixNode.blocks`.
5. Return exit `0` on success, `2` if diagnostics include any error/fatal,
   `1` if `--strict` and there are warnings.
6. Output schema: `{ok, command:"parse", syntaxVersion, profile, ast,
   diagnostics, durationMs}`.

### `lint`

1. Parse the TXT (no rendering, no docx).
2. Resolve the profile (Task 01); emit `MISSING_PROFILE` if unknown.
3. Run AST composition checks delivered by Task 07 plus the
   `FORMAT_RULE_NOT_SUPPORTED` enumeration delivered by Task 03.
4. Reuse parser diagnostics; do not duplicate codes.
5. Exit `0`/`1`/`2` according to severity and `--strict`.
6. Output schema: `{ok, command:"lint", syntaxVersion, profile, diagnostics,
   summary:{errors, warnings, infos}}`.

### `list-profiles`

1. For each entry in `PROFILES`, emit:
   - `name`;
   - `displayName`;
   - `sourceDocs` (list of paths, deterministic order);
   - `ruleCount`;
   - `rendererSupport`: count of rules with `renderer_status=IMPLEMENTED`;
   - `validatorSupport`: count with `validator_status=IMPLEMENTED`;
   - `unsupportedRendererRuleIds` (sorted);
   - `unsupportedValidatorRuleIds` (sorted);
   - `requiredMetadata` (union of `required_metadata` parameters across the
     profile's `*.metadata.required` rules);
   - `titlePageForm` (the `form` parameter from the profile's `*.title_page.*`
     rule, if any).
2. Output schema: `{ok, command:"list-profiles", profiles:[…], total}`.

### `export-schema`

1. Support `--schema` values `diagnostics`, `ast`, `profiles`, `results`,
   `coverage_matrix`.
2. Each schema is a JSON Schema 2020-12 dictionary stored in
   `src/sfu_converter/cli_schemas/`. Load on demand to keep startup cheap.
3. Diagnostic schema must include: `code`, `severity` (enum: `error`, `warning`,
   `info`, `fatal`), `message`, `ruleId` (nullable), `source` (object with
   `document`, `section`, `lineStart`, `lineEnd`), `data`.
4. AST schema must mirror `ast_to_json(...)` exactly.
5. Output: print the schema directly to stdout; do not wrap in a result
   envelope unless `--format text` is requested (then print a one-line summary
   and the schema beneath it).

## Tests

- `parse --format json --input <txt>` produces `ok=true`, `ast.blocks` list
  matches the parsed `Document`, and is deterministic (golden file).
- `parse --syntax-version 99 --input <txt>` exits `3` with `UNKNOWN_SYNTAX_VERSION`.
- `parse --input <broken.txt>` exits `2` and includes parser diagnostics.
- `lint --profile coursework --input <txt>` reports malformed markers without
  writing any DOCX.
- `lint --profile coursework --strict --input <warn.txt>` exits `1` when only
  warnings are present.
- `list-profiles --format json` includes every key in `PROFILES`, and the
  `unsupportedRendererRuleIds` list contains
  `coursework.frame.course_project_explanatory_note` for the coursework
  profile.
- `export-schema --schema diagnostics --format json` validates every code
  emitted by parser/converter/validator with `jsonschema.validate(...)`.
- Stub tests for each of the four commands are removed.

## Verification

```bash
python -m pytest tests/test_cli.py tests/test_syntax_metadata.py tests/test_registry.py
python -m sfu_converter parse --input tests/test_input.txt --format json | python -m json.tool >/dev/null
python -m sfu_converter list-profiles --format json
python -m sfu_converter export-schema --schema diagnostics --format json
```

## Notes / dependencies

- Depends on Task 01 (profile plumbing) and Task 03 (unsupported-rule
  diagnostics) for the `lint` semantics.
- Task 07 (composition validation) supplies extra diagnostics consumed by
  `lint`; if Task 07 is not done yet, `lint` runs without composition checks
  but still passes its own tests.
