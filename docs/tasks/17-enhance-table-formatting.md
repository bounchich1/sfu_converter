# Task 17: Enhance Table Formatting

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: `src/sfu_converter/converter.py`, Config
## References: `docs/formatting requirements/common.md` — Tables section

## Summary

Current table implementation is basic. Enhance to match STU 7.5-07-2021 requirements.

## Current Gaps vs Standard

| Feature | Current | Required |
|---------|---------|----------|
| Font size in tables | 14pt (same as body) | 10-12pt allowed |
| Header separator | Single line | Double line (per standard) |
| Multi-page tables | Not supported | "Продолжение таблицы N" header on continuation pages |
| Table caption format | Basic left-align | "Таблица N — Name" with hyphen, left-aligned |
| Table reference | Not implemented | Must reference every table in text as "таблица N" or "(таблица N)" |
| Column width | Auto | Should respect content |
| Cell padding | Pt(6) fixed | Configurable |

## Implementation

### 1. Table font size

Add config option and apply in `_create_table()`:
```python
TABLE = {
    'font_size': Pt(12),  # 12pt for table content (10-12pt allowed)
    'header_font_size': Pt(12),
    'header_bold': True,
    'line_spacing': 1.0,  # Single spacing in tables
    'cell_padding': Pt(6),
}
```

Update `_create_table()` to apply table-specific font size:
```python
for row in table.rows:
    for cell in row.cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.size = self.config.TABLE['font_size']
```

### 2. Table caption formatting

Format: `Таблица N — Название` (em-dash, not hyphen)
```python
def _format_table_caption(self, caption: str, table_number: int) -> str:
    # If caption doesn't start with "Таблица", prepend
    if not caption.startswith('Таблица'):
        return f"Таблица {table_number} \u2014 {caption}"
    return caption
```

### 3. Multi-page table headers

This requires XML manipulation in python-docx to set the "Repeat Header Rows" property:
```python
def _set_repeat_header_row(self, table):
    """Set first row to repeat on every page."""
    row = table.rows[0]
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    trPr.append(tblHeader)
```

### 4. Update table cell formatting

- Apply single line spacing (1.0) in table cells
- Center-align header row
- Left-align data rows
- Apply configurable cell padding

## Tests

- Table content uses 12pt font
- Header row is bold
- Table caption is formatted correctly with em-dash
- Repeat header row XML property is set
- Cell padding is applied

## Verification

1. Convert a file with tables
2. Open in Word — table font is 12pt, headers are bold, captions use em-dash
3. For long tables — header row repeats on subsequent pages
