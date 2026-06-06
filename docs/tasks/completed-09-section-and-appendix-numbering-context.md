# Task 09: Implement Section-Based and Appendix-Based Numbering Context

## Priority: High
## Phase: Phase 5 (Renderer)
## Standard reference
- PDF §7.4 (heading numbering), §7.6 (formulas — section-based and
  appendix-prefixed), §7.7 (tables — `Таблица 7.1`, `Таблица А.1`), §7.8
  (figures — `Рисунок 1.1`, `Рисунок А.1`), §7.11 (appendix internal
  numbering `А.1`, `А.1.1`, `А.1.1.1`, `А.1.1.1.1`).
- Audit rows: "Section-based numbering" / "Appendix numbering" → MISSING for
  formulas, tables, figures, headings inside appendices.

## Affected files
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/numbering.py` *(new)*
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_numbering.py` *(new)*
- `tests/test_docx_renderer.py`

## Current state

The renderer keeps a single global counter for tables, figures and formulas.
Counters never reset between sections or between appendices. Appendix-internal
headings receive plain `1`, `1.1` numbering, not `А.1`, `А.1.1`.

## Implementation

1. Move every counter into a `NumberingContext` class:

   ```python
   class NumberingContext:
       def __init__(self, mode: NumberingMode, ...):
           self.mode = mode  # GLOBAL, SECTION, APPENDIX
           self.section_numbers: list[int] = [0, 0, 0, 0]
           self.appendix_letter: str | None = None
           self.formula_counter = 0
           self.table_counter = 0
           self.figure_counter = 0

       def enter_section(self, level: HeadingLevel): ...
       def enter_appendix(self, letter: str): ...
       def leave_appendix(self): ...
       def next_formula_number(self) -> str: ...
       def next_table_number(self) -> str: ...
       def next_figure_number(self) -> str: ...
   ```

2. The mode is selected per profile via `common.formula.section_numbering`,
   `common.table.section_numbering`, `common.figure.section_numbering`. The
   default for `common` stays `GLOBAL` for backward compatibility; ВКР and
   coursework default to `SECTION` (driven by Task 04 rules).
3. In `enter_appendix(letter)`, swap the counter set so that
   `next_table_number()` returns `А.1`, `А.2`, etc. Heading numbering inside
   appendices follows the same rule: `enter_section` of H1 produces `А.1`,
   H2 produces `А.1.1`.
4. Use a stack so nested appendices (rare, but possible during renderer
   traversal) restore the previous context on exit.
5. Cross-reference resolution (Task 21) reads numbers from this context, not
   from raw counters scattered across the renderer.
6. Update `_format_table_caption`, `_format_figure_caption`, and
   `_render_formula` to call into the context. Drop their local counters.

## Tests

- Profile with `formula.section_numbering=on` renders the second formula in
  section 2 as `(2.1)` and the next as `(2.2)`; section 3 resets to
  `(3.1)`.
- Same profile inside `[APPENDIX letter=A]` renders the first formula as
  `(А.1)` and the first table as `Таблица А.1`.
- Default `common` profile keeps global counters
  (`(1)`, `(2)`, `Таблица 1`, `Таблица 2`, regardless of section).
- H1 inside `[APPENDIX letter=А]` renders as `А.1`; the next `[H2]` inside
  the appendix renders as `А.1.1`.
- Counters reset on each new appendix.

## Verification

```bash
python -m pytest tests/test_numbering.py tests/test_docx_renderer.py
```

## Notes / dependencies

- Required by Tasks 16 (tables), 17 (figures), 18 (formulas), 21
  (cross-references), and 24 (appendix numbering).
