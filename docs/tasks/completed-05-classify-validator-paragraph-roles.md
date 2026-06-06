# Task 05: Implement Validator Paragraph-Role Classification

## Priority: Critical (prerequisite for almost every fine-grained rule)
## Phase: Phase 5 (Validator)
## Standard reference
- Audit "Validator coverage at a glance": every paragraph is checked against
  body-text rules, so figure captions, missing-image placeholders, formula
  bodies, formula explanations, bibliography entries and table captions raise
  false positives on `common.text.indent.first_line`.
- PDF §7.4–§7.10 — each paragraph type has its own rule family; without role
  classification the validator cannot route to the correct rule.

## Affected files
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/infrastructure/paragraph_roles.py` *(new)*
- `src/sfu_converter/domain/diagnostics.py`
- `tests/test_paragraph_roles.py` *(new)*
- `tests/test_docx_validator.py`
- `tests/test_validator.py`

## Current state

`DocxValidator` walks `document.paragraphs` and applies `common.text.*` to
every paragraph that is not recognized as a heading or structural heading.
Generated figure captions, formula bodies, formula explanations, bibliography
entries, table captions, missing-image placeholders, list items, and TOC
entries fail body-indent checks.

## Implementation

1. Create `infrastructure/paragraph_roles.py` exposing:

   ```python
   class ParagraphRole(Enum):
       BODY = auto()
       HEADING_H1 = auto()
       HEADING_H2 = auto()
       HEADING_H3 = auto()
       HEADING_H4 = auto()
       STRUCTURAL_HEADING = auto()
       TOC_HEADING = auto()
       TOC_ENTRY = auto()
       TABLE_CAPTION = auto()
       FIGURE_CAPTION = auto()
       FIGURE_EXPLANATORY = auto()
       FIGURE_PLACEHOLDER = auto()
       LIST_ITEM = auto()
       FORMULA_BODY = auto()
       FORMULA_EXPLANATION = auto()
       BIBLIOGRAPHY_ENTRY = auto()
       APPENDIX_HEADING = auto()
       PAGE_NUMBER = auto()
       UNKNOWN = auto()
   ```

   and `classify(paragraph, *, prev, next, table_context, figure_context,
   profile) -> ParagraphRole`.
2. Classify using these signals (in order):
   1. Word style name on the paragraph (`Heading 1`, `Heading 2`, `Heading 3`,
      `Heading 4`, `TOC 1`, `Caption`).
   2. Custom style name applied by the renderer
      (`SFUStructuralHeading`, `SFUTableCaption`, `SFUFigureCaption`,
      `SFUFormulaBody`, `SFUFormulaExplanation`, `SFUBibliographyEntry`,
      `SFUListItem`, `SFUFigurePlaceholder`).
   3. Regex on `paragraph.text` (only when style does not disambiguate):
      - `^\s*(Таблица|Продолжение таблицы|Окончание таблицы)\s+`,
      - `^\s*(Рисунок)\s+`,
      - `^\s*\d+(\.\d+)*\s+\S` for headings,
      - `^\s*[аб]\)|^\s*[-—–]\s` for list items,
      - `^\s*\[\s*\d+\s*\]` for missing-image placeholders.
   4. Surrounding structure: paragraphs after a `figure_context` table within
      the same `Table` element are usually figure captions; a paragraph
      following an inline image is the caption.
3. Update the renderer (Task 06 covers the styles) to apply these custom
   styles consistently. Until styles ship, fall back to text regexes.
4. Replace the body-text check loop with a router that dispatches on role.
   Each role corresponds to a rule ID:
   - `BODY` → `common.text.*`
   - `HEADING_H1/H2/H3/H4` → `common.heading.h1/h2/h3/h4`
   - `STRUCTURAL_HEADING` → `common.structural.heading`
   - `TOC_HEADING` → `common.structural.heading`
   - `TOC_ENTRY` → no first-line indent check
   - `TABLE_CAPTION` → `common.table.caption`
   - `FIGURE_CAPTION` → `common.figure.caption`
   - `FIGURE_EXPLANATORY` → `common.figure.explanatory_data`
   - `FIGURE_PLACEHOLDER` → no body checks; emit only `FIGURE_MISSING_IMAGE`
     `INFO` diagnostic
   - `LIST_ITEM` → `common.list.item`
   - `FORMULA_BODY` → `common.formula.body`
   - `FORMULA_EXPLANATION` → `common.formula.explanation`
   - `BIBLIOGRAPHY_ENTRY` → `common.bibliography.entry`
   - `APPENDIX_HEADING` → `common.appendix.heading` (introduce stub if missing)
5. When classification yields `UNKNOWN`, emit `FORMAT_ROLE_UNRECOGNIZED`
   `WARNING` only when the paragraph carries non-default formatting that does
   not match body text; pure body text is silent.
6. Keep all heuristics free of `python-docx` mutation: no edits to the
   document during classification.

## Tests

- A generated DOCX (built from a fixture TXT) containing one of each block
  type validates without `common.text.indent.first_line` false positives.
- Forcing the wrong alignment on a figure caption surfaces
  `common.figure.caption`, not `common.text.alignment`.
- Forcing the wrong indent on a formula explanation surfaces
  `common.formula.explanation`, not `common.text.indent.first_line`.
- TOC entries do not fail the first-line indent rule.
- A paragraph whose text matches `Рисунок 1 — Foo` and whose style is
  `Caption` classifies as `FIGURE_CAPTION`.
- An unknown styled paragraph that is centered, bold, uppercase, and starts
  with a digit classifies as `STRUCTURAL_HEADING` (matches the renderer's
  output) — assert against a fixture.

## Verification

```bash
python -m pytest tests/test_paragraph_roles.py tests/test_docx_validator.py tests/test_validator.py
```

## Notes / dependencies

- Task 06 (paragraph styles in renderer) is best landed alongside this task.
  Until then, classification falls back to regex heuristics on existing
  output.
- Many later validator-status flips depend on this work: figure caption,
  table caption, formula body, bibliography entry validators all assume
  correct paragraph routing.
