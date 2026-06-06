---
name: sfu-converter
description: Use when generating SFU-formatted (Сибирский Федеральный Университет / СФУ) reports, lab works, coursework, VKR, practice reports, or research reports. Produces V2 TXT syntax accepted by sfu-converter CLI, then lints and converts to DOCX. Trigger when user asks to "write report SFU style", "make lab report", "create coursework TXT", "convert TXT to DOCX SFU", or mentions Russian university documents requiring СТУ 7.5-07-2021 formatting.
---

# SFU Converter Skill

Generate SFU-compliant academic documents in V2 TXT syntax, lint, then convert to DOCX via the `sfu-converter` CLI.

## Prerequisites

User must have `sfu-converter` CLI installed in working dir (or globally):

```bash
git clone https://github.com/Nikita2005qwe/sfu_converter.git
cd sfu_converter
pip install -e ".[dev]"
```

If CLI missing, instruct user to install before proceeding.

## When to use

User asks for any of:
- Lab / practice / coursework / VKR / research report (Russian academic)
- "СФУ", "СибГУ", "Сибирский Федеральный", "СТУ 7.5-07-2021"
- TXT-to-DOCX conversion with academic formatting
- Bibliography, formulas, figures, tables in formal academic layout

## Workflow

```
[gather facts]  → [pick profile] → [write V2 TXT] → [lint] → [fix] → [convert] → [validate DOCX]
```

### Step 1 — Gather metadata before writing

Required minimum:
- title (тема работы)
- student (ФИО студента)
- group (учебная группа)
- year

Recommended:
- supervisor, city, profile name, faculty, course number

If missing, ask user once. Don't invent FIO or group numbers.

### Step 2 — Pick profile

| User says                              | Profile                              |
|----------------------------------------|--------------------------------------|
| "лабораторная", "практическая работа"  | `lab_practical_project_reports`      |
| "отчёт по практике"                    | `practice_reports`                   |
| "НИР", "научно-исследовательская"      | `research_reports`                   |
| "курсовая", "курсовой проект"          | `coursework`                         |
| "ВКР", "выпускная квалификационная"    | `graduation_qualification_work`      |
| "реферат", "контрольная", "эссе"       | `small_written_works`                |
| Unsure                                  | `common`                             |

Verify with `sfu-converter list-profiles --format json`.

### Step 3 — Write V2 TXT

Always start with `[DOC syntax=2 ...]`. Follow with `[META ...]` block. Then content.

#### Skeleton

```text
[DOC syntax=2 profile=<PROFILE> language=ru]
[META key=title value="<TITLE>"]
[META key=student value="<FIO>"]
[META key=group value="<GROUP>"]
[META key=supervisor value="<SUPERVISOR>"]
[META key=year value="2025"]
[META key=city value="Красноярск"]

[H level=1 title="Введение"]
[P] <Актуальность, цель, задачи.>

[H level=1 title="<Основная глава>"]
[H level=2 title="<Раздел>"]
[P] <Содержательный текст.>

[H level=1 title="Заключение"]
[P] <Итоги.>

[H level=1 title="Список использованных источников"]
[SOURCE number=1] <Фамилия И.О. Название. — Город: Издательство, Год.>
```

#### Hard rules

1. **Latin markers only.** `[H ...]` not `[Н ...]`, `[TABLE ...]` not `[ТABLE ...]`. Cyrillic lookalikes break parsing.
2. **Every body line wrapped in `[P]`.** Plain unmarked text emits warnings (errors in `--strict`).
3. **Always close blocks** — `[TABLE_END]`, `[LIST_END]`, `[FORMULA_END]`, `[RAW_END]`.
4. **Unique `id`s.** If two figures both use `id=fig:overview`, parser flags `TXT_DUPLICATE_ID`.
5. **Equal table cell count.** Every row needs the same number of `|`-delimited cells.
6. **Heading level 1–4 only.** Higher levels rejected.
7. **Structural sections recognized by title:** `Введение`, `Заключение`, `Содержание`, `Список использованных источников`, `Реферат`, `Аннотация`, `Список сокращений`, `Приложение`. Use these exact words for `[H level=1 title="..."]` to trigger correct formatting.

#### Inline formatting

```text
[P] Текст с **жирным** и *курсивом*.
```

#### Cross-references

Define id on figure/table/formula/appendix, then reference:

```text
[FIGURE src="arch.png" caption="Архитектура" id=fig:arch]
[P] См. рисунок [REF target=fig:arch].
```

#### Lists

```text
[LIST type=numbered]
[-] Первый шаг.
[-] Второй шаг.
[-] Третий шаг.
[LIST_END]
```

`type` ∈ {`bullet`, `numbered`, `lettered`} (aliases: `unordered`/`ul`, `ordered`/`ol`, `alpha`).

#### Formulas

```text
[FORMULA id=eq:rmse number=1]
RMSE = sqrt(sum((y_i - y_pred_i)^2) / n)
[FORMULA_END]
[FORMULA_EXPLANATION] где y_i — фактическое значение, y_pred_i — прогноз, n — размер выборки
```

#### Appendices

```text
[PAGE_BREAK]
[APPENDIX id=app:a title="Исходный код"]
[P] Листинг 1 — реализация модуля авторизации.
[RAW]
def authorize(user):
    return user.token is not None
[RAW_END]
```

Code or any literal `[...]` text must go in `[RAW]...[RAW_END]`.

### Step 4 — Lint

```bash
sfu-converter lint --input <file>.txt --syntax-version 2 --profile <PROFILE> --strict --format json
```

Read JSON `diagnostics`. Exit codes:

| Code | Meaning                          |
|------|----------------------------------|
| 0    | Clean                            |
| 1    | Warnings (only in `--strict`)    |
| 2    | Errors                           |

### Step 5 — Fix common diagnostics

| Code                         | Fix                                                       |
|------------------------------|-----------------------------------------------------------|
| `TXT_UNKNOWN_MARKER`         | Wrap line in `[P]` or correct marker spelling             |
| `TXT_CYRILLIC_IN_MARKER`     | Replace Cyrillic letter with Latin equivalent             |
| `TXT_MISSING_BLOCK_END`      | Add matching `[*_END]`                                    |
| `TXT_DUPLICATE_ID`           | Make ids unique (`fig:overview1`, `fig:overview2`)        |
| `TXT_INVALID_TABLE_SHAPE`    | Pad / trim row to match header cell count                 |
| `TXT_MALFORMED_ATTRIBUTE`    | Quote values with spaces, check `key=value` syntax        |
| `INVALID_HEADING_LEVEL`      | Use level 1–4 only                                        |
| `TXT_UNSUPPORTED_SYNTAX`     | Use `syntax=2` in `[DOC]`                                 |

### Step 6 — Convert

```bash
sfu-converter convert \
  --input <file>.txt \
  --output <file>.docx \
  --profile <PROFILE> \
  --syntax-version 2 \
  --strict \
  --validate-output \
  --format json
```

`--validate-output` runs the DOCX style validator after rendering. Combine with `--strict` to fail on warnings.

### Step 7 — Report results

Tell user:
- output DOCX path
- profile used
- diagnostics count (errors / warnings)
- any unresolved warnings

## Idiomatic skeletons

### Lab report

```text
[DOC syntax=2 profile=lab_practical_project_reports language=ru]
[META key=title value="Лабораторная работа №3: <TOPIC>"]
[META key=student value="<FIO>"]
[META key=group value="<GROUP>"]
[META key=supervisor value="<SUPERVISOR>"]
[META key=year value="2025"]

[H level=1 title="Цель работы"]
[P] <Цель.>

[H level=1 title="Теоретическая часть"]
[P] <Теория.>

[H level=1 title="Ход работы"]
[H level=2 title="Подготовка окружения"]
[P] <Шаги.>
[H level=2 title="Реализация"]
[P] <Описание.>

[H level=1 title="Результаты"]
[P] <Что получилось.>

[H level=1 title="Заключение"]
[P] <Выводы.>

[H level=1 title="Список использованных источников"]
[SOURCE number=1] <Источник.>
```

### Coursework

```text
[DOC syntax=2 profile=coursework language=ru]
[META key=title value="<ТЕМА>"]
[META key=student value="<FIO>"]
[META key=group value="<GROUP>"]
[META key=supervisor value="<SUPERVISOR>"]
[META key=year value="2025"]

[H level=1 title="Введение"]
[P] <Актуальность, цель, задачи, объект, предмет.>

[H level=1 title="Аналитическая часть"]
[H level=2 title="Обзор предметной области"]
[P] <Текст.>

[H level=1 title="Проектная часть"]
[H level=2 title="Архитектура решения"]
[FIGURE src="arch.png" caption="Архитектура системы" id=fig:arch]

[H level=1 title="Заключение"]
[P] <Итоги.>

[H level=1 title="Список использованных источников"]
[SOURCE number=1] <...>
```

## Anti-patterns

- `[H1] Заголовок` — V1 syntax. V2 uses `[H level=1 title="Заголовок"]`.
- `Просто текст без маркера.` — wrap in `[P]`.
- `[Н level=1 title="..."]` — Cyrillic `Н`. Use Latin `H`.
- Two figures with same `id`. Make unique.
- Code blocks pasted without `[RAW]`. Square brackets in code (`list[0]`) trigger marker parser.
- Inventing FIO, group, supervisor names. Ask user.

## CLI reference

```bash
sfu-converter list-profiles --format json
sfu-converter explain-syntax --syntax-version 2 --format json
sfu-converter parse --input file.txt --syntax-version 2 --format json
sfu-converter lint --input file.txt --syntax-version 2 --profile <P> --strict --format json
sfu-converter convert --input file.txt --output file.docx --profile <P> --syntax-version 2 --strict --validate-output --format json
sfu-converter validate-docx --input file.docx --profile <P> --format json
```

Always pass `--format json` for programmatic parsing of results in agent loops.
