# Task 13: Implement Structural Sections

## Priority: High
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, Config
## References: `docs/formatting requirements/common.md` — Core Text Document Structure

## Summary

Implement formatting for structural document sections per STU 7.5-07-2021. These are predefined section headings that follow special formatting rules different from regular H1/H2/H3 headings.

## Structural Section Names

These are always uppercase, centered, bold, no numbering, no indent:
- `РЕФЕРАТ` (Abstract)
- `АННОТАЦИЯ` (Annotation)
- `СОДЕРЖАНИЕ` (Contents)
- `ВВЕДЕНИЕ` (Introduction)
- `ЗАКЛЮЧЕНИЕ` (Conclusion)
- `СПИСОК СОКРАЩЕНИЙ` (List of abbreviations)
- `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` (List of used sources)
- `ПРИЛОЖЕНИЕ` (Appendix)

## Formatting Rules

- Centered alignment
- No paragraph indent (first_line_indent = 0)
- UPPERCASE letters
- Bold font
- No numbering
- No underline
- Separated from following text by one blank line
- Each starts on a new page (page break before)

## Implementation

### 1. Add syntax support (V1 and V2)

**V1 syntax** — auto-detect known structural headings in H1 tags:
```text
[H1] ВВЕДЕНИЕ
```
If the H1 text (uppercased) matches a known structural heading, treat it as a structural section.

**V2 syntax** — explicit marker:
```text
[SECTION type=introduction]
```
or
```text
[STRUCTURAL title="ВВЕДЕНИЕ"]
```

### 2. Add AST node

In `domain/ast_nodes.py`:
```python
class StructuralSectionType(Enum):
    ABSTRACT = "РЕФЕРАТ"
    ANNOTATION = "АННОТАЦИЯ"
    CONTENTS = "СОДЕРЖАНИЕ"
    INTRODUCTION = "ВВЕДЕНИЕ"
    CONCLUSION = "ЗАКЛЮЧЕНИЕ"
    ABBREVIATIONS = "СПИСОК СОКРАЩЕНИЙ"
    SOURCES = "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"
    APPENDIX = "ПРИЛОЖЕНИЕ"

@dataclass(frozen=True)
class StructuralSectionNode:
    section_type: StructuralSectionType
    title: str  # The actual displayed title
    source: Optional[SourceSpan] = None
```

### 3. Add renderer logic

```python
def _render_structural_section(self, node: StructuralSectionNode):
    # Add page break before
    self.doc.add_page_break()
    
    # Add heading paragraph
    para = self.doc.add_paragraph()
    run = para.add_run(node.title.upper())
    self._set_run_style(run, bold=True)
    
    # Formatting
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    
    # Empty line after
    self._add_empty_paragraph('empty_after_header')
```

### 4. Add config

```python
STRUCTURAL_SECTION = {
    'align': WD_ALIGN_PARAGRAPH.CENTER,
    'bold': True,
    'line_spacing': 1.0,
    'indent': Cm(0),
    'uppercase': True,
    'page_break_before': True,
    'space_before': Pt(0),
    'space_after': Pt(0),
}

STRUCTURAL_HEADINGS = [
    'РЕФЕРАТ', 'АННОТАЦИЯ', 'СОДЕРЖАНИЕ', 'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ',
    'СПИСОК СОКРАЩЕНИЙ', 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'ПРИЛОЖЕНИЕ'
]
```

## Tests

- Parser recognizes structural headings in `[H1]` tags
- Renderer applies page break before structural sections
- Renderer applies uppercase, centered, bold formatting
- Renderer adds blank line after heading
- Each structural section type is recognized correctly

## Verification

1. Convert a file with `[H1] ВВЕДЕНИЕ` — opens on new page, centered, bold, uppercase
2. Convert a file with `[H1] ЗАКЛЮЧЕНИЕ` — same formatting
3. Regular H1 headings that don't match structural names retain normal H1 formatting
