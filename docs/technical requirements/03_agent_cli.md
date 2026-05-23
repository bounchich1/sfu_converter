# Agent CLI requirements

## Goal

The project must expose a deterministic, non-interactive CLI that an AI agent can call safely from scripts. The CLI must never require prompts unless the explicit `interactive` command is used.

The executable name should be:

```bash
sfu-converter
```

During development, `python -m sfu_converter` must expose the same command surface.

## Global behavior

- All commands must accept absolute and relative paths.
- All commands must support `--format json` and `--format text`; JSON is required for agent workflows.
- Machine-readable output must go to stdout.
- Logs, progress messages, and human warnings must go to stderr.
- `--quiet` must suppress non-essential stderr output.
- `--no-color` must disable ANSI color.
- `--workdir PATH` must define the base directory for relative assets, templates, and output.
- Commands must return stable exit codes.

## Required commands

### `parse`

Parses TXT into the canonical AST without writing DOCX.

```bash
sfu-converter parse --input examples/report_10_full.txt --syntax-version 1 --format json
```

### `lint`

Validates TXT syntax and formatting-profile compatibility.

```bash
sfu-converter lint --input report.txt --profile lab_practical_project_reports --format json
```

### `convert`

Converts TXT to DOCX.

```bash
sfu-converter convert --input report.txt --output results/report.docx --profile lab_practical_project_reports --strict --format json
```

Required options:

- `--input PATH`
- `--output PATH`
- `--profile NAME`

Optional options:

- `--template PATH_OR_NAME`
- `--template-mode append|preserve-prefix|replace-body`
- `--insert-after-page N`
- `--insert-at-bookmark NAME`
- `--validate-template include|exclude|prefix-only`
- `--syntax-version 1|2`
- `--strict`
- `--validate-output`
- `--diagnostics PATH`

Template behavior:

- `--template` accepts a DOCX template path or a registered template name.
- `--template-mode preserve-prefix` is required for already-formatted title pages or assignment pages that must not be changed.
- `--insert-after-page 1` means generated content starts after the first template page.
- `--insert-after-page 2` means generated content starts after the second template page.
- `--insert-at-bookmark NAME` inserts content at a named DOCX bookmark or content control and is preferred for complex templates.
- If no insertion option is provided, generated content is appended after the full template.
- In preserve mode, the CLI must not rewrite preserved pages and must report a diagnostic if that guarantee cannot be met.

### `validate-docx`

Validates an existing DOCX against a formatting profile.

```bash
sfu-converter validate-docx --input results/report.docx --profile research_reports --format json
```

### `list-profiles`

Lists available formatting profiles and their linked formatting documents.

```bash
sfu-converter list-profiles --format json
```

### `explain-syntax`

Prints the supported TXT syntax for a syntax version.

```bash
sfu-converter explain-syntax --syntax-version 2 --format json
```

### `export-schema`

Emits JSON schemas for AST, diagnostics, command results, and formatting profiles.

```bash
sfu-converter export-schema --schema diagnostics --format json
```

### `interactive`

Starts the legacy human menu. This command may prompt, but no other command may.

```bash
sfu-converter interactive
```

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success, no errors |
| 1 | Completed with warnings when `--strict` is enabled |
| 2 | Syntax or validation errors |
| 3 | Missing input, image, template, or profile |
| 4 | Output write failure |
| 5 | Internal application error |
| 64 | Invalid CLI usage |

## JSON result contract

Every JSON command result must include:

- `ok`: boolean;
- `command`: command name;
- `inputs`: normalized input paths and options;
- `outputs`: generated files or schemas;
- `profile`: selected formatting profile when applicable;
- `syntaxVersion`: detected or requested syntax version;
- `diagnostics`: array of structured diagnostics;
- `durationMs`: integer.

No command may print ad hoc success strings in JSON mode.
