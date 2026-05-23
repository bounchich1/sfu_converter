# Task 18: Implement Formula Support

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST
## References: `docs/formatting requirements/common.md` — Formulas section

## Summary

Add formula block support per STU 7.5-07-2021.

## Rules from the Standard

- Formulas are placed on a separate line
- Centered alignment
- Numbered on the right side in parentheses: `(1)`, `(2)`, etc.
- If only one formula in the document, it is numbered `(1)`
- Explanation of symbols follows the formula with the word `где` (where) on a new line without indent
- Each symbol explanation starts on a new line with a hyphen and semicolon separator
- The first line of explanation starts with `где` without paragraph indent

## TXT Syntax

### V1
```text
[FORMULA]
E = mc^2
[FORMULA_END]
```

### V2
```text
[FORMULA id=eq:energy number=auto]
E = mc^2
[FORMULA_END]
[FORMULA_EXPLANATION]
где E — энергия, Дж;
    m — масса, кг;
    c — скорость света, м/с.
[FORMULA_EXPLANATION_END]
```

## Implementation

### 1. Parser

Add formula block detection in `_render_lines()` / parser:
```python
elif stripped.startswith('[FORMULA'):
    formula_lines = []
    explanation = None
    i += 1
    while i < len(lines) and not lines[i].strip().startswith('[FORMULA_END]'):
        formula_lines.append(lines[i])
        i += 1
    # Check for explanation block
    if i + 1 < len(lines) and lines[i + 1].strip().startswith('[FORMULA_EXPLANATION]'):
        i += 2
        expl_lines = []
        while i < len(lines) and not lines[i].strip().startswith('[FORMULA_EXPLANATION_END]'):
            expl_lines.append(lines[i])
            i += 1
        explanation = '\n'.join(expl_lines)
    
    blocks.append(FormulaNode(
        content='\n'.join(formula_lines),
        explanation=explanation,
        source=span,
    ))
```

### 2. Renderer

```python
def _render_formula(self, node: FormulaNode, number: int):
    # Formula paragraph — use tab stops for centering formula and right-aligning number
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    
    # Formula text
    run = para.add_run(node.content)
    self._set_run_style(run, bold=False)
    
    # Number — right-aligned using tab
    run_number = para.add_run(f'\t({number})')
    self._set_run_style(run_number, bold=False)
    
    # Add right-aligned tab stop
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    tab_stops = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), str(int(Cm(16.5).emu / 635)))  # Right margin position
    tab_stops.append(tab)
    para._p.get_or_add_pPr().append(tab_stops)
    
    # Explanation block
    if node.explanation:
        expl_para = self.doc.add_paragraph()
        expl_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        expl_pf = expl_para.paragraph_format
        expl_pf.first_line_indent = Cm(0)  # No indent for "где"
        expl_pf.line_spacing = 1.5
        run = expl_para.add_run(node.explanation)
        self._set_run_style(run, bold=False)
```

### 3. Formula counter

Add a formula counter to the renderer that auto-increments for each formula.

## Tests

- Parse formula block from V1 and V2 syntax
- Render formula with centered alignment
- Verify formula number appears right-aligned
- Render explanation block with `где` prefix
- Test multiple formulas get sequential numbers
- Test formula without explanation

## Verification

1. Convert a file with formulas
2. Open in Word — formulas centered, numbers right-aligned in parentheses
3. Explanation starts with `где` without indent
