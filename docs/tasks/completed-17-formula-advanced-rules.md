# Task 17: Implement Advanced Formula Rules (Indent, Line Continuation, Repeated Symbols, Consecutive Formulas)

## Priority: High
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.6 (p. 19–21).
- Audit *7.6 Формулы* — body indent, line continuation on operator signs,
  repeated-symbol explanation, consecutive formulas separated by comma,
  cross-references are MISSING.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/attributes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/formula_layout.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_formula_layout.py` *(new)*
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

Formulas render as a single paragraph with an auto-number right-aligned in
parentheses. Explanation paragraph honours "no first-line indent". Indent
of the formula body itself is 0 cm — the standard requires 12.5 mm. There is
no symbol-level explanation, no line continuation, no repeated-symbol
shorthand, and no consecutive-formula handling.

## Implementation

1. **Bug fix**: change `common.formula.body.indent_cm` to `1.25`. Update the
   renderer to honour it. Update existing tests.
2. Extend `FormulaNode` with:
   - `explanations: tuple[FormulaSymbol, ...]` where
     `FormulaSymbol(name: str, description: str, repeats: bool = False)`;
   - `continuation_lines: tuple[str, ...]` for multi-line bodies;
   - `consecutive_with: str | None` (id of an immediately preceding
     formula).
3. V2 syntax additions:
   ```
   [FORMULA id=f1 number=auto consecutive=false]
   E = m * c**2
   [FORMULA_SYMBOL name=E text="энергия, Дж"]
   [FORMULA_SYMBOL name=m text="масса, кг"]
   [FORMULA_SYMBOL name=c text="скорость света в вакууме, м/с"]
   [/FORMULA]
   ```

   plus an inline shortcut `[FORMULA_SYMBOL ... repeats=true]` that emits
   `c — то же, что и в формуле (1)`.
4. Renderer:
   - body paragraph: indent 1.25 cm, centred body content followed by a
     right-aligned tab-stop number;
   - line continuation: when the body contains operator signs `+ − = × ÷`
     and the rendered width exceeds the page text width, split on the
     last operator before the right margin and repeat the operator at the
     start of the next line;
   - explanation paragraph: first line `где` (no colon), then one symbol
     per line, left-aligned, no first-line indent;
   - repeated symbols render `<name> — то же, что и в формуле (<n>)`;
   - consecutive formulas: when `consecutive_with` is set, suppress the
     blank line between them and render a `,` after the previous
     formula's body.
5. Validator additions:
   - `common.formula.body_indent` checks 1.25 cm indent on the formula
     paragraph;
   - `common.formula.explanation_marker` — explanation must start with `где`,
     no colon;
   - `common.formula.repeated_symbol` — repeated names must reference an
     earlier formula's symbol;
   - `common.formula.consecutive_comma` — consecutive formulas must be
     separated by comma in the rendered text;
   - `common.formula.line_continuation` — long formulas without operator
     splits trigger info diagnostic.
6. Flip the matching registry rules to `IMPLEMENTED` for `common`.

## Tests

- A formula `(2.1)` indents 1.25 cm; the number is right-aligned at 16.5 cm.
- An explanation block beginning with `где:` produces
  `common.formula.explanation_marker` diagnostic.
- A formula with two `FORMULA_SYMBOL repeats=true` lines produces
  the `то же, что и в формуле (N)` shorthand.
- Consecutive formulas with `consecutive_with` render with no blank line
  and a trailing comma after the first body.
- Long formula body with operator signs triggers automatic line break on
  the operator.

## Verification

```bash
python -m pytest tests/test_formula_layout.py tests/test_v1_parser.py \
                 tests/test_v2_parser.py tests/test_docx_renderer.py \
                 tests/test_docx_validator.py
```

## Notes / dependencies

- Numbering supplied by Task 09 (section/appendix prefixes).
- Cross-reference resolution handled in Task 20.
