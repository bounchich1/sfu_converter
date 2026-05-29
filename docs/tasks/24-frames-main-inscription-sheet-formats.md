# Task 24: Implement Frames, Main Inscriptions (Forms 1–6), and Sheet Formats

## Priority: High (largest renderer feature outside title pages)
## Phase: Phase 5/6 (Renderer)
## Standard reference
- PDF §7.1.2 (p. 14): landscape margins L 20 / R 20 / T 30 / B 10 mm.
- PDF §7.1.3 (p. 14): ДП/КП explanatory notes use framed sheets; horizontal
  text-to-frame margin 5 mm, vertical 15 mm; left sheet edge to frame 20 mm,
  other edges 5 mm.
- PDF §7.2 (p. 14): page number in graph 7 of the main inscription.
- PDF Приложение Р (p. 53): explanatory-note sheet template.
- PDF Приложение С (p. 54–55): main-inscription forms 1, 2, 3, 4 (text
  documents) and 5, 6 (graphic documents) with all 17 graphs.
- Audit *7.1.3 Framed sheets* and *Forms 1–6* — fully MISSING.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/frames.py` *(new)*
- `src/sfu_converter/infrastructure/main_inscription.py` *(new)*
- `src/sfu_converter/infrastructure/section_setup.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_frames.py` *(new)*
- `tests/test_main_inscription.py` *(new)*
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

The renderer produces A4 portrait pages with default margins. There is no
landscape support, no frame, no main inscription, no sheet-format selection.

## Implementation

1. Add a `SectionSetupNode` to the AST representing a Word section:
   `orientation`, `sheet_format` (`A4 | A3 | A3x4 | A4x4 | A2 | A1`),
   `frame` (`none | text_first | text_following | graphic`),
   `title_block_form` (`form_1..form_6`).
2. V2 parser:
   ```
   [SECTION orientation=landscape sheet=A3 frame=text_following form=form_3]
   …content…
   [/SECTION]
   ```
3. `section_setup.configure(document, node)` writes the section properties
   to `document.sections[i]`:
   - portrait margins from `common.page.margins.portrait`;
   - landscape margins from `common.page.margins.landscape` (added in
     Task 04 — flip `common.page.margins.landscape.renderer_status` to
     `IMPLEMENTED`);
   - sheet format → `<w:pgSz w:w=… w:h=…>` (A3 = 297×420, A2 = 420×594,
     A1 = 594×841; A3×4 / A4×4 are oversize sheets — folded to A4 for
     print, but the DOCX uses the unfolded size).
4. `frames.draw(document, section, profile)` adds the rectangular frame.
   Implementation: a single-cell, full-page borderless table whose only
   cell holds the section content, plus a `<w:framePr>` border definition
   set to inscribe the frame at the standard offsets.
5. `main_inscription.render(form, *, fields)` builds the title block per
   Приложение С as a nested table at the bottom-right of the page (forms 1
   and 5 — first sheet) or bottom (forms 3, 4 — following sheets). The
   table fills graphs 1–17; the renderer fills any provided field and
   leaves the rest blank.
6. Page-number wiring: when `frame ∈ {text_first, text_following}`, the
   page-numbering helper from Task 12 places the `PAGE` field into graph 7
   of the title block.
7. Validator additions:
   - `common.page.margins.landscape`: confirm 20/20/30/10 mm;
   - `coursework.frame.course_project_explanatory_note`: each ДП/КП
     section has a frame and a form 1/3 main inscription;
   - `project_designations.title_block.forms`: forms 1, 2 → first sheet;
     forms 3, 4 → following sheets;
   - `graphic_and_demonstration_materials.sheet.frame`: drawings use form
     5/6.
8. Flip:
   - `common.page.margins.landscape` → `IMPLEMENTED`;
   - `coursework.frame.course_project_explanatory_note` → `IMPLEMENTED`;
   - `project_designations.explanatory_note.frame` → `IMPLEMENTED`;
   - `project_designations.title_block.forms` → `IMPLEMENTED`.

## Tests

- A V2 document with `[SECTION orientation=landscape]` produces a Word
  section with landscape orientation and the right margins.
- `[SECTION sheet=A3 frame=text_first form=form_1]` renders an A3
  landscape page with a frame and form 1 main inscription containing the
  expected fields.
- The page number from Task 12 lands inside graph 7 of the inscription.
- A second framed page in the same section uses form 3 (following sheet)
  rather than form 1.
- `cmd_validate_docx --profile coursework` reports a missing frame
  diagnostic for an unframed coursework document.

## Verification

```bash
python -m pytest tests/test_frames.py tests/test_main_inscription.py \
                 tests/test_v2_parser.py tests/test_docx_renderer.py \
                 tests/test_docx_validator.py
```

## Notes / dependencies

- Depends on Task 12 (page numbering) and Task 25 (project designations
  populate field 2).
- Form 5/6 (graphic sheets) consumed by Task 28.
