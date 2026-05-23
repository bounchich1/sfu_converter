# Task 12: Implement Page Numbering

## Priority: High
## Phase: Phase 5 (Renderer features)
## Affected files: `src/sfu_converter/converter.py` (or `infrastructure/docx_renderer.py`)
## References: `docs/formatting requirements/common.md` — Page numbering section

## Summary

Add automatic page numbering to generated documents. Per STU 7.5-07-2021:
- Arabic numerals
- Centered at the bottom of the page
- Font size: 14pt
- Title page is page 1 but the number is NOT printed on it
- Numbering starts from 1 including title page

## Detailed Implementation

Page numbering in `python-docx` requires manipulating the section's footer XML directly, because `python-docx` doesn't have a high-level API for page number fields.

### 1. Add a method to the renderer/converter

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def _add_page_numbering(self):
    """Add centered page numbers in the footer."""
    for section in self.doc.sections:
        # Enable "Different First Page" to hide number on title page
        section.different_first_page_header_footer = True
        
        # Configure the default footer (pages 2+)
        footer = section.footer
        footer.is_linked_to_previous = False
        
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Clear existing content
        for run in paragraph.runs:
            run.clear()
        
        run = paragraph.add_run()
        
        # Set font
        run.font.name = self.config.FONT_NAME
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Add PAGE field
        fldChar_begin = OxmlElement('w:fldChar')
        fldChar_begin.set(qn('w:fldCharType'), 'begin')
        run._element.append(fldChar_begin)
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = ' PAGE '
        run._element.append(instrText)
        
        fldChar_end = OxmlElement('w:fldChar')
        fldChar_end.set(qn('w:fldCharType'), 'end')
        run._element.append(fldChar_end)
        
        # First page footer remains empty (no number on title page)
        first_footer = section.first_page_footer
        if first_footer.paragraphs:
            first_footer.paragraphs[0].clear()
```

### 2. Call from document initialization

```python
def _initialize_document(self, template):
    self.doc = self._load_template(template)
    self._setup_document_margins()
    self._add_page_numbering()  # Add this line
```

### 3. Add config constants

In `config.py` or rule registry:
```python
PAGE_NUMBERING = {
    'position': 'bottom_center',
    'font_size': Pt(14),
    'font_name': 'Times New Roman',
    'format': 'arabic',
    'skip_first_page': True,  # Title page has no number
}
```

## Tests

- Generate a DOCX and verify footer XML contains PAGE field
- Verify `different_first_page_header_footer` is True
- Verify first page footer is empty
- Verify default footer has centered alignment
- Verify font is Times New Roman 14pt

## Verification

1. Convert a multi-page example file
2. Open in Word — page 1 has no number, page 2+ shows Arabic numbers centered at bottom
3. Numbers are in Times New Roman 14pt
