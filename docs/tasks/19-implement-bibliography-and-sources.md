# Task 19: Implement Bibliography / Source List

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST
## References: `docs/formatting requirements/common.md` — List of Used Sources

## Summary

Add source list and bibliographic reference support per STU 7.5-07-2021.

## Rules from the Standard

- Sources are listed in the order they are first referenced in the text
- Each source entry is numbered: `1 Автор. Название. — Город: Издательство, год.`
- In-text references use square brackets: `[1]`, `[1, 2]`, `[1-5]`
- The section heading is `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` (structural section)
- Formatting follows GOST R 7.0.100-2018

## TXT Syntax

### V1
```text
[H1] СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ
1 Иванов И.И. Основы программирования. — М.: Наука, 2023.
2 Петров П.П. Алгоритмы и структуры данных. — СПб.: БХВ, 2022.
```

In-text references can be literal: `... как показано в [1]...`

### V2
```text
[SOURCE number=1] Иванов И.И. Основы программирования. — М.: Наука, 2023.
[SOURCE number=2] Петров П.П. Алгоритмы и структуры данных. — СПб.: БХВ, 2022.

[REF target=1] — generates [1] inline reference
```

## Implementation

### 1. Parser

In V1, numbered lines after `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` are bibliography entries:
```python
# Detect "N Author..." pattern (number at start of line)
if re.match(r'^\d+\s', stripped) and self._in_bibliography:
    match = re.match(r'^(\d+)\s(.+)', stripped)
    blocks.append(BibliographyEntryNode(
        number=int(match.group(1)),
        text=match.group(2),
        source=span,
    ))
```

### 2. Renderer

```python
def _render_bibliography_entry(self, node: BibliographyEntryNode):
    para = self.doc.add_paragraph()
    text = f"{node.number} {node.text}"
    run = para.add_run(text)
    self._set_run_style(run, bold=False)
    
    pf = para.paragraph_format
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(1.25)
    pf.line_spacing = 1.5
```

## Tests

- Parse bibliography entries with numbers
- Parse in-text references `[1]`
- Render source list with correct formatting
- Test sequential numbering

## Verification

1. Convert a file with a source list
2. Open in Word — sources are numbered, properly formatted
3. In-text references `[1]` appear correctly
