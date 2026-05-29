# Migration roadmap

## Phase 1: Package and baseline CLI

Create an installable `sfu_converter` package while preserving current behavior.

Acceptance criteria:

- `python -m sfu_converter` works.
- `sfu-converter interactive` starts the current menu.
- `sfu-converter convert` supports explicit input and output paths.
- Existing tests pass.
- Coverage tooling is installed, even if the gate is not yet 100%.

## Phase 2: Domain AST and compatibility parser

Extract parsing from `TextToDocxConverter` into a versioned parser that emits the domain AST.

Acceptance criteria:

- README syntax parses as syntax version 1.
- Parser diagnostics are structured.
- Existing examples have golden AST snapshots.
- Rendering still produces equivalent DOCX output for existing examples.

## Phase 3: Version 2 syntax

Add explicit, agent-friendly syntax version 2.

Acceptance criteria:

- Version 2 supports metadata, headings, paragraphs, figures, tables, lists, formulas, references, appendices, and raw blocks.
- Version 1 compatibility maps into the same AST.
- `explain-syntax` and `export-schema` describe both supported syntax versions.

## Phase 4: Formatting rule registry

Create structured formatting profiles linked to `docs/formatting requirements/`.

Acceptance criteria:

- Each profile maps to source formatting documents.
- Every implemented style has a rule ID.
- Renderer and validator both consume the same rule registry.
- CLI can list profiles and unsupported rules.

## Phase 5: Renderer and validator rewrite

Move DOCX behavior into infrastructure adapters behind application ports.

Acceptance criteria:

- Application use cases do not import `python-docx`.
- Renderer accepts AST plus profile and emits DOCX.
- Validator reports rule-ID diagnostics.
- Missing images, malformed tables, and unsupported rules are reported deterministically.

## Phase 5A: Template composition

Add DOCX template composition for preserved title pages and front matter.

Acceptance criteria:

- `convert --template ... --template-mode preserve-prefix --insert-after-page 1` preserves page 1 and starts generated content after it.
- `convert --template ... --template-mode preserve-prefix --insert-after-page 2` preserves pages 1-2 and starts generated content after them.
- Bookmark/content-control insertion is supported for templates that define explicit insertion points.
- Preserved template pages are not restyled or rewritten.
- Validation can include or exclude preserved template pages.
- Missing insertion points produce structured diagnostics and non-zero strict-mode exit codes.

## Phase 6: 100% coverage gate

Raise quality gates to the final target.

Acceptance criteria:

- 100% statement and branch coverage enforced in CI.
- CLI tests cover success and failure paths.
- Golden example tests cover existing examples.
- No tests write persistent artifacts during collection.

## Phase 7: DRY hardening and documentation generation

Remove remaining duplication and generate machine-readable docs where useful.

Acceptance criteria:

- Syntax help is generated from syntax metadata.
- CLI JSON schemas are exported and tested.
- Formatting rules are discoverable through CLI.
- Duplicate-code and import-boundary checks pass.

## Phase 8: Deprecation cleanup

Retire obsolete paths only after compatibility is proven.

Acceptance criteria:

- Old `src/main.py` entry remains as a thin compatibility wrapper or is removed in a documented breaking release.
- README is rewritten to point to the new CLI and syntax docs.
- Deprecated syntax behavior has clear warnings and migration examples.
