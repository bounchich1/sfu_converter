# Task 25: Rewrite Validator with Rule IDs

## Priority: High
## Phase: Phase 5 (Renderer and validator rewrite)
## Affected files: `src/sfu_converter/validator.py` → NEW `src/sfu_converter/infrastructure/docx_validator.py`
## References: `docs/technical requirements/05_formatting_traceability.md`

## Summary

Rewrite the validator to:
1. Fix `validate_line_spacing()` never being called (current bug)
2. Use rule IDs from the formatting rule registry
3. Report structured `Diagnostic` objects instead of plain strings
4. Validate ALL implemented formatting rules, not just font/indent/spacing
5. Check all runs in a paragraph, not just the first one

## Current Bugs to Fix

### Bug 1: `validate_line_spacing()` is defined but never called

**Location:** `src/sfu_converter/validator.py`, lines 80-91 (defined), lines 93-144 (`validate_file` never calls it)

**Fix:** Add call in `validate_file()`:
```python
# In the paragraph loop (after line 124):
spacing_issues = self.validate_line_spacing(para, para_count)
self.errors.extend(spacing_issues)
```

### Bug 2: Header detection is too simplistic

**Current:** `_is_header_paragraph()` only checks center alignment — false positives for centered image captions.

**Fix:** Check for heading styles:
```python
def _is_header_paragraph(self, para):
    style_name = para.style.name if para.style else ''
    return style_name.startswith('Heading') or (
        para.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
        and any(run.bold for run in para.runs)
    )
```

### Bug 3: Only first run of paragraph is validated

**Current:** `para.runs[0]` — misses formatting on subsequent runs.

**Fix:** Validate all runs:
```python
for run_idx, run in enumerate(para.runs):
    font_issues = self.validate_font(run, para_count)
    self.errors.extend(font_issues)
```

### Bug 4: Magic number in indent calculation

**Current:** `expected_indent_pt = 1.25 * 28.3465` (line 73)

**Fix:** Use `Cm(1.25).pt`:
```python
from docx.shared import Cm
expected_indent_pt = Cm(1.25).pt
```

## Full Rewrite Structure

```python
class DocxValidator:
    def __init__(self, profile: FormattingProfile):
        self.profile = profile
        self.diagnostics: list[Diagnostic] = []
    
    def validate_file(self, file_path: str) -> list[Diagnostic]:
        self.diagnostics = []
        doc = Document(file_path)
        
        self._validate_margins(doc)
        self._validate_page_setup(doc)
        
        for i, para in enumerate(doc.paragraphs):
            self._validate_paragraph(para, i)
        
        for i, table in enumerate(doc.tables):
            self._validate_table(table, i)
        
        return self.diagnostics
    
    def _validate_margins(self, doc):
        for section in doc.sections:
            # Check each margin against rule
            rule = self._get_rule('common.page.margins.portrait')
            if rule:
                expected_left = Cm(rule.parameters['left_mm'] / 10)
                if section.left_margin != expected_left:
                    self.diagnostics.append(Diagnostic(
                        code='FORMAT_MARGIN_LEFT',
                        message=f'Left margin is {section.left_margin}, expected {expected_left}',
                        severity=Severity.ERROR,
                        rule_id=rule.id,
                    ))
    
    def _validate_paragraph(self, para, index):
        if not para.text.strip():
            return
        
        # Font validation — all runs
        for run in para.runs:
            self._validate_font(run, index)
        
        # Paragraph formatting
        self._validate_indent(para, index)
        self._validate_spacing(para, index)
        self._validate_line_spacing(para, index)  # FIXED: now actually called
        self._validate_alignment(para, index)
```

## New Validations to Add

| Validation | Rule ID | Description |
|------------|---------|-------------|
| Page margins | `common.page.margins.portrait` | All 4 margins |
| Font color | `common.text.font.color` | Must be black |
| Line spacing | `common.text.line_spacing` | 1.5 for body, 1.0 for headers |
| Alignment | `common.text.alignment` | Justify for body |
| Heading format | `common.heading.*` | Bold, alignment, indent per level |
| Table font | `common.table.font.size` | 10-12pt |
| No period in headings | `common.heading.no_period` | Heading must not end with `.` |

## Tests

- Validate DOCX with correct formatting → no diagnostics
- Validate DOCX with wrong font → diagnostic with rule ID
- Validate DOCX with wrong margins → diagnostic with rule ID
- Validate line spacing is actually checked (regression test for the bug)
- Validate all runs in paragraph are checked
- Test diagnostic JSON format matches spec

## Verification

1. `python -m pytest tests/test_validator.py` passes
2. Validate a generated DOCX → diagnostics include rule IDs
3. JSON output matches the format in `05_formatting_traceability.md`
