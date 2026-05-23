# Task 22: Implement Title Page Generation

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Renderer, Config, AST
## References: `docs/formatting requirements/common.md` — Title Page section

## Summary

Add title page generation based on document metadata per STU 7.5-07-2021. The title page layout varies by document type.

## Rules from the Standard

- Title page is page 1 but page number is NOT printed
- Layout depends on document type (VKR, course work, lab report, etc.)
- Common elements:
  - University name (full)
  - Institute name (full)
  - Department name (full)
  - Approval block (for VKR)
  - Document type/name
  - Topic name
  - Supervisor info (position, degree, name, signature)
  - Student info (name, signature)
  - City and year at bottom

## TXT Syntax

### V2 metadata
```text
[DOC syntax=2 profile=lab_practical_project_reports]
[META key=university value="Сибирский федеральный университет"]
[META key=institute value="Институт космических и информационных технологий"]
[META key=department value="Кафедра вычислительной техники"]
[META key=title value="Отчёт по лабораторной работе №1"]
[META key=subject value="Программирование"]
[META key=student value="Иванов И.И."]
[META key=group value="КИ22-01Б"]
[META key=supervisor value="Петров П.П."]
[META key=supervisor_title value="доцент, канд. техн. наук"]
[META key=city value="Красноярск"]
[META key=year value="2026"]
```

## Implementation

### 1. Title page renderer

Create a dedicated title page renderer that takes metadata and generates the appropriate layout:

```python
def _render_title_page(self, metadata: dict[str, str], profile_name: str):
    """Generate title page based on metadata and profile."""
    # University name — centered, uppercase
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run('МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ')
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    
    # Federal university name
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(metadata.get('university', 'Сибирский федеральный университет').upper())
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    # Institute
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(metadata.get('institute', ''))
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    
    # Department
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(metadata.get('department', ''))
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    
    # ... spacing ...
    
    # Document title — centered, bold, large
    para = self.doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(metadata.get('title', ''))
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.bold = True
    
    # ... student/supervisor info, city/year at bottom ...
    
    # Page break after title page
    self.doc.add_page_break()
```

### 2. Use with templates

If a DOCX template is provided with `--template-mode preserve-prefix`, the title page generation is skipped (template already has it). Only generate title page if no template is used or template mode is `replace-body`.

## Tests

- Generate title page with all metadata fields
- Generate title page with minimal metadata (only required fields)
- Verify no page number on title page
- Verify layout matches expected format for lab report profile
- Verify title page is skipped when using preserve-prefix template mode

## Verification

1. Convert with metadata — title page generated with all info
2. Open in Word — layout matches SFU standard form
3. Page number not visible on title page
