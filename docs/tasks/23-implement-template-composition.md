# Task 23: Implement Template Composition

## Priority: High
## Phase: Phase 5A (Template composition)
## Affected files: Renderer, CLI, NEW template adapter
## References: `docs/technical requirements/02_clean_architecture.md` — Template composition requirements

## Summary

Implement DOCX template composition allowing users to provide pre-formatted title pages and front matter that the converter preserves while appending generated content.

## Requirements from Technical Docs

- Template pages selected for preservation must NOT be reformatted, restyled, or mutated
- Converter must preserve template's sections, headers, footers, margins, title blocks, page numbering, and embedded media
- Generated content starts at the requested insertion point with a page/section break
- Template adapter must report diagnostic if insertion point not found
- Validator can validate whole document or only generated part

## CLI Interface

```bash
# Preserve page 1 (title page), append after it
sfu-converter convert --input report.txt --output report.docx \
  --template title_page.docx --template-mode preserve-prefix --insert-after-page 1

# Preserve pages 1-2, append after page 2
sfu-converter convert --input report.txt --output report.docx \
  --template front_matter.docx --template-mode preserve-prefix --insert-after-page 2

# Insert at a named bookmark
sfu-converter convert --input report.txt --output report.docx \
  --template template.docx --insert-at-bookmark CONTENT_START

# Append after full template (default)
sfu-converter convert --input report.txt --output report.docx \
  --template template.docx --template-mode append
```

## Implementation

### 1. Template adapter port

```python
# ports/template.py
class TemplatePort(ABC):
    @abstractmethod
    def load_template(self, path: str) -> 'TemplateDocument':
        ...
    
    @abstractmethod
    def find_insertion_point(self, template: 'TemplateDocument',
                              mode: str, page: int | None = None,
                              bookmark: str | None = None) -> 'InsertionPoint':
        ...
    
    @abstractmethod
    def compose(self, template: 'TemplateDocument',
                insertion_point: 'InsertionPoint',
                generated_content: bytes) -> bytes:
        ...
```

### 2. Infrastructure implementation

```python
# infrastructure/template_adapter.py
class DocxTemplateAdapter(TemplatePort):
    def load_template(self, path: str) -> TemplateDocument:
        doc = Document(path)
        return TemplateDocument(doc=doc, path=path)
    
    def find_insertion_point(self, template, mode, page=None, bookmark=None):
        if bookmark:
            # Search for named bookmark in template
            bookmarks = self._find_bookmarks(template.doc)
            if bookmark not in bookmarks:
                return InsertionPoint(found=False, diagnostic=Diagnostic(
                    code='TEMPLATE_BOOKMARK_NOT_FOUND',
                    message=f'Bookmark "{bookmark}" not found in template',
                    severity=Severity.ERROR,
                ))
            return InsertionPoint(found=True, element=bookmarks[bookmark])
        
        if mode == 'preserve-prefix' and page:
            # Find the paragraph/element after the Nth page break
            return self._find_after_page(template.doc, page)
        
        # Default: append at end
        return InsertionPoint(found=True, element=None)  # append
    
    def compose(self, template, insertion_point, generated_content):
        # Copy template, insert generated content at insertion point
        ...
```

### 3. Integration with converter

Update the conversion pipeline:
```python
def convert_file(self, input_file, output_file, template=None,
                 template_mode='append', insert_after_page=None,
                 insert_at_bookmark=None):
    source = Path(input_file).read_text(encoding='utf-8')
    ast = self.parser.parse(source)
    
    if template:
        tmpl = self.template_adapter.load_template(template)
        insertion = self.template_adapter.find_insertion_point(
            tmpl, template_mode, insert_after_page, insert_at_bookmark
        )
        if not insertion.found:
            # Report diagnostic
            ...
        # Render into template
        self.renderer.render_into_template(ast, tmpl, insertion)
    else:
        self.renderer.render(ast, output_file)
```

## Tests

- Load template and find insertion after page 1
- Load template and find insertion after page 2
- Load template with bookmark and find insertion point
- Template with missing bookmark → diagnostic
- Composed document preserves template formatting
- Generated content starts after insertion point
- Preserved pages are not modified

## Verification

1. Use `templates/template1.docx` — append after full template
2. Create a template with 2 pages — preserve both, append after
3. Verify template pages retain original formatting
4. Verify generated content follows template with proper page break
