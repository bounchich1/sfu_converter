# Task 10: Implement Profile-Specific Title Page Forms (Б, В, Г, Д, Е, Ж, И, К, Л, М, Н)

## Priority: Critical (largest single gap in §6.2)
## Phase: Phase 5 (Renderer)
## Standard reference
- PDF §6.2.1–§6.2.2 (p. 9–11) and Приложения Б, В, Г, Д, Е, Ж, И, К, Л, М, Н
  (p. 38–53). Each form prescribes the exact list of metadata fields, their
  layout and the required strings such as `МАГИСТЕРСКАЯ ДИССЕРТАЦИЯ`,
  `ДИПЛОМНЫЙ ПРОЕКТ`, `Пояснительная записка`, `КУРСОВОЙ ПРОЕКТ`,
  `КУРСОВАЯ РАБОТА`, `ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ`,
  `ОТЧЕТ О ПРАКТИЧЕСКОЙ РАБОТЕ`, `ОТЧЕТ О ВЫПОЛНЕНИИ ПРОЕКТА`,
  `ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ`, `РЕФЕРАТ`, `КОНТРОЛЬНАЯ РАБОТА`,
  `РАСЧЁТНО-ГРАФИЧЕСКАЯ РАБОТА`, `ЭССЕ`.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/title_pages/__init__.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_b.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_v.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_g.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_d.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_e.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_zh.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_i.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_k.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_l.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_m.py` *(new)*
- `src/sfu_converter/infrastructure/title_pages/form_n.py` *(new)*
- `src/sfu_converter/registry/rules.py` (status flips)
- `tests/test_title_page.py`
- `tests/fixtures/title_pages/*.json` *(new metadata fixtures)*

## Current state

`_render_title_page(metadata, profile_name)` in `docx_renderer.py` writes a
generic ministry/university/institute/department/subject/title/supervisor/
student/city/year layout. The argument `profile_name` is ignored — every
profile gets the same page. None of the appendix forms is implemented.

## Implementation

1. Move the generic layout into `title_pages/generic.py` so the registry can
   keep a fallback for the `common` profile.
2. Add a dispatcher
   `select_title_page_form(profile, metadata, *, override=None) ->
   TitlePageForm` that consults the profile's `*.title_page.form_*` rule and
   any `TitlePageNode.profile` override. The override is honoured only when
   the named form exists; otherwise emit `TXT_TITLE_FORM_NOT_FOUND`.
3. Implement one module per form. Each module exposes:

   ```python
   FORM_ID: str = "form_b"
   DEFAULT_DOCUMENT_TYPE: str = "МАГИСТЕРСКАЯ ДИССЕРТАЦИЯ"
   REQUIRED_METADATA: tuple[str, ...] = ("title", "student", "supervisor",
                                         "direction_code", "direction_name",
                                         "master_program_code",
                                         "master_program_name", "reviewer")
   OPTIONAL_METADATA: tuple[str, ...] = (...)
   def render(document, metadata, *, layout: TitlePageLayout) -> None: ...
   ```

   Each `render(...)` writes paragraphs in the order shown in the appendix
   form, using the existing typographic helpers for centered/right-aligned
   blocks.

4. Form layouts in detail (each renders on a single A4 portrait page; first
   page is excluded from page numbering — see Task 11):
   - **Б — МД**: МИНОБРНАУКИ → СФУ → институт → кафедра →
     `УТВЕРЖДАЮ Заведующий кафедрой ____________ ФИО / «___» _____ 20__ г.`
     → `МАГИСТЕРСКАЯ ДИССЕРТАЦИЯ` → name → `по направлению ХХ.ХХ.ХХ Название` →
     `по магистерской программе ХХ.ХХ.ХХ-ХХ Название` → научный руководитель →
     рецензент → выпускник → город, год.
   - **В — ДП**: same banner → `ДИПЛОМНЫЙ ПРОЕКТ` → optional subtitle
     `Пояснительная записка` → name → код+name специальности → руководитель →
     консультанты (по разделам) → нормоконтролёр → дипломник.
   - **Г — ДР**: like Б but `ДИПЛОМНАЯ РАБОТА`, with рецензент.
   - **Д — БР**: `БАКАЛАВРСКАЯ РАБОТА`, no рецензент by default.
   - **Е — VKR continuation**: second page of Б/В/Г/Д for additional
     консультанты по разделам and нормоконтролёр signatures.
   - **Ж — combined VKR**: single page version including рецензент,
     консультантов и нормоконтролёра.
   - **И — КП/КР**: subtype banner `КУРСОВОЙ ПРОЕКТ` или `КУРСОВАЯ РАБОТА` based
     on metadata. Includes group + zachetnaya knizhka.
   - **К — отчёт о практике**: top label is one of
     `ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ ПРАКТИКЕ`,
     `ОТЧЕТ О НАУЧНО-ПЕДАГОГИЧЕСКОЙ ПРАКТИКЕ`,
     `ОТЧЕТ О ПРОИЗВОДСТВЕННОЙ ПРАКТИКЕ`,
     `ОТЧЕТ О ПРЕДДИПЛОМНОЙ ПРАКТИКЕ` driven by `metadata.practice_kind`.
     Includes `Место прохождения практики`, university supervisor, enterprise
     supervisor.
   - **Л — отчёт о НИР магистранта**: includes magister program head
     approval block.
   - **М — отчёт по лаб./практ./проекту**: lab number / topic, дисциплина,
     преподаватель, студент группа № зачётной книжки.
   - **Н — РЕФЕРАТ / КОНТРОЛЬНАЯ / РГЗ / РГР / ЭССЕ**: `по дисциплине`,
     `тема (вариант)`, преподаватель, студент.
5. Each form validates required metadata and emits
   `TXT_MISSING_METADATA` with `data.missing` list when any required field
   is absent. Optional fields render only when present.
6. Set `renderer_status=IMPLEMENTED` on the `*.title_page.form_*` rules
   listed in Task 04 and the metadata-required rule for the profile.
7. Update `cmd_list_profiles` output to expose `titlePageForm` for every
   profile.

## Tests

For each of the 11 forms:

- Render with full metadata; assert that the produced first page contains
  every required string (banners, codes, supervisor headings) at the
  expected paragraph index using a golden text dump.
- Render with one required field missing; assert that the diagnostic list
  contains exactly one `TXT_MISSING_METADATA` referencing the field, and
  the page still renders (warning, not blocking).
- `TitlePageNode(profile="form_i")` inside a `lab_practical_project_reports`
  document overrides the form when permitted, fallbacks otherwise.
- `select_title_page_form(...)` returns the generic form for the `common`
  profile.
- The first page is excluded from page numbering (asserted via the section
  footer XML — `different_first_page=True`).

## Verification

```bash
python -m pytest tests/test_title_page.py
python -m sfu_converter convert --profile graduation_qualification_work --input examples/vkr.txt --output build/vkr.docx
```

Manual QA: open each generated DOCX in Word and compare the first page to
the corresponding appendix scan in `docs/sfu-stu-7.5-07.pdf` (pages 38–53).

## Notes / dependencies

- Depends on Task 01 (profile plumbing), Task 04 (extra metadata-required
  rules per form), Task 06 (paragraph styles).
- Form А (assignment) is a separate generator delivered by Task 11 because
  it is excluded from page numbering and inserted **after** the title page.
