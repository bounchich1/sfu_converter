# Task 20: Implement Appendices

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST
## References: `docs/formatting requirements/common.md` — Appendices section

## Summary

Add appendix support per STU 7.5-07-2021.

## Rules from the Standard

- Each appendix starts on a new page
- Heading: `ПРИЛОЖЕНИЕ А` (using Russian uppercase letters: А, Б, В, Г, Д, Е, Ж, И, К, Л, М, Н, П, Р, С, Т, У, Ф, Х, Ц, Ш, Щ)
- Letters `Ё`, `З`, `Й`, `О`, `Ч`, `Ъ`, `Ы`, `Ь` are NOT used
- The appendix heading is centered
- Below the designation, on a separate line, the appendix title is centered in parentheses with the content type
- Appendices can be mandatory (`обязательное`) or informational (`справочное`, `рекомендуемое`)
- Appendices have their own page numbering or continue document numbering
- Tables, figures, and formulas in appendices are numbered with the appendix letter prefix: `Таблица А.1`, `Рисунок Б.2`

## TXT Syntax

### V1
```text
[H1] ПРИЛОЖЕНИЕ А
Справочное
Название приложения
```

### V2
```text
[APPENDIX id=app:a letter=А type=справочное title="Исходные данные"]
```

## Implementation

### 1. Add Russian letter sequence utility

```python
APPENDIX_LETTERS = [
    'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'И', 'К', 'Л', 'М', 'Н',
    'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ш', 'Щ',
]
```

### 2. Parser

Detect `[H1] ПРИЛОЖЕНИЕ X` pattern:
```python
if stripped.upper().startswith('[H1] ПРИЛОЖЕНИЕ'):
    letter = stripped.split()[-1] if len(stripped.split()) > 2 else None
    blocks.append(AppendixNode(
        title=stripped.replace('[H1]', '').strip(),
        id=f'app:{letter.lower()}' if letter else None,
        source=span,
    ))
```

### 3. Renderer

```python
def _render_appendix(self, node: AppendixNode):
    # Page break
    self.doc.add_page_break()
    
    # "ПРИЛОЖЕНИЕ X" centered
    para = self.doc.add_paragraph()
    run = para.add_run(node.title.upper())
    self._set_run_style(run, bold=True)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.first_line_indent = Cm(0)
```

## Tests

- Parse appendix from V1 syntax
- Verify correct Russian letter sequence (no Ё, З, Й, О, Ч, Ъ, Ы, Ь)
- Render appendix with page break and centered heading
- Test multiple appendices get sequential letters

## Verification

1. Convert a file with appendices
2. Open in Word — each appendix on new page, centered heading with letter
