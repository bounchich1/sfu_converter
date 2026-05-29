# Task 28: Implement Graphic and Demonstration Materials (Drawings, Posters, Slides)

## Priority: Medium (separate output mode)
## Phase: Phase 6 (Additional output mode)
## Standard reference
- PDF §8 (p. 28): drawings/charts on framed sheets per ГОСТ 2.301 with
  inscription forms 5 and 6; scales per ГОСТ 2.302; drawing fonts per
  ГОСТ 2.304; abbreviations per ГОСТ 2.316 / Р 21.101. Posters: A1, ≥70 %
  fill, large title, inscription on reverse. Slides: required first-slide
  fields, ≥70 % fill, header continuity, A4 print-out.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/graphics.py` *(new)*
- `src/sfu_converter/infrastructure/pptx_renderer.py` *(new — optional output)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_graphics.py` *(new)*
- `tests/test_pptx_renderer.py` *(new)*

## Current state

The registry exposes graphic-material rules as stubs. None of the renderer
or validator logic exists. The repo is a TXT→DOCX converter; PPTX output
is the natural target for slides.

## Implementation

1. Add nodes `DrawingSheetNode`, `PosterNode`, `SlideDeckNode`,
   `SlideNode`.
2. V2 syntax:
   ```
   [DRAWING sheet=A1 frame=graphic form=form_5 scale="1:50"]
   src="diagram.svg"
   designation=ДП-23.05.02 ABCDEF.001 Э3
   [/DRAWING]
   [POSTER format=A1 title="Архитектура системы"]
   ...
   [/POSTER]
   [SLIDE_DECK format=A4]
       [SLIDE first_slide=true]
           title="Цель работы"
           student="..."
       [/SLIDE]
       [SLIDE]title="Методы"[/SLIDE]
   [/SLIDE_DECK]
   ```
3. Drawings: render to a framed DOCX section using Task 24's frame helper
   with `form_5` or `form_6` inscription. Validate scale string against
   the ГОСТ 2.302 list (added in Task 04 dictionary).
4. Posters: render as a single landscape A1 page with the title at top
   and the body filling at least 70 % of the area (measured by
   non-whitespace text+image rectangles). Inscription rendered on a
   following section labelled "reverse side" — Word cannot rotate pages,
   so the reverse-side section uses the appropriate orientation.
5. Slides: add optional PPTX output via `python-pptx`. The CLI gains
   `--output-format docx|pptx`. PPTX output:
   - first slide carries required fields: institution, institute, title,
     student, supervisor, city, year;
   - subsequent slides reuse the title placeholder for "header
     continuity" (same banner displayed across slides);
   - `slide.layout.aspect_ratio` is set to match A4 (so a printed copy
     fits cleanly on portrait A4);
   - fill-density check uses placeholder + content box area to estimate
     fill ≥ 70 %.
6. Validator additions:
   - `graphic_and_demonstration_materials.sheet.frame`,
   - `graphic_and_demonstration_materials.drawing.scale_set`,
   - `graphic_and_demonstration_materials.drawing.font_set`,
   - `graphic_and_demonstration_materials.poster.fill_density`,
   - `graphic_and_demonstration_materials.poster.title_block_on_reverse`,
   - `graphic_and_demonstration_materials.slide.required_first_slide_fields`,
   - `graphic_and_demonstration_materials.slide.fill_density`,
   - `graphic_and_demonstration_materials.slide.header_continuity`,
   - `graphic_and_demonstration_materials.slide.a4_print_out`.

## Tests

- A `DrawingSheetNode` with `scale="1:1000"` (not in ГОСТ 2.302 list)
  triggers `graphic_and_demonstration_materials.drawing.scale_set`.
- A poster with text covering 30 % of the page triggers
  `graphic_and_demonstration_materials.poster.fill_density`.
- A slide deck whose first slide lacks `supervisor` triggers
  `graphic_and_demonstration_materials.slide.required_first_slide_fields`.
- Slide deck with mismatched titles triggers
  `graphic_and_demonstration_materials.slide.header_continuity`.
- `--output-format pptx --input deck.txt` produces a `.pptx` file with the
  expected slide count.

## Verification

```bash
python -m pytest tests/test_graphics.py tests/test_pptx_renderer.py
```

## Notes / dependencies

- Depends on Task 24 (frames/inscriptions) and Task 25 (project
  designations).
- PPTX output is optional and only required for slide decks; add a
  guard so the dependency is loaded lazily.
