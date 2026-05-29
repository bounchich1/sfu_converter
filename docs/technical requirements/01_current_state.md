# Current state analysis

Analysis date: 2026-05-23.

## Project shape

The project is a small Python application that converts UTF-8 TXT files into DOCX files using `python-docx`.

- `src/main.py` wires logging, `TextToDocxConverter`, `StyleValidator`, and `ConsoleMenu`.
- `src/menu.py` provides an interactive terminal menu tied to `examples/`, `templates/`, and `results/`.
- `src/converter.py` combines TXT parsing, document rendering, image insertion orchestration, table creation, style application, and file IO.
- `src/utils_image_insert.py` handles image conversion, sizing, buffering, and DOCX insertion.
- `src/validator.py` validates a limited subset of DOCX styles after generation.
- `src/config.py` stores formatting constants as a Python class.
- `tests/` covers selected converter and validator behavior.

The current test baseline passes in the repository virtual environment:

```bash
.venv\Scripts\python.exe -m pytest -q
```

Result observed during analysis: `28 passed`. Coverage tooling is not installed, so current statement and branch coverage are unknown.

## Current README syntax

The current public TXT language supports:

- `[H1]`, `[H2]`, `[H3]` headings.
- Plain paragraphs for normal text.
- `[IMAGE=path]` followed by a natural-language caption line such as `Рисунок 1 - ...`.
- `[TABLE_CAPTION] ...`.
- `[TABLE_START]` and `[TABLE_END]` table blocks.
- Pipe-delimited table rows such as `| Header 1 | Header 2 |`.

The README also warns that marker names must use Latin letters, because visually similar Cyrillic characters break parsing.

## Strengths

- The application already converts common report content into DOCX.
- Explicit input and output paths are supported through `convert_file`.
- Basic table, image, heading, paragraph, and validation behavior has tests.
- The repository now contains detailed formatting requirement documents grouped by report type.
- The examples directory provides real-world TXT samples that can become golden fixtures.

## Gaps blocking large-scale growth

- There is no package-level CLI with stable command arguments, exit codes, JSON output, or schema output for AI agents.
- The interactive menu is the primary UX and cannot be reliably automated.
- Parsing and rendering are coupled inside `TextToDocxConverter._render_lines`.
- Template loading exists, but template composition is not specified as a first-class behavior: users cannot explicitly preserve page 1 or page 2 and append generated content after that preserved front matter.
- Formatting constants are hard-coded in Python and are not traceable to `docs/formatting requirements/`.
- The validator checks only a narrow subset of the SFU requirements.
- Syntax is informal and unversioned, with ambiguous image caption detection.
- Unknown markers, malformed tables, and Cyrillic marker lookalikes are not represented as structured diagnostics.
- Tests do not enforce 100% coverage, branch coverage, CLI behavior, or formatting-rule traceability.
- Several responsibilities repeat across parser logic, config constants, validator checks, tests, and README prose, creating DRY risk.

## Target state

The rewrite must preserve current useful behavior while introducing a clean, testable core:

- A versioned parser that turns TXT into an explicit document AST.
- A renderer that converts the AST to DOCX using formatting profiles.
- A validator that reports rule-based diagnostics linked to formatting docs.
- A CLI that exposes parse, lint, convert, validate, and schema commands for agents.
- A coverage gate that fails below 100% statement and branch coverage.
