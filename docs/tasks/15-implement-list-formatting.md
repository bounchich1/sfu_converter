# Task 15: Implement List Formatting

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST, Config
## References: `docs/formatting requirements/common.md` — Enumerations section

## Summary

Add support for bulleted and numbered lists per STU 7.5-07-2021. Currently the converter has no list support at all.

## Rules from the Standard

- Items of the enumeration are introduced by a hyphen (`-`), or, if reference is needed, by lowercase Russian letters (except `ё`, `з`, `й`, `о`, `ч`, `ъ`, `ы`, `ь`), followed by a closing parenthesis
- For further detailing, Arabic numerals followed by a closing parenthesis are used, with paragraph indent
- Each enumeration item that starts with a hyphen or letter is written with lowercase first letter and ends with a semicolon (`;`), except the last item which ends with a period (`.`)
- Items starting with a digit get a period (`.`) at the end
- If enumeration text consists of a complete sentence, it starts with uppercase and ends with a period

## TXT Syntax

### V1 (simple)
```text
- первый элемент;
- второй элемент;
- третий элемент.
```

Auto-detect lines starting with `- ` as list items. Consecutive lines starting with `- ` form a list block.

### V2 (explicit)
```text
[LIST type=bullet]
[-] первый элемент;
[-] второй элемент;
[-] третий элемент.
[LIST_END]

[LIST type=letter]
[а)] первый элемент;
[б)] второй элемент;
[в)] третий элемент.
[LIST_END]

[LIST type=number]
[1)] первый элемент.
[2)] второй элемент.
[3)] третий элемент.
[LIST_END]
```

## Implementation

### 1. Parser additions

In `v1_parser.py`, detect consecutive `- ` lines:
```python
elif stripped.startswith('- '):
    # Accumulate consecutive list items
    items = []
    while i < len(lines) and lines[i].strip().startswith('- '):
        item_text = lines[i].strip()[2:]  # Remove '- '
        items.append(ListItemNode(text=item_text, source=SourceSpan(...)))
        i += 1
    i -= 1  # Back up one since the outer loop will increment
    blocks.append(ListNode(
        list_type=ListType.BULLET,
        items=tuple(items),
        source=span,
    ))
```

### 2. Renderer additions

```python
def _render_list(self, node: ListNode):
    for item in node.items:
        para = self.doc.add_paragraph()
        
        # Set formatting
        pf = para.paragraph_format
        pf.first_line_indent = Cm(1.25)  # Paragraph indent
        pf.line_spacing = 1.5
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Add list marker and text
        if node.list_type == ListType.BULLET:
            text = f"- {item.text}"
        elif node.list_type == ListType.LETTERED:
            # Use Russian letters
            text = f"{self._get_letter(index)}) {item.text}"
        elif node.list_type == ListType.NUMBERED:
            text = f"{index + 1}) {item.text}"
        
        run = para.add_run(text)
        self._set_run_style(run, bold=False)
```

### 3. Config

```python
LIST_ITEM = {
    'align': WD_ALIGN_PARAGRAPH.JUSTIFY,
    'indent': Cm(1.25),
    'line_spacing': 1.5,
    'bold': False,
    'space_before': Pt(0),
    'space_after': Pt(0),
}
```

## Tests

- Parse bullet list from V1 syntax
- Parse lettered list from V2 syntax
- Parse numbered list from V2 syntax
- Render bullet list with correct indentation
- Render lettered list with Russian letters
- Test list items have correct punctuation (semicolons, final period)
- Test empty list handling

## Verification

1. Convert a file with `- item` lines
2. Open in Word — items have hyphens, proper indentation, justified alignment
3. Verify list items are treated as separate paragraphs with correct formatting
