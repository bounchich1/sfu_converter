# Task 14: Implement Section Numbering

## Priority: Medium
## Phase: Phase 5 (Renderer features)
## Affected files: Parser, Renderer, AST
## References: `docs/formatting requirements/common.md` — Sections and subsections

## Summary

Implement automatic hierarchical numbering for sections, subsections, and points per STU 7.5-07-2021:
- Sections: `1`, `2`, `3`, ...
- Subsections: `1.1`, `1.2`, `2.1`, ...
- Points: `1.1.1`, `1.1.2`, ...

## Rules from the Standard

- Sections are numbered with Arabic numerals sequentially within the main body
- Subsections are numbered within each section: `section.subsection`
- Points are numbered within each subsection: `section.subsection.point`
- After the last digit, NO period is placed
- Structural sections (ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ, etc.) are NOT numbered
- Each section starts on a new page
- Headings with numbers do not end with a period

## Implementation

### 1. Add numbering state to the renderer

```python
class SectionNumberer:
    """Tracks and generates hierarchical section numbers."""
    
    def __init__(self):
        self._counters = [0, 0, 0]  # [section, subsection, point]
    
    def next_number(self, level: int) -> str:
        """Get next number for the given heading level (1-3)."""
        idx = level - 1
        self._counters[idx] += 1
        # Reset lower-level counters
        for i in range(idx + 1, len(self._counters)):
            self._counters[i] = 0
        # Build number string
        parts = self._counters[:level]
        return '.'.join(str(p) for p in parts)
    
    def reset(self):
        self._counters = [0, 0, 0]
```

### 2. Apply during rendering

```python
def _render_heading(self, node: HeadingNode):
    if node.number == 'auto':
        number = self._numberer.next_number(node.level.value)
        text = f"{number} {node.text}"
    else:
        text = node.text
    
    para = self.doc.add_paragraph()
    run = para.add_run(text)
    ...
```

### 3. V1 syntax: auto-number by default

In V1 syntax, headings are auto-numbered unless they match structural section names. The parser should set `number='auto'` for regular headings and `number=None` for structural sections.

### 4. V2 syntax: explicit control

```text
[H level=1 title="Теоретическая часть" number=auto]
[H level=2 title="Обзор литературы" number=auto]
[H level=1 title="ВВЕДЕНИЕ" number=none]  # structural, no number
```

## Tests

- Test `SectionNumberer` produces `1`, `2`, `3` for consecutive H1
- Test `SectionNumberer` produces `1.1`, `1.2` for H2 after H1
- Test `SectionNumberer` resets subsection counter on new section
- Test `SectionNumberer` produces `1.1.1`, `1.1.2` for H3
- Test structural sections are not numbered
- Test rendered heading text includes number

## Verification

1. Convert a file with multiple sections/subsections
2. Verify numbering is `1 Heading`, `1.1 Subheading`, `1.1.1 Point`
3. Verify no trailing period after numbers
4. Verify ВВЕДЕНИЕ/ЗАКЛЮЧЕНИЕ have no numbers
