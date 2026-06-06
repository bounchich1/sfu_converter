# SFU Converter — TXT to DOCX (SFU Standard)

Converts structured TXT files into DOCX formatted per Siberian Federal University (SFU / СФУ) standards. Supports multiple document profiles, automatic title pages, bibliography, formulas, and validation.

## Installation

```bash
git clone https://github.com/Nikita2005qwe/sfu_converter.git
cd sfu_converter
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
```

## CLI

```bash
sfu-converter <command> [options]
```

| Command           | Description                                |
|-------------------|--------------------------------------------|
| `convert`         | Convert TXT to DOCX                        |
| `validate-docx`   | Validate existing DOCX against profile     |
| `parse`           | Parse TXT to AST (JSON)                    |
| `lint`            | Lint TXT syntax + profile rules            |
| `list-profiles`   | Show available formatting profiles         |
| `explain-syntax`  | Print syntax reference                     |
| `export-schema`   | Export JSON schemas (ast, diagnostics, etc) |
| `interactive`     | Legacy interactive menu                    |

### Convert example

```bash
sfu-converter convert \
  --input report.txt \
  --output report.docx \
  --profile lab_practical_project_reports \
  --syntax-version 2 \
  --strict \
  --format json
```

### Common flags

| Flag                 | Description                                    |
|----------------------|------------------------------------------------|
| `--syntax-version`   | `1` (legacy) or `2` (recommended)              |
| `--profile`          | Formatting profile name                        |
| `--strict`           | Treat warnings as errors                       |
| `--format json`      | Machine-readable JSON output                   |
| `--quiet`            | Suppress non-essential stderr                  |
| `--template`         | Path to DOCX template for title pages          |
| `--template-mode`    | `append`, `preserve-prefix`, `replace-body`    |

## TXT Syntax (Version 2)

Version 2 is the recommended format. All markers use Latin uppercase, attributes use `key=value`, quoted values support spaces.

### Document header

```text
[DOC syntax=2 profile=lab_practical_project_reports language=ru]
[META key=title value="Отчёт по лабораторной работе"]
[META key=student value="Иванов И.И."]
[META key=group value="КИ22-01"]
[META key=supervisor value="Петров А.В."]
[META key=city value="Красноярск"]
[META key=year value="2025"]
```

### Headings (H1–H4)

```text
[H level=1 title="Введение"]
[H level=2 title="Обзор литературы" number=1]
[H level=3 title="Этапы работы"]
[H level=4 title="Подготовительный этап"]
```

Headings with well-known structural titles (`ВВЕДЕНИЕ`, `ЗАКЛЮЧЕНИЕ`, `СОДЕРЖАНИЕ`, `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ`, etc.) are auto-detected as structural sections — they render with special formatting per profile rules.

### Paragraphs

```text
[P] Обычный абзац текста. Поддерживается **жирный** и *курсив*.
```

All body text must be wrapped in `[P]`. Plain text without a marker produces a diagnostic warning (error in strict mode).

### Figures

```text
[FIGURE src="diagram.png" caption="Общая схема" id=fig:overview]
```

| Attribute  | Required | Description               |
|------------|----------|---------------------------|
| `src`      | no       | Image filename            |
| `caption`  | no       | Caption text              |
| `id`       | no       | Referenceable identifier  |

### Tables

```text
[TABLE caption="Метрики" id=tbl:metrics header=true]
| Метрика   | Значение |
| Accuracy  | 0.94     |
| Recall    | 0.91     |
[TABLE_END]
```

First row is treated as header unless `header=false`. All rows must have equal cell count.

### Lists

```text
[LIST type=bullet]
[-] Первый пункт
[-] Второй пункт
[LIST_END]
```

| `type` value                     | Result          |
|----------------------------------|-----------------|
| `bullet`, `unordered`, `ul`      | Bullet list     |
| `numbered`, `ordered`, `ol`      | Numbered list   |
| `lettered`, `alpha`              | Lettered list   |

### Formulas

```text
[FORMULA id=eq:energy number=1]
E = mc^2
[FORMULA_END]
[FORMULA_EXPLANATION] где E — энергия, m — масса, c — скорость света
```

Multi-line formula content between `[FORMULA ...]` and `[FORMULA_END]`. Optional `[FORMULA_EXPLANATION]` on next line.

### References

```text
[REF target=fig:overview]
```

References a figure, table, formula, or appendix by its `id`. Parser checks for duplicate IDs.

### Bibliography sources

```text
[SOURCE number=1] Петров А.В. Машинное обучение. — М.: Наука, 2023.
[SOURCE number=2] Сидорова Е.К. Анализ данных. — СПб.: Питер, 2024.
```

### Page breaks

```text
[PAGE_BREAK]
```

### Appendices

```text
[APPENDIX id=app:a title="Исходные данные"]
```

### Raw / escaped text

```text
[RAW]
[This line is literal, not parsed as a marker]
[RAW_END]
```

## Formatting profiles

```bash
sfu-converter list-profiles --format json
```

| Profile                              | Description                               |
|--------------------------------------|-------------------------------------------|
| `common`                             | Shared baseline rules                     |
| `lab_practical_project_reports`       | Lab / Practical / Project reports         |
| `practice_reports`                    | Practice reports                          |
| `research_reports`                    | Research-work reports                     |
| `coursework`                         | Course project / Course work              |
| `graduation_qualification_work`       | VKR (graduation qualification work)       |
| `small_written_works`                 | Referat / Control / Calc-graphic / Essay  |
| `graphic_and_demonstration_materials` | Graphic and demonstration materials       |
| `project_designations`               | Project designations                      |

## Full V2 example

```text
[DOC syntax=2 profile=lab_practical_project_reports language=ru]
[META key=title value="Разработка REST API"]
[META key=student value="Иванов И.И."]
[META key=group value="КИ22-01"]

[H level=1 title="Введение"]
[P] Целью работы является разработка REST API для управления каталогом товаров.

[H level=2 title="Теоретическая часть" number=1]
[P] REST — архитектурный стиль взаимодействия компонентов распределённой системы.

[TABLE caption="Методы HTTP" id=tbl:http]
| Метод  | Описание                |
| GET    | Получение ресурса       |
| POST   | Создание ресурса        |
| PUT    | Обновление ресурса      |
| DELETE | Удаление ресурса        |
[TABLE_END]

[P] Как показано в [REF target=tbl:http], протокол HTTP определяет четыре основных метода.

[H level=2 title="Практическая часть" number=2]

[FIGURE src="architecture.png" caption="Архитектура системы" id=fig:arch]

[FORMULA id=eq:complexity number=1]
O(n log n)
[FORMULA_END]
[FORMULA_EXPLANATION] где n — количество элементов

[H level=1 title="Заключение"]
[P] Поставленные цели достигнуты. Разработан REST API с полным CRUD.

[H level=1 title="Список использованных источников"]
[SOURCE number=1] Филдинг Р. REST: принципы. — 2000.
[SOURCE number=2] Ричардсон Л. RESTful Web APIs. — O'Reilly, 2013.

[PAGE_BREAK]
[APPENDIX id=app:a title="Листинг кода"]
[P] Исходный код серверной части приложения.
```

## Diagnostics

Parser reports structured diagnostics with codes, severity, and source location.

Key diagnostic codes:

| Code                          | Meaning                                  |
|-------------------------------|------------------------------------------|
| `TXT_UNKNOWN_MARKER`          | Unrecognized `[...]` marker              |
| `TXT_DUPLICATE_ID`            | Same `id` used on multiple blocks        |
| `TXT_MISSING_BLOCK_END`       | Missing `[TABLE_END]`, `[LIST_END]`, etc |
| `TXT_MALFORMED_ATTRIBUTE`     | Bad attribute in marker                  |
| `TXT_INVALID_TABLE_SHAPE`     | Row cell count mismatch                  |
| `TXT_UNSUPPORTED_SYNTAX`      | Unknown syntax version in `[DOC]`        |
| `TXT_CYRILLIC_IN_MARKER`      | Cyrillic lookalikes in marker name       |
| `INVALID_HEADING_LEVEL`       | Heading level outside 1–4                |

Use `--format json` to get machine-readable diagnostics.

## Cyrillic marker warning

Markers must use **Latin** characters. Cyrillic lookalikes (`Н` instead of `H`, `Т` instead of `T`) break parsing silently.

Check: `python -m sfu_converter.tools.check_cyrillic_markers`
Fix:   `python -m sfu_converter.tools.fix_cyrillic_markers`

## Formatting standards

Body text: Times New Roman 14pt, justified, 1.25cm first-line indent, 1.5 line spacing.

| Element        | Alignment | Bold | Line spacing | First indent |
|----------------|-----------|------|--------------|--------------|
| H1             | Center    | Yes  | 1.0          | 0            |
| H2             | Left      | Yes  | 1.0          | 0            |
| H3             | Left      | No   | 1.0          | 0            |
| Body text      | Justified | No   | 1.5          | 1.25 cm      |
| Figure caption | Center    | No   | 1.5          | 0            |
| Table caption  | Left      | No   | 1.5          | 0            |

## Development

```bash
python -m pytest                                                        # run tests
python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing  # coverage
```

## Project structure

```
src/sfu_converter/
  cli.py              # CLI entry point
  parser/             # V1 + V2 TXT parsers
  domain/             # AST nodes, formatting rules, diagnostics
  application/        # Composition, conversion use cases
  infrastructure/     # DOCX renderer, validator, title pages
  registry/           # Profiles + rules registry
  tools/              # Cyrillic marker checker/fixer
docs/                 # Formatting & technical requirements
examples/             # Example TXT files
templates/            # DOCX templates
```
