# Task 11: Refactor Paragraph Format Dispatch

## Priority: Medium
## Phase: Phase 5 (Renderer rewrite)
## Affected files: `src/sfu_converter/converter.py`
## References: `docs/technical requirements/07_dry_maintainability.md`

## Summary

Replace the 13-branch `if/elif` chain in `_set_paragraph_format()` with a data-driven approach. Currently every style type is handled by a separate branch that extracts the same dict keys repetitively.

## Current State (converter.py)

`_set_paragraph_format(para, style_type)` has 13 branches like:
```python
if style_type == 'normal':
    para.alignment = self.config.ALIGNMENT
    para.paragraph_format.first_line_indent = self.config.FIRST_LINE_INDENT
    para.paragraph_format.line_spacing = self.config.LINE_SPACING_NORMAL
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)
elif style_type == 'h1':
    para.alignment = self.config.H1['align']
    para.paragraph_format.first_line_indent = self.config.H1['indent']
    para.paragraph_format.line_spacing = self.config.H1['line_spacing']
    ...
# repeated 11 more times
```

## Fix: Data-Driven Style Dispatch

### 1. Create a style map that maps style_type strings to config dicts

```python
def _get_style_map(self):
    """Returns a mapping of style_type -> formatting parameters dict."""
    c = self.config
    return {
        'normal': {
            'align': c.ALIGNMENT,
            'indent': c.FIRST_LINE_INDENT,
            'line_spacing': c.LINE_SPACING_NORMAL,
            'bold': False,
            'space_before': Pt(0),
            'space_after': Pt(0),
        },
        'h1': c.H1,
        'h2': c.H2,
        'h3': c.H3,
        'caption_image': c.CAPTION_IMAGE,
        'caption_table': c.CAPTION_TABLE,
        'empty_before_header': c.EMPTY_BEFORE_HEADER,
        'empty_after_header': c.EMPTY_AFTER_HEADER,
        'empty_before_image': c.EMPTY_BEFORE_IMAGE,
        'empty_after_image': c.EMPTY_AFTER_IMAGE,
        'empty_before_table': c.EMPTY_BEFORE_TABLE,
        'empty_after_table': c.EMPTY_AFTER_TABLE,
        'image': {
            'align': c.IMAGE.get('alignment', WD_ALIGN_PARAGRAPH.CENTER),
            'indent': Cm(0),
            'line_spacing': c.IMAGE.get('line_spacing', 1.5),
            'bold': False,
            'space_before': Pt(0),
            'space_after': Pt(0),
        },
    }
```

### 2. Replace `_set_paragraph_format` with generic application

```python
def _set_paragraph_format(self, para, style_type):
    """Apply formatting from the style map."""
    style_map = self._get_style_map()
    style = style_map.get(style_type)
    if style is None:
        self.logger.warning(f"Unknown style_type: {style_type}")
        return

    pf = para.paragraph_format
    if 'align' in style:
        para.alignment = style['align']
    if 'indent' in style:
        pf.first_line_indent = style['indent']
    if 'line_spacing' in style:
        pf.line_spacing = style['line_spacing']
    if 'space_before' in style:
        pf.space_before = style['space_before']
    if 'space_after' in style:
        pf.space_after = style['space_after']
```

### 3. Add validation for unknown style_type

Instead of silently doing nothing for unknown style_type, log a warning. In strict mode, raise.

## Benefits

- Removes ~100 lines of repetitive code
- Adding a new style requires only one dict entry
- Style parameters become testable as data
- Catches unknown style_type strings at runtime

## Tests

- Test every style_type produces correct paragraph formatting
- Test unknown style_type produces warning
- Test that all config dict keys are consumed correctly

## Verification

1. `python -m pytest` — no regressions
2. Convert example files — output is identical to before refactor
3. `_set_paragraph_format` is now ~20 lines instead of ~100
