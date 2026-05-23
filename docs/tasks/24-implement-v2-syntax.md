# Task 24: Implement V2 TXT Syntax

## Priority: Medium
## Phase: Phase 3 (Version 2 syntax)
## Affected files: NEW `src/sfu_converter/parser/v2_parser.py`
## References: `docs/technical requirements/04_txt_syntax.md`

## Summary

Implement the version 2 TXT syntax which is explicit, agent-friendly, and deterministic. V2 must produce the same AST as V1 for equivalent content.

## V2 Syntax Elements

### Document metadata
```text
[DOC syntax=2 profile=lab_practical_project_reports language=ru]
[META key=title value="Report title"]
```

### Headings
```text
[H level=1 title="Введение" number=auto]
```

### Paragraphs
```text
[P] Normal paragraph text.
```

### Figures
```text
[FIGURE src="image.png" caption="Description" id=fig:overview number=auto]
```

### Tables
```text
[TABLE caption="Data" id=tbl:data number=auto]
| A | B |
| C | D |
[TABLE_END]
```

### Lists
```text
[LIST type=bullet]
[-] item 1
[-] item 2
[LIST_END]
```

### Formulas
```text
[FORMULA id=eq:main number=auto]
E = mc^2
[FORMULA_END]
```

### References
```text
[REF target=fig:overview]
[SOURCE number=1] Author. Title. Year.
```

### Page breaks and appendices
```text
[PAGE_BREAK]
[APPENDIX id=app:a title="Data"]
```

### Escaping
```text
[RAW]
[This is not a marker]
[RAW_END]
```

## Implementation

### 1. Attribute parser

```python
def _parse_attributes(self, text: str) -> dict[str, str]:
    """Parse key=value and key="value with spaces" attributes."""
    attrs = {}
    pattern = re.compile(r'(\w+)=(?:"([^"]*)"|([^\s\]]+))')
    for match in pattern.finditer(text):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        attrs[key] = value
    return attrs
```

### 2. V2 Parser class

```python
class V2Parser(BaseParser):
    def parse(self, source: str, filename: str | None = None) -> ParserResult:
        lines = source.splitlines()
        blocks = []
        diagnostics = []
        metadata = {}
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            span = SourceSpan(line_start=i+1, line_end=i+1, filename=filename)
            
            if line.startswith('[DOC '):
                attrs = self._parse_attributes(line)
                # Extract syntax version, profile, language
                ...
            elif line.startswith('[META '):
                attrs = self._parse_attributes(line)
                metadata[attrs.get('key', '')] = attrs.get('value', '')
                blocks.append(MetadataNode(key=attrs['key'], value=attrs['value'], source=span))
            elif line.startswith('[H '):
                attrs = self._parse_attributes(line)
                level = int(attrs.get('level', 1))
                title = attrs.get('title', '')
                blocks.append(HeadingNode(
                    level=HeadingLevel(level),
                    text=title,
                    number=attrs.get('number'),
                    source=span,
                ))
            elif line.startswith('[P]'):
                text = line[3:].strip()
                runs = self._parse_inline_formatting(text, span)
                blocks.append(ParagraphNode(runs=runs, source=span))
            elif line.startswith('[FIGURE '):
                attrs = self._parse_attributes(line)
                blocks.append(FigureNode(
                    src=attrs.get('src', ''),
                    caption=attrs.get('caption'),
                    id=attrs.get('id'),
                    source=span,
                ))
            # ... TABLE, LIST, FORMULA, APPENDIX, PAGE_BREAK, RAW, SOURCE, REF
            i += 1
        
        document = Document(
            blocks=tuple(blocks),
            syntax_version=2,
            metadata=metadata,
            source_file=filename,
        )
        return ParserResult(document=document, diagnostics=diagnostics)
```

### 3. Parser factory

```python
def get_parser(syntax_version: int) -> BaseParser:
    if syntax_version == 1:
        return V1Parser()
    elif syntax_version == 2:
        return V2Parser()
    else:
        raise ValueError(f"Unsupported syntax version: {syntax_version}")
```

## Tests

- Parse every V2 block type
- V1 and V2 produce equivalent AST for same content
- Test attribute parsing with quoted values
- Test unknown markers in strict mode
- Test RAW block escaping
- Test duplicate ID detection
- Test invalid syntax version

## Verification

1. Create V2 example files
2. Parse and compare AST with equivalent V1 files
3. Convert V2 files — output matches V1 conversion
