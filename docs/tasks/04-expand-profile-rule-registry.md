# Task 04: Expand Profile-Specific Rule Registry to Cover Standard Sections

## Priority: High (data backbone for tasks 05–32)
## Phase: Phase 4 (Formatting registry)
## Standard reference
- PDF §6.1 (структура), §6.2 (титульный лист — Forms Б, В, Г, Д, Е, Ж, И, К, Л,
  М, Н, П), §7.1.3 (framed sheets for ДП/КП), §7.2 (page numbering, frame field
  7), §7.7 (tables — many rules), §7.8 (figures), §7.9–7.10 (bibliography), §7.11
  (appendices), §8 (graphic materials), §9 (project designations).
- Audit *Suggested implementation order* §1, §3, §4, §6, §7, §8, §9, §10, §12.

## Affected files
- `src/sfu_converter/registry/rules.py`
- `src/sfu_converter/registry/profiles.py`
- `src/sfu_converter/registry/loader.py`
- `docs/formatting requirements/common.md`
- `docs/formatting requirements/coursework.md`
- `docs/formatting requirements/graduation_qualification_work.md`
- `docs/formatting requirements/practice_reports.md`
- `docs/formatting requirements/research_reports.md`
- `docs/formatting requirements/lab_practical_project_reports.md`
- `docs/formatting requirements/small_written_works.md`
- `docs/formatting requirements/project_designations.md`
- `docs/formatting requirements/graphic_and_demonstration_materials.md`
- `tests/test_registry.py`
- `tests/test_quality_gates.py`

## Current state

`COMMON_RULES` covers 31 records (page setup, body text, headings H1-H3,
structural heading, list item, figure caption, formula, bibliography entry,
table caption, table body). Profile-specific tuples are short (1-3 records
each) and mark almost everything `not_supported`. Several standard sections
have **no** rule record at all.

## Implementation

For every gap listed below, add a `FormattingRule` record with explicit
`renderer_status` and `validator_status` set to `NOT_SUPPORTED` until the
corresponding feature task lands.

### `COMMON_RULES` — additions

| Rule ID | Section in PDF | Parameters |
|---|---|---|
| `common.page.margins.landscape` | §7.1.2 | `top_mm=30`, `bottom_mm=10`, `left_mm=20`, `right_mm=20` |
| `common.heading.h4` | §7.4 | mirrors H3 with indent 1.25 cm |
| `common.heading.no_hyphenation` | §7.5 | `allow_word_break=False` |
| `common.heading.two_sentence_separator` | §7.5 | `separator="."`, `enforce=True` |
| `common.heading.point_requires_subpoints` | §7.4 | `min_subpoints=2` |
| `common.list.lettered` | §7.4 | `excluded_letters="ёзйочьыъ"`, `format="а)"`, `indent_cm=1.25` |
| `common.list.nested_numeric` | §7.4 | `format="N)"`, `extra_indent_chars=2` |
| `common.list.marker_alphabetical` | §7.4 | enforce a) before б) before в)… |
| `common.formula.body_indent` | §7.6 | **fix: `indent_cm=1.25` (not 0)** |
| `common.formula.section_numbering` | §7.6 | `pattern="{section}.{n}"`, default off |
| `common.formula.appendix_numbering` | §7.6/§7.11 | `pattern="{letter}.{n}"` |
| `common.formula.line_continuation` | §7.6 | break on operation signs, repeat sign on next line |
| `common.formula.explanation_marker` | §7.6 | first explanation must start with `где`, no colon |
| `common.formula.repeated_symbol` | §7.6 | repeated symbol → "то же, что и в формуле (N)" |
| `common.formula.consecutive_comma` | §7.6 | comma between consecutive formulas |
| `common.formula.cross_reference` | §7.6 | `(N)` or `(N.M)` patterns |
| `common.table.borders` | §7.7 | `left=True`, `right=True`, `bottom=True`, `top=False`, `header_double=True` |
| `common.table.forbid_serial_column` | §7.7 | reject column whose header equals "Номер по порядку"/"№ п/п" |
| `common.table.section_numbering` | §7.7 | optional `Таблица {section}.{n}` |
| `common.table.appendix_numbering` | §7.7/§7.11 | `Таблица {letter}.{n}` |
| `common.table.subheader` | §7.7 | sub-header lower-case if forms one sentence with header, otherwise capital |
| `common.table.no_diagonal_split` | §7.7 | reject diagonal cells in header |
| `common.table.no_period_in_header` | §7.7 | header text must not end with period |
| `common.table.unit_label` | §7.7 | single label above table on right, 12 pt |
| `common.table.column_unit_suffix` | §7.7 | accept `, Гц` suffix in column header |
| `common.table.numbering_row_replacement` | §7.7 | continuation page replaces header with numbering row |
| `common.table.continuation_label` | §7.7 | `Продолжение таблицы N` / `Окончание таблицы N` |
| `common.table.footnote` | §7.7 | inside the table, above closing line, marker `*` or `1)` |
| `common.table.italic_letters` | §7.7 (ГОСТ 2.321) | letter designations italic |
| `common.figure.section_numbering` | §7.8 | `Рисунок {section}.{n}` |
| `common.figure.appendix_numbering` | §7.8/§7.11 | `Рисунок {letter}.{n}` |
| `common.figure.placement_after_reference` | §7.8 | place after first ref or on next page |
| `common.figure.explanatory_data` | §7.8 | above caption, 12 pt |
| `common.figure.multi_sheet_label` | §7.8 | "лист 1", "Рисунок N, лист 2" |
| `common.bibliography.gost_record` | §7.10 | record format from ГОСТ Р 7.0.100/7.80 |
| `common.bibliography.gost_abbreviations` | §7.10 | ГОСТ 7.11 / Р 7.0.12 abbreviations |
| `common.bibliography.grouping_method` | §7.10 | one of `alphabetical`, `systematic`, `chronological` |
| `common.bibliography.russian_first` | §7.10 | Russian entries before non-Russian |
| `common.reference.in_text_simple` | §7.9 | `[N]` |
| `common.reference.in_text_pages` | §7.9 | `[N, с. M]`, page ranges |
| `common.reference.in_text_volume` | §7.9 | `[N, т. T, с. M]` |
| `common.reference.in_text_group` | §7.9 | `[59; 67, с. 40-46; 82]` |
| `common.reference.footnote` | §7.9 | subscript marker, separator line, smaller font |
| `common.reference.cross_check` | §7.9 | each `[N]` matches a bibliography entry |
| `common.reference.figure_table_formula` | §7.6/7.7/7.8/7.11 | refs `(рисунок N)`, `(таблица N)`, `(N)`, `(приложение А)` |
| `common.appendix.auto_letter` | §7.11 | automatic Russian-letter assignment, skipping `Ё З Й О Ч Ь Ы Ъ` |
| `common.appendix.continuation_label` | §7.11 | `Продолжение приложения А` / `Окончание приложения А` |
| `common.appendix.section_numbering` | §7.11 | `А.1`, `А.1.1`, `А.1.1.1`, `А.1.1.1.1` |
| `common.appendix.in_text_reference` | §7.11 | "…в соответствии с приложением А" |
| `common.abbreviations.two_column_layout` | §6.9 | left = abbreviation alphabetical, right = expansion |
| `common.referat.template` | §6.3 | counts (страницы, рисунки, таблицы, формулы, приложения, источники), keywords ≤15, ≤1 page |
| `common.referat.keywords_uppercase` | §6.3 | comma-separated, nominative, uppercase |
| `common.style.abbreviation_introduction` | §7.3 | "…информационно-аналитический комплекс (ИАК)" |
| `common.style.no_abbreviations_in_headings` | §7.3 | reject abbreviations in heading text |
| `common.style.unit_consistency` | §7.3 (ГОСТ 8.417) | a single unit choice per quantity |

### Profile-specific additions

- `coursework.title_block.field_2_designation` — letter-numeric code in field 2
- `coursework.title_block.field_7_page_number` — page number in field 7 of frame
- `coursework.metadata.required_designation`
- `graduation_qualification_work.title_page.form_e` (Е — VKR continuation,
  консультанты, нормоконтролёр)
- `graduation_qualification_work.title_page.form_zh` (Ж — single-page combined)
- `graduation_qualification_work.referat.required` — Form П generator on
- `graduation_qualification_work.assignment.form_a` — Form А (assignment)
- `graduation_qualification_work.title_page.form_b.required_metadata` — extends with
  `direction_code`, `direction_name`, `master_program_code`, `master_program_name`,
  `reviewer`
- `graduation_qualification_work.title_page.form_v.required_metadata` — adds
  `specialty_code`, `subtitle="Пояснительная записка"`
- `graduation_qualification_work.title_page.form_g.required_metadata` — adds
  `reviewer`
- `practice_reports.title_page.form_k.headings` — 4 variants: учебная,
  производственная, преддипломная, технологическая
- `project_designations.code.dictionary` — full enum from Приложение Х:
  `ПЗ, РР, ПМ, И, Д, ВС, ВП, ТБ, ТУ, СБ, ВО, ТЧ, ГЧ, МЭ, МЧ, УЧ, МК, КТП, ОК,
  ВОБ, ВМ, С, ЛС, ТХ, ГП, ГТ, АР, АС, АИ, КЖ, КМ, КМД, КД, ВК, ОВ, ТМ, ГСВ, ГР,
  НВ, НК, ТС, АД, ТР` plus schema codes `Э / Г / П / К / В / Л / Р / Е / С` and
  type numbers `1-7` and `0`.
- `project_designations.code.format` — pattern
  `^[А-Я]{2,3}[-–—] ?\d{2}\.\d{2}\.\d{2}( ?\w+){0,3}( [А-Я]{1,3})?$`
- `project_designations.code.year_optional` — pattern allowing `–YYYY`
- `graphic_and_demonstration_materials.drawing.frame_form_5_or_6`
- `graphic_and_demonstration_materials.drawing.scale_set` — ГОСТ 2.302 list
- `graphic_and_demonstration_materials.drawing.font_set` — ГОСТ 2.304 list
- `graphic_and_demonstration_materials.poster.title_block_on_reverse`
- `graphic_and_demonstration_materials.slide.fill_density` — ≥ 70 %
- `graphic_and_demonstration_materials.slide.header_continuity`
- `graphic_and_demonstration_materials.slide.a4_print_out`
- `*.appendix.sheet_format` — accept А3, А3×4, А4×4, А2, А1.

### Profile composition adjustments

1. `coursework` source docs already include `project_designations.md` and
   `graphic_and_demonstration_materials.md`; verify the rule tuple actually
   pulls in `PROJECT_DESIGNATION_RULES` and the new
   `coursework.title_block.*` rules.
2. `graduation_qualification_work` must include
   `GRAPHIC_AND_DEMONSTRATION_MATERIAL_RULES`,
   `PROJECT_DESIGNATION_RULES`, and the assignment Form А rule.
3. Every profile must include `common.reference.*` and the new style rules.

## Tests

- `len(get_profile("common").rules) >= 31 + count(new_common_rules)`.
- Every new rule ID is unique across `ALL_RULES`.
- Every `source_doc` path resolves to a file under
  `docs/formatting requirements/`.
- Every `source_section` slug matches a heading present in the referenced
  document (asserted by parsing markdown headers — Task 32 enforces this in
  CI).
- `coursework` profile contains
  `coursework.frame.course_project_explanatory_note`,
  `coursework.title_block.field_2_designation`,
  `project_designations.code.format`.
- `graduation_qualification_work` profile contains every Form Б/В/Г/Д/Е/Ж
  title-page rule.

## Verification

```bash
python -m pytest tests/test_registry.py tests/test_quality_gates.py
python -m sfu_converter list-profiles --format json | python -m json.tool
```

## Notes / dependencies

- Status fields stay `NOT_SUPPORTED` for now. Each downstream task flips a
  specific subset of statuses to `IMPLEMENTED` once the feature lands.
- This expansion drives the unsupported-rule diagnostics from Task 03 and the
  coverage matrix from Task 32; together they make every gap auditable.
