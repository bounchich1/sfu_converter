# СТУ 7.5–07–2021: PDF vs converter implementation

Walk-through of `docs/sfu-stu-7.5-07.pdf` (61 pages) cross-referenced with the
current state of `src/sfu_converter/`. Each section follows the standard's own
numbering. Status is one of:

- **DONE** — implemented and matches the standard.
- **PARTIAL** — implemented but only a subset of the standard's text.
- **MISSING** — not implemented in renderer, validator, or both.

Verified against:

- `src/sfu_converter/registry/rules.py` (60 rule records)
- `src/sfu_converter/registry/profiles.py` (9 profiles)
- `src/sfu_converter/parser/{v1_parser.py, v2_parser.py, syntax_spec.py}`
- `src/sfu_converter/infrastructure/{docx_renderer.py, docx_validator.py}`
- `src/sfu_converter/converter.py`, `src/sfu_converter/cli.py`

---

## 1 Область применения (p. 4)

The standard applies to ВКР, КП/КР, контрольные, РГЗ/РГР, отчёты по практикам,
лабораторным, НИР, отчёты о выполнении проектов, рефераты, эссе.

| Item | Status | Notes |
|------|--------|-------|
| Document scope (paper + EIOS) | n/a | Out of scope for a TXT→DOCX renderer; no validation that a generated document belongs to one of the listed types. |
| Profile per document type | PARTIAL | 9 profiles defined; profile is **not wired** through `TextToDocxConverter.convert_file()` and `StyleValidator` (see `converter.py:108` — always `get_profile("common")`). |

---

## 2 Нормативные ссылки (p. 5–6)

The standard pulls in 17 GOST/SP/STU references (ЕСКД 2.102, 2.104, 2.201, 2.301,
2.302, 2.304, 2.316, 2.321, 2.501, 2.701; ГОСТ 3.1102; 7.11; 7.80; 8.417; 34.201;
ГОСТ Р 2.105, 7.0.5, 7.0.12, 7.0.100, 21.101; СТУ 7.5–10; Р 50–77–88).

| Referenced norm | Used in standard | Status |
|---|---|---|
| ГОСТ 2.104 / ГОСТ Р 21.101 | Frame + main inscription (Form 1–6) | MISSING |
| ГОСТ 2.201 / 34.201 / Р 21.101 | Letter-numeric project designation | MISSING |
| ГОСТ 2.301 | Sheet formats (А1, А2, А3, А3×4, А4×4) | MISSING |
| ГОСТ 2.302 | Drawing scales | MISSING |
| ГОСТ 2.304 | Drawing fonts | MISSING |
| ГОСТ 2.321 | Italic letter designations in tables | MISSING |
| ГОСТ 2.501 | Folding sequence (Приложение Ф) | MISSING |
| ГОСТ 7.11 / 7.0.12 | Bibliographic abbreviations | MISSING |
| ГОСТ 7.80 / Р 7.0.100 | Bibliographic record format | MISSING |
| ГОСТ Р 7.0.5 | Bibliographic references | MISSING |
| ГОСТ 8.417 | Physical-quantity units | MISSING |

The validator emits no diagnostics tied to any of these GOSTs.

---

## 3 Термины и определения (p. 6–8) and 4 Сокращения (p. 8)

Definitions for ВКР, БР, ДП, ДР, КП, КР, МД, ПЭВМ, РГЗ, РГР, "графический
материал", "демонстрационный материал", "иллюстрация", "пояснительная записка",
"реферат ВКР", "таблица", "формула", etc.

| Item | Status | Notes |
|---|---|---|
| Profile names map to terms (МД, ДП, ДР, БР…) | PARTIAL | Profiles `graduation_qualification_work`, `coursework`, `practice_reports`, `research_reports`, `lab_practical_project_reports`, `small_written_works`, `graphic_and_demonstration_materials`, `project_designations` exist; `magisters_dissertation` is folded into `graduation_qualification_work`. |
| Auto-generated «СПИСОК СОКРАЩЕНИЙ» from the abbreviations used in the text | MISSING | Renderer accepts the structural section heading but does not collect or format two columns. |

---

## 5 Общие положения (p. 9)

| Rule (5.x) | Status | Notes |
|---|---|---|
| 5.1 Document classification (text vs graphic) | n/a | Renderer is text-only. |
| 5.6 Form А (задание ВКР) inserted after title page, **excluded from page count** | MISSING | Form А not implemented. No support for "skip pages from numbering". |
| 5.7 Норма-контроль via СТУ 7.5–10 | MISSING | No norm-control workflow. |
| 5.8 Folding to А4 (Приложение Ф) | MISSING | n/a for DOCX output. |

---

## 6 Требования к построению текстового документа (p. 9–13)

### 6.1 Структура текстового документа

Required (or conditional) elements: титульный лист, реферат, содержание,
введение, основная часть, аключение, список сокращений, список использованных
источников, приложения. МД may add АННОТАЦИЯ, АВТОРЕФЕРАТ. **Title page** and
**основная часть** are mandatory; the rest depend on document type.

| Item | Status | Notes |
|---|---|---|
| Recognise structural headings РЕФЕРАТ, АННОТАЦИЯ, СОДЕРЖАНИЕ, ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ, СПИСОК СОКРАЩЕНИЙ, СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ, ПРИЛОЖЕНИЕ | DONE | `parser/v1_parser.py`, mapped via `STRUCTURAL_TYPES`. |
| Each structural element starts on a new page | DONE | Renderer inserts `add_page_break()`. |
| Centred, bold, uppercase, no period, no number | DONE | `common.structural.heading` rule. |
| One blank line after the heading | DONE | `_add_empty_paragraph("empty_after_header")`. |
| Enforce title page and "main part" presence | MISSING | No structural validator. |
| Enforce per-profile required sections | PARTIAL | Rule records list required sections, but they are not validated (`*.structure.required_sections` rules are not exercised). |
| Order check: e.g. СПИСОК СОКРАЩЕНИЙ before СПИСОК ИСТОЧНИКОВ | MISSING | No order validator. |

### 6.2 Титульный лист (forms Б, В, Г, Д, Е, Ж, И, К, Л, М, Н)

This is the largest implementation gap.

| Form | Standard requirement | Status |
|---|---|---|
| Generic title page from metadata | renderer-defined fallback | DONE — `_render_title_page()`, ~70 lines, prints ministry, university, institute, department, subject, title, supervisor, student, city, year. |
| Б — МД | Magisterial dissertation; "МАГИСТЕРСКАЯ ДИССЕРТАЦИЯ", code+name направления, code+name магистерской программы, рецензент | MISSING — rule `graduation_qualification_work.title_page.form_b` exists but no renderer branch. |
| В — ДП | "ДИПЛОМНЫЙ ПРОЕКТ", код специальности, "Пояснительная записка" subtitle | MISSING |
| Г — ДР | "ДИПЛОМНАЯ РАБОТА", рецензент | MISSING |
| Д — БР | "БАКАЛАВРСКАЯ РАБОТА" | MISSING |
| Е — VKR continuation | Консультанты по разделам, нормоконтролёр | MISSING |
| Ж — single-page VKR with рецензент + консультанты + нормоконтролёр | combined version | MISSING |
| И — КП/КР | "КУРСОВОЙ ПРОЕКТ" or "КУРСОВАЯ РАБОТА", student group | MISSING — rule `coursework.title_page.form_i` exists, no renderer. |
| К — отчёт о практике | one of four practice headings, "место прохождения практики", руководитель от университета + от предприятия | MISSING |
| Л — отчёт о НИР | "ОТЧЁТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ", руководитель магистерской программы | MISSING |
| М — лабораторная/практическая/проект | "ОТЧЁТ ПО ЛАБОРАТОРНОЙ РАБОТЕ" / "ОТЧЁТ О ПРАКТИЧЕСКОЙ РАБОТЕ" / "ОТЧЁТ О ВЫПОЛНЕНИИ ПРОЕКТА", "Преподаватель", "Студент <группа, зачётной книжки>" | MISSING |
| Н — реферат/РГЗ/РГ/контрольная/эссе | "по <дисциплина>", "тема (вариант)", "Преподаватель", "Студент …" | MISSING |
| 6.2.2 Required fields validation per form | MISSING | `*.metadata.required` rules exist, never validated. |

The `_render_title_page(metadata, profile_name)` signature already accepts a
profile name; the renderer just ignores it.

### 6.3 Реферат ВКР

Standard: тема, страницы, рисунки, таблицы, формулы, приложения, источники,
графический материал, ≤15 keywords (uppercase, comma-separated, nominative
case), цели/задачи/актуальность/новизна/выводы, ≤1 page.

| Item | Status |
|---|---|
| Template / generator for `[REFERAT]` block with auto-counts | MISSING |
| Form П example | MISSING |
| Validator for keyword count and uppercase | MISSING |
| Word-count / page-count check (≤1 page) | MISSING |

### 6.4 Содержание

| Item | Status | Notes |
|---|---|---|
| Insert Word TOC field | DONE | `_render_table_of_contents()`. |
| Heading styles attached so Word can populate TOC | DONE | `_apply_word_heading_style`. |
| 24-page-rule (omit TOC for short documents) | MISSING | No length check. |
| Structural-element entries with `Содержание` heading bold uppercase | DONE | Title is "СОДЕРЖАНИЕ". |
| Subsection indent ≈ 2 chars from section, point indent ≈ 2 chars from subsection | MISSING | Delegated entirely to Word's TOC field. |
| Continuation indent (заголовок переноса на 2-ю строку) | MISSING |
| `Приложения А–Т ……58–74` grouped form | MISSING |
| Verify that TOC entries match actual headings | MISSING |
| Form Т (КР contents example) generator | MISSING |

### 6.5 Введение / 6.6 Основная часть / 6.7 Заключние / 6.8 Список сокращений / 6.9 Список использованных источников / 6.10 Приложения

| Item | Status |
|---|---|
| Headings recognised as structural sections | DONE |
| Two-column abbreviations list (left = abbreviation alphabetical, right = expansion) | MISSING |
| Required-content checklist per element | MISSING |

---

## 7 Требования к оформлению и изложению (p. 14–28)

### 7.1 Общие требования

| Rule | Status | Notes |
|---|---|---|
| 7.1.1 А4, Times New Roman 14, line spacing 1.0 or 1.5 | DONE | `common.text.font.*`, `common.text.line_spacing` (default 1.5). |
| Paragraph indent 12.5 mm | DONE | `common.text.indent.first_line` = 1.25 cm. |
| Justify text | DONE | `common.text.alignment` |
| Hand-written allowance (height 2.5 mm, line spacing 8–10 mm) | n/a | Out of scope. |
| 7.1.2 Margins **portrait** L 30 / T 20 / B 20 / R 10 mm | DONE | `common.page.margins.portrait`, validated. |
| 7.1.2 Margins **landscape** L 20 / R 20 / T 30 / B 10 mm | MISSING | No landscape rule, no orientation switching. |
| 7.1.3 ДП/КП on **framed sheets** with main inscription (forms 1–4) — text-to-frame margin 5 mm horizontal, 15 mm vertical | MISSING | `coursework.frame.course_project_explanatory_note`, `project_designations.explanatory_note.frame` exist as registry stubs only. |

### 7.2 Нумерация страниц

| Rule | Status | Notes |
|---|---|---|
| Sequential Arabic numerals | DONE |
| Bottom-centre, no first-line indent, TNR 14 | DONE | Renderer footer; **validator skips** (`common.page.numbering` validator_status = not_supported). |
| Page number in graph 7 of frame for ДП/КП | MISSING |
| Title page included in count, not printed | PARTIAL | First-page footer is blank, but no formal "page 1 hidden" check; pages of Form А (задание ВКР) excluded from numbering — MISSING. |

### 7.3 Изложение текста

Style requirements (clarity, terminology, abbreviation expansion at first use,
ГОСТ 8.417 units). All renderer + validator MISSING; this is a stylistic
checker, far beyond the current converter.

| Item | Status |
|---|---|
| Recognise abbreviation introduction `… информационно-аналитический комплекс (ИАК)` | MISSING |
| Forbid abbreviations in headings, captions of figures/tables | MISSING |
| Unit-consistency check across the document | MISSING |

### 7.4 Деление текста

| Rule | Status | Notes |
|---|---|---|
| Sections numbered 1, 2, 3 within main part | DONE | H1 auto-numbering. |
| Subsections 1.1, 1.2 | DONE | H2. |
| Points 1.1.1 | DONE | H3. |
| **Subpoints 1.1.1.1** | MISSING | No H4 in parser/renderer. |
| Auto-renumber after edits | DONE | counter-based at render time. |
| Перечисления (lists): dash | DONE | `common.list.item`. |
| Lettered list а), б), …, excluding ё з й о ч ь ы ъ | DONE | enforced in `format_list_marker`. |
| Nested numeric 1), 2), shifted +2 chars from lettered level | PARTIAL | nesting recognised in renderer but parser does **not preserve nested structure**; validator does not check indentation. |
| Validate that lettered markers stay alphabetical and skip the disallowed letters | MISSING |

### 7.5 Заголовки

| Rule | Status | Notes |
|---|---|---|
| Headings present for sections / subsections | DONE | parser-driven. |
| Point heading only when subsection has ≥2 points split into subpoints | MISSING | No structural check. |
| Capital first letter, bold, no period, no underline | DONE | `common.heading.h1/h2/h3` + `common.heading.no_period`. |
| Two-sentence heading separated by period | MISSING | No detection of multi-sentence headings. |
| No word hyphenation in headings | MISSING | Validator does not check. |
| Heading separated from text by one blank line | PARTIAL | Renderer adds spacing; validator marked not_supported (`common.heading.spacing_*`). |

### 7.6 Формулы

| Rule | Status | Notes |
|---|---|---|
| Formula on its own line, paragraph indent | PARTIAL | `common.formula.body` uses indent 0 cm; the standard says "с абзацного отступа" (12.5 mm). **Bug candidate**. |
| One blank line above and below | DONE | renderer; validator skips. |
| Continue formulas on operation signs, repeat sign on next line | MISSING | No line-break logic. |
| Continuous numbering in parens, right-aligned | DONE | Tab-stop based. |
| Section-based numbering (1.1) | MISSING | Counter is global. |
| Appendix numbering (А.1) | MISSING |
| Inline formulas in tables / illustration explanatory data must be unnumbered | MISSING | No "inline formula" concept. |
| Explanation paragraph: "где" without colon, no first-line indent, one symbol per line | PARTIAL | `common.formula.explanation` enforces no indent; text "где" is not enforced; multi-line splitting is up to the author. |
| Repeated symbol explained once ("L_сл — то же, что и в формуле (1)") | MISSING |
| Consecutive formulas separated by comma | MISSING |
| Cross-reference `(2)` to formula 2 | MISSING |
| Hand-written formula allowance | n/a |

### 7.7 Таблицы

The standard is detailed; many sub-rules.

| Rule | Status | Notes |
|---|---|---|
| Place table after first reference or on next page | MISSING | No reference tracking. |
| Allow landscape (альбомная) table | MISSING |
| Caption "Таблица N – Name" left-aligned, no indent, no period at end, 14 pt | DONE | `_format_table_caption` outputs `Таблица N — Name`. |
| Borders left, right, bottom (no top border on the body) | PARTIAL | Renderer uses default `Table Grid`; not the standard's "side+bottom only with double line under головка". |
| Double line between головка and body | MISSING |
| Forbid "Номер по порядку" column | MISSING | No column inspection. |
| Continuous numbering, allow section-based (Таблица 7.1) | PARTIAL | Continuous only. |
| Appendix numbering Таблица А.1 | MISSING |
| Reference checking: every table referenced in text | MISSING |
| Bold + centred header, lower-case sub-header if it forms one sentence with header, otherwise capital | PARTIAL | bold + centre done; sub-header rule MISSING. |
| Forbid diagonal split in headers | MISSING |
| No period at the end of header / sub-header text | MISSING |
| Single physical-unit label on the right above the table, 12 pt | MISSING |
| Per-column unit suffix `, Hz` form | MISSING |
| Numbering row replacement on continuation pages | MISSING |
| "Продолжение таблицы N" / "Окончание таблицы N" on continuations | MISSING |
| Header repeats on continuation page | DONE | `tblHeader` element. |
| Table footnote inside the table, above closing line, marker `*` or `1)` | MISSING |
| Italic letter designations from ГОСТ 2.321 | MISSING |
| Body 10–12 pt | DONE | `common.table.font.size` 12 pt. |
| Cell padding 6 pt | DONE | `common.table.cell_padding` (validator MISSING). |

### 7.8 Иллюстрации

| Rule | Status | Notes |
|---|---|---|
| Place after first reference or on next page | MISSING |
| Centred, with blank line above and below | DONE | `common.figure.spacing_*` applied; validator MISSING. |
| Single figure → "Рисунок 1" | DONE |
| Caption format "Рисунок N – Name" centred, 14 pt | DONE | `_format_figure_caption`, separator `—`. |
| Section-based numbering | MISSING |
| Appendix numbering "Рисунок А.1" | MISSING |
| Reference checking | MISSING |
| Explanatory data above the caption, 12 pt | MISSING |
| Multi-page figures: "лист 1", "Рисунок 1, лист 2", "Рисунок 1, лист 3" | MISSING |
| Image readability check, diagram-type appropriateness | MISSING |
| ESKD/SPDS drawings | MISSING |
| Image width ≤ 15 cm | DONE | `common.figure.image` (max width). |

### 7.9 Библиографические ссылки

| Rule | Status | Notes |
|---|---|---|
| In-text reference `(Андреевич В.К. … М., 1887. С. 61–62)` | MISSING |
| Footnote reference (subscript `1`, separator line, smaller font) | MISSING |
| List reference `[13]` | PARTIAL — parser leaves `[13]` as plain text; no validation. |
| Page-fragment ref `[20, с. 29]` | MISSING |
| Multi-volume ref `[18, т. 1, с. 75]` | MISSING |
| Group of refs `[59; 67, с. 40-46; 82]` | MISSING |
| Build by ГОСТ Р 7.0.5 | MISSING |
| Cross-check that every `[N]` matches an entry in СПИСОК ИСТОЧНИКОВ | MISSING |

### 7.10 Список использованных источников

| Rule | Status | Notes |
|---|---|---|
| Place sources before приложения | MISSING | No order check. |
| Numbered, paragraph indent | DONE | `common.bibliography.entry`. |
| ГОСТ Р 7.0.100 / 7.80 record format | MISSING |
| ГОСТ 7.11 / Р 7.0.12 abbreviations | MISSING |
| Grouping methods (alphabetical / systematic / chronological) — pick one | MISSING |
| Forbid mixing methods | MISSING |
| Russian first, then non-Russian alphabetical run | MISSING |
| Form У example library (templates per record type: норматив, патент, книга 1/2/3/4 авторов, том, диссертация, эл. ресурс, статья) | MISSING — only free-text entries. |
| V2 `[SOURCE number=N]` syntax | DONE | parser support. |

### 7.11 Оформление приложений

| Rule | Status | Notes |
|---|---|---|
| Position at end of document | DONE (de facto) | renderer keeps order; not validated. |
| Designate with Russian capital, skip Ё З Й О Ч Ь Ы Ъ | DONE | parser/renderer enforces in `appendix.letter` and `format_appendix_letter`. |
| Auto-letter assignment | MISSING — explicit letter required. |
| Heading bold, centred, optional title, separated by one blank line | DONE | `_render_appendix`. |
| New page per appendix | DONE |
| Sheet formats А3, А3×4, А4×4, А2, А1 | MISSING |
| Section/subsection inside appendix numbered А.1, А.1.1, А.1.1.1, А.1.1.1.1 | MISSING |
| Appendix-prefixed Таблица А.1, Рисунок А.1, формула (А.1) | MISSING |
| Continuation labels "Продолжение приложения А", "Окончание приложения А" | MISSING |
| Independent-document appendix (own title page, page numbers continued) | MISSING |
| In-text references "…в соответствии с приложением А" | MISSING |
| V2 parser preserves `letter`/`type` attributes on `AppendixNode` | MISSING |

---

## 8 Требования к оформлению графических и демонстрационных материалов (p. 28)

| Rule | Status |
|---|---|
| Drawings (чертежи / схемы) on framed sheets per ГОСТ 2.301 + main inscription forms 5/6 | MISSING |
| ЕСКД / СПДС / ЕСТД / ЕСПД / Горная-документация compliance | MISSING |
| Scales per ГОСТ 2.302 | MISSING |
| Drawing fonts per ГОСТ 2.304 | MISSING |
| Abbreviations per ГОСТ 2.316 / Р 21.101 | MISSING |
| Posters: А1, ≥70 % fill, large title, main inscription on reverse | MISSING — `graphic_and_demonstration_materials.poster.fill_density` rule is a stub. |
| Slides: required first-slide fields (university, institute, theme, FIO, city, year), ≥70 % fill, header continuity, A4 print-out | MISSING |

The converter is text-only and does not target this section.

---

## 9 Требования к обозначению проектов (p. 29–30)

| Rule | Status |
|---|---|
| Letter-numeric code `ДП–23.05.02 ХХХХХХ.ХХХ СБ` (ГОСТ 2.201) | MISSING |
| Variant `ДП–08.05.01 ПЗ` (ГОСТ Р 21.101) | MISSING |
| Optional year insertion `ДП–23.05.02–2021 …` | MISSING |
| Place code in box 2 of every sheet's main inscription | MISSING |
| Document-code dictionary (Приложение Х): ПЗ, РР, ПМ, И, Д, ВС, ВП, ТБ, ТУ, СБ, ВО, ТЧ, ГЧ, МЭ, МЧ, УЧ, МК, КТП, ОК, ВОБ, ВМ, С, ЛС, ТХ, ГП, ГТ, АР, АС, АИ, КЖ, КМ, КМД, КД, ВК, ОВ, ТМ, ГСВ, ГР, НВ, НК, ТС, АД, ТР; schema codes Э/Г/П/К/В/Л/Р/Е/С + types 1–7/0 | MISSING — no enum, no validator. |

---

## Приложения А–Х: per-form gaps

| Приложение | Content | Implementation |
|---|---|---|
| А (рекомендуемое) | Form задания на ВКР (2 pages) | MISSING |
| Б (обязательное) | Form МД title page | MISSING |
| В | Form ДП title page | MISSING |
| Г | Form ДР title page | MISSING |
| Д | Form БР title page | MISSING |
| Е | Continuation page (консультанты, нормоконтролёр) | MISSING |
| Ж | Single-page VKR title with рец. + конс. + норма | MISSING |
| И | Form КП/КР | MISSING |
| К | Form отчёта о практике (4 variants) | MISSING |
| Л | Form отчёта о НИР магистранта | MISSING |
| М | Form отчёта по лаб./практ./проекту | MISSING |
| Н | Form реферата / РГЗ / РЗ / контр. / эссе | MISSING |
| П (рекомендуемое) | Example реферата ВКР (template) | MISSING |
| Р (обязательное) | Form листа ПЗ ДП/КП (рамка) | MISSING |
| С (обязательное) | Основные надписи forms 1–6 with graphs 1–17 | MISSING |
| Т (обязательное) | Example СОДЕРЖАНИЕ КР | MISSING |
| У (рекомендуемое) | Bibliographic record templates per resource type | MISSING — list exists in docs only. |
| Ф (обязательное) | Folding scheme А1/А2/А3 | n/a |
| Х (справочное) | Document-code dictionary | MISSING |

---

## CLI and orchestration gaps

| Capability | Status | Notes |
|---|---|---|
| `convert` command | DONE |
| `validate-docx` | DONE — common profile only |
| `parse` | STUB — returns *Not yet implemented* |
| `lint` | STUB |
| `list-profiles` | STUB |
| `export-schema` | STUB |
| `explain-syntax` | DONE |
| `--profile` plumbed into conversion | MISSING — `converter.py:108` always selects `common`. |
| `--profile` plumbed into validation | MISSING — `StyleValidator` always uses `common`. |
| Structured `not_supported` diagnostics emitted during conversion when a profile uses a not-yet-implemented family | MISSING |

---

## Validator coverage at a glance

Of the 31 common rules, **13 have `validator_status=implemented`** and **18 are
`not_supported`**. The 18 unsupported families:

`common.page.numbering`, `common.heading.spacing_before`,
`common.heading.spacing_after`, `common.list.item` *(only paragraph spacing
checked)*, `common.figure.caption` *(only alignment)*, `common.figure.spacing_before/after`,
`common.figure.image`, `common.formula.body` *(only paragraph alignment)*,
`common.formula.explanation`, `common.formula.spacing_before/after`,
`common.bibliography.entry`, `common.table.caption` *(only alignment)*,
`common.table.spacing_before/after`, `common.table.body`, `common.table.cell_padding`.

In addition, the validator treats every paragraph as *normal body text*:
generated figure captions, missing-image placeholders, and bibliography entries
get checked against `common.text.indent.first_line` and fail because they
deliberately do not have a first-line indent. Paragraph-role classification is
the prerequisite fix for almost every rule listed above.

---

## Suggested implementation order (engineering view)

1. **Wire `--profile` end-to-end** through `TextToDocxConverter.convert_file()`
   and `StyleValidator`. Without it, every profile-specific rule below is
   dead code.
2. **Paragraph-role classification** in the validator. Until figure captions,
   bibliography entries, formula bodies, table captions etc. are tagged, no
   fine-grained rule can be checked without false positives.
3. **Title-page form generators** (Б, В, Г, Д, Е, Ж, И, К, Л, М, Н, П) — bulk
   work, but each generator is mostly a layout template + metadata schema. Pair
   each form with its `*.metadata.required` validator.
4. **Section-based and appendix-based numbering** for headings, формулы,
   таблицы, рисунки. Single counter context plus `Section.appendix_letter`
   gives `1.1`, `А.1`, `(А.1)`, `Таблица А.1`, `Рисунок А.1`.
5. **Fourth-level heading (1.1.1.1)** in parser, AST and renderer.
6. **Reference graph** `[N]`, `(рисунок N)`, `(таблица N)`, `(формула (N))`,
   `(приложение Х)` — needed by both linter and validator. Drives "every
   table/figure must be referenced" and "appendix-X exists" checks.
7. **Frame + main inscription (Form Р + Forms 1–6 of Прил. С)** for ДП/КП. Big
   feature: landscape + portrait, repeated header, page number in graph 7.
8. **Graphic / demonstration materials** track (Section 8, А1 posters and
   slides, frames forms 5/6) — likely a separate output backend.
9. **Project designations** (Section 9 + Приложение Х code dictionary).
10. **Bibliography templates** for ГОСТ Р 7.0.100/7.80 plus Приложение У
    record-type generators. Followed by validator for grouping consistency.
11. **Reference parser** for `[20, с. 29]`, `[18, т. 1, с. 75]`, `[59; 67;
    82]`, internal-text refs, footnote refs.
12. **Special structural blocks**: `СПИСОК СОКРАЩЕНИЙ` two-column generator;
    `[REFERAT]` template with auto-counts; Form А (assignment) generator with
    page-numbering exclusion.
