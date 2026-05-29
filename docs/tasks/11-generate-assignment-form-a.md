# Task 11: Generate ВКР Assignment Form А (Excluded From Page Count)

## Priority: High (ВКР workflow)
## Phase: Phase 5 (Renderer)
## Standard reference
- PDF §5.6 (p. 9): Form А (задание ВКР) is inserted after the title page and
  is **excluded from the page count**.
- PDF Приложение А (p. 36–37): two-page assignment template with sections:
  утверждаю/задание/тема/исходные данные/перечень разделов/перечень
  графического материала/консультанты/нормоконтролёр/руководитель/студент/
  календарный план/срок защиты.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/syntax_spec.py`
- `src/sfu_converter/infrastructure/title_pages/form_a.py` *(new)*
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_title_page.py`
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`

## Current state

There is no `[ASSIGNMENT_A]` block, no domain node, and no logic for
excluding pages from the global page count. ВКР outputs go straight from
title page to реферат.

## Implementation

1. Add `AssignmentFormANode` with fields:
   - `topic`, `topic_approved_by`, `topic_approval_date`,
   - `initial_data`, `sections`, `graphic_material`,
   - `consultants` (list of `(section, name)`),
   - `norm_controller`, `supervisor`, `student`, `student_group`,
   - `calendar_plan` (list of `(stage, due_date)`),
   - `defense_deadline`, `head_of_department`, `approval_date`.
2. V1 parser recognizes a multiline block:
   ```
   [ASSIGNMENT_A]
   topic = ...
   topic_approval_date = ...
   sections = (multi-line list, dash-prefixed)
   ...
   [/ASSIGNMENT_A]
   ```
3. V2 parser uses attribute syntax with multi-line bodies for the long
   fields (`sections`, `calendar_plan`, `graphic_material`).
4. `title_pages/form_a.render(...)` writes a 2-page block. The first page
   contains the УТВЕРЖДАЮ/ЗАДАНИЕ headers plus the topic, initial data,
   sections, graphic material, consultants. The second page contains the
   календарный план (table) and signatures.
5. Insert a Word section break before and after Form А. The section
   uses the same margins but its footer **omits the page-number field**, so
   those two pages do not affect the visible page numbers in the rest of
   the document.
6. Numbering for subsequent pages must continue from the value the
   document had on entering the assignment (page 1 of the title page is
   blank, page 1 effectively becomes the first page of the реферат).
7. Set `graduation_qualification_work.assignment.form_a` →
   `renderer_status=IMPLEMENTED` (rule added in Task 04).
8. Composition validator (Task 07) gains `STRUCTURE_ASSIGNMENT_A_MISSING`
   when the profile requires it and the AST has no `AssignmentFormANode`.

## Tests

- Parsing `[ASSIGNMENT_A] … [/ASSIGNMENT_A]` produces an
  `AssignmentFormANode` with the expected fields.
- Rendering inserts two pages between the title page and the next block;
  these pages are inside their own DOCX section with `<w:pgNumType>`
  configured to suppress display.
- The reference test `convert --profile graduation_qualification_work` over
  the example fixture produces a document where page numbers begin at the
  реферат, not at Form А.
- Missing Form А for ВКР triggers
  `STRUCTURE_ASSIGNMENT_A_MISSING`.

## Verification

```bash
python -m pytest tests/test_title_page.py tests/test_v1_parser.py tests/test_v2_parser.py
```

## Notes / dependencies

- Pairs with Task 12 (page numbering control). Task 10 must land first to
  position Form А after the chosen ВКР title page form.
