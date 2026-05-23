# Task 16: Implement Inline Text Formatting

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST nodes

## Summary

Add support for bold and italic text within paragraphs. Currently the converter has no inline formatting — all text in a paragraph uses the same style.

## TXT Syntax

### V1 (Markdown-style)
```text
This text has **bold** and *italic* and ***bold italic*** words.
```

### V2 (explicit)
```text
[P] This text has [B]bold[/B] and [I]italic[/I] and [BI]bold italic[/BI] words.
```

## Implementation

### 1. Parser: Split paragraph text into TextRuns

In the parser, when creating `ParagraphNode`, parse inline formatting markers:

```python
import re

def _parse_inline_formatting(self, text: str, source: SourceSpan) -> tuple[TextRun, ...]:
    """Parse **bold**, *italic*, ***bold-italic*** into TextRuns."""
    runs = []
    # Pattern: ***bold italic***, **bold**, *italic*, plain text
    pattern = re.compile(
        r'(\*\*\*(.+?)\*\*\*)'   # bold italic
        r'|(\*\*(.+?)\*\*)'       # bold
        r'|(\*(.+?)\*)'           # italic
        r'|([^*]+)'               # plain text
    )
    for match in pattern.finditer(text):
        if match.group(2):  # bold italic
            runs.append(TextRun(text=match.group(2), bold=True, italic=True))
        elif match.group(4):  # bold
            runs.append(TextRun(text=match.group(4), bold=True))
        elif match.group(6):  # italic
            runs.append(TextRun(text=match.group(6), italic=True))
        elif match.group(7):  # plain
            runs.append(TextRun(text=match.group(7)))
    
    return tuple(runs) if runs else (TextRun(text=text),)
```

### 2. Renderer: Handle multiple TextRuns per paragraph

```python
def _render_paragraph(self, node: ParagraphNode):
    para = self.doc.add_paragraph()
    self._set_paragraph_format(para, 'normal')
    
    for text_run in node.runs:
        run = para.add_run(text_run.text)
        # Apply base style
        self._set_run_style(run, bold=text_run.bold)
        # Apply italic
        if text_run.italic:
            run.font.italic = True
```

### 3. Update AST `TextRun` (already has bold/italic fields)

The `TextRun` dataclass from Task 06 already includes `bold` and `italic` fields, so no AST changes needed.

## Tests

- Parse `**bold**` → TextRun(bold=True)
- Parse `*italic*` → TextRun(italic=True)
- Parse `***bold italic***` → TextRun(bold=True, italic=True)
- Parse mixed text: `Hello **world** and *friends*` → 4 TextRuns
- Parse text with no formatting → single TextRun
- Parse text with unmatched asterisks → treated as literal
- Render paragraph with multiple runs → verify DOCX has correct formatting

## Verification

1. Convert a file with inline **bold** and *italic*
2. Open in Word — bold/italic formatting is applied correctly
3. Existing files without inline formatting still work identically
