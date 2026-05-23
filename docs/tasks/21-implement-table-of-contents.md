# Task 21: Implement Table of Contents

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Renderer
## References: `docs/formatting requirements/common.md` — Contents section

## Summary

Add automatic table of contents (TOC) generation per STU 7.5-07-2021.

## Rules from the Standard

- Include headings of structural elements, all sections/subsections/points, and appendices
- Headings written in lowercase with first letter uppercase
- Dot leaders between heading and page number
- Headings must exactly match headings in the text
- Section headings start at line beginning
- Subsection entries indented 2 characters relative to sections
- Point entries indented 2 characters relative to subsections
- If document ≤24 pages, TOC is not recommended

## Implementation

### 1. Insert TOC field in DOCX

`python-docx` does not have native TOC support. Insert a TOC field code that Word will update when opening:

```python
def _add_table_of_contents(self):
    """Add a TOC field that Word will update on open."""
    # Add СОДЕРЖАНИЕ heading
    para = self.doc.add_paragraph()
    run = para.add_run('СОДЕРЖАНИЕ')
    self._set_run_style(run, bold=True)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.first_line_indent = Cm(0)
    
    # Add empty line
    self._add_empty_paragraph('empty_after_header')
    
    # Add TOC field
    paragraph = self.doc.add_paragraph()
    run = paragraph.add_run()
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(qn('w:fldCharType'), 'begin')
    run._element.append(fldChar_begin)
    
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' TOC \\o "1-3" \\h \\z \\u '  # 3 levels, hyperlinks
    run._element.append(instrText)
    
    fldChar_separate = OxmlElement('w:fldChar')
    fldChar_separate.set(qn('w:fldCharType'), 'separate')
    run._element.append(fldChar_separate)
    
    # Placeholder text
    run2 = paragraph.add_run('Обновите оглавление (Ctrl+A, F9)')
    self._set_run_style(run2, bold=False)
    
    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(qn('w:fldCharType'), 'end')
    run2._element.append(fldChar_end)
    
    # Page break after TOC
    self.doc.add_page_break()
```

### 2. Apply heading styles for TOC recognition

For TOC fields to work, headings must use Word's built-in heading styles (`Heading 1`, `Heading 2`, `Heading 3`):

```python
def _render_heading(self, node: HeadingNode):
    # Use built-in heading style for TOC compatibility
    style_name = f'Heading {node.level.value}'
    para = self.doc.add_paragraph(style=style_name)
    # Then override formatting to match SFU standard
    ...
```

### 3. Insert TOC at the correct position

TOC goes after the title page and before ВВЕДЕНИЕ. The renderer must track document structure and insert TOC at the right point.

## Tests

- Verify TOC field XML is correctly generated
- Verify headings use built-in Word heading styles
- Verify TOC placeholder text is present
- Integration test: generate DOCX with TOC and multiple headings

## Verification

1. Convert a multi-section file
2. Open in Word — TOC field is present
3. Press Ctrl+A, F9 — TOC updates with all headings and page numbers
4. Click on TOC entries — hyperlinks navigate to correct headings
