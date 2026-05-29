# Task 07: Validate Structural Document Composition (Required Sections, Order)

## Priority: High
## Phase: Phase 5 (Application validation)
## Standard reference
- PDF §6.1 — required structural elements per document type, mandatory order:
  титульный лист → реферат → содержание → введение → основная часть →
  заключение → список сокращений → список использованных источников →
  приложения. МД adds АННОТАЦИЯ and АВТОРЕФЕРАТ.
- Audit *6.1 Структура текстового документа* table: enforcement of presence,
  per-profile required sections, and ordering is MISSING.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/domain/diagnostics.py`
- `src/sfu_converter/application/composition.py` *(new)*
- `src/sfu_converter/application/convert.py`
- `src/sfu_converter/cli.py` (lint command — see Task 02)
- `src/sfu_converter/registry/rules.py`
- `tests/test_application_composition.py` *(new)*
- `tests/test_application_convert.py`

## Current state

Structural section nodes are parsed and rendered. Nothing checks whether the
document contains a title page, whether the section order matches §6.1, or
whether profile-specific sections (e.g. реферат for ВКР) are present.

## Implementation

1. Add a per-profile composition spec on top of the registry:

   ```python
   @dataclass(frozen=True)
   class CompositionSpec:
       required: tuple[StructuralSectionType, ...]
       optional: tuple[StructuralSectionType, ...]
       order: tuple[StructuralSectionType, ...]
       requires_title_page: bool
       requires_assignment_form_a: bool  # ВКР
       requires_referat: bool             # ВКР, also research reports per §6.3
       requires_main_part: bool
       requires_sources: bool
       allow_appendices_only_after_sources: bool
   ```

   and one instance per profile name, derived from §6.1 + Task 04 rule
   parameters. The `order` tuple is the canonical sequence:

   `TITLE_PAGE → ASSIGNMENT_A → REFERAT → ANNOTATION → CONTENTS → INTRODUCTION →
   MAIN_PART → CONCLUSION → ABBREVIATIONS → SOURCES → APPENDIX`.

2. Add `composition.validate(document, profile)` returning a list of
   diagnostics. Codes:
   - `STRUCTURE_TITLE_PAGE_MISSING` (rule
     `<profile>.title_page.<form>`).
   - `STRUCTURE_MAIN_PART_MISSING` (`<profile>.structure.required_sections`).
   - `STRUCTURE_REQUIRED_SECTION_MISSING` with `data.section`.
   - `STRUCTURE_DUPLICATE_SECTION` (with both source spans).
   - `STRUCTURE_SECTION_OUT_OF_ORDER` (`data.expected_after`,
     `data.actual_position`).
   - `STRUCTURE_APPENDIX_BEFORE_SOURCES`.
   - `STRUCTURE_SOURCES_BEFORE_ABBREVIATIONS`.
3. Treat the "main part" as the contiguous run of `HeadingNode` blocks
   between the introduction and the conclusion or sources; emit
   `STRUCTURE_MAIN_PART_MISSING` when the run is empty.
4. Plug `composition.validate(...)` into `ConvertTextToDocx.execute(...)` and
   `cmd_lint`. Diagnostics are non-blocking warnings unless `--strict`
   promotes them.
5. The renderer continues to render even if composition is invalid; the
   resulting DOCX is still useful for inspection.

## Tests

- Document missing a title page reports
  `STRUCTURE_TITLE_PAGE_MISSING` with the profile-specific rule ID for
  coursework.
- Appendix before sources reports `STRUCTURE_APPENDIX_BEFORE_SOURCES`.
- Two `СОДЕРЖАНИЕ` headings report a single
  `STRUCTURE_DUPLICATE_SECTION` diagnostic with both spans.
- Minimal valid lab report (`[TITLE_PAGE]` + `[H1] Раздел 1` + body)
  passes composition validation.
- Profile-specific required sections (e.g. `research_reports` requires
  `ВВЕДЕНИЕ`) trigger missing-section diagnostics when absent.
- Composition diagnostics serialize through `diagnostic_to_json()` with
  source spans intact.

## Verification

```bash
python -m pytest tests/test_application_composition.py tests/test_application_convert.py
```

## Notes / dependencies

- Depends on Task 01 (profile plumbing) and Task 04 (registry expansion). The
  ВКР assignment Form А (Task 16) and the реферат generator (Task 15)
  populate the section types this validator checks for.
