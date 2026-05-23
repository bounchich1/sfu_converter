# TXT syntax requirements

## Syntax goals

The TXT syntax must be easy for AI agents to generate and easy for humans to review. It must be line-oriented, explicit, deterministic, UTF-8 encoded, and versioned.

## Compatibility

Syntax version 1 is the current README syntax:

```text
[H1] Heading
[H2] Heading
[H3] Heading
[IMAGE=filename.png]
Рисунок 1 - Caption
[TABLE_START]
[TABLE_CAPTION] Таблица 1 - Caption
| A | B |
| C | D |
[TABLE_END]
```

Version 1 must remain supported through a compatibility parser. It must produce the same AST as version 2.

## Version 2 principles

- Document syntax version must be explicit or CLI-selected.
- Tags must use Latin uppercase marker names.
- Tag attributes must use `key=value`.
- Quoted strings must support spaces.
- Ambiguous natural-language inference must be avoided.
- Every block that can be referenced must support an optional stable `id`.
- Parser diagnostics must include line and column.
- Unknown tags must fail in strict mode and warn in compatibility mode.

## Required version 2 blocks

### Document metadata

```text
[DOC syntax=2 profile=lab_practical_project_reports language=ru]
[META key=title value="Report title"]
[META key=student value="Ivanov I.I."]
```

Template usage may be declared in metadata, but CLI flags must take precedence:

```text
[DOC syntax=2 profile=lab_practical_project_reports template="title_page.docx" template_mode=preserve-prefix insert_after_page=1]
```

This means the DOCX template contains already formatted front matter and generated content must begin after page 1 without modifying the preserved page.

### Headings and paragraphs

```text
[H level=1 title="Введение" number=auto]
[P] Normal paragraph text.
```

`[H level=1]`, `[H level=2]`, and `[H level=3]` must map to the existing heading levels. The parser may support shorthand aliases `[H1]`, `[H2]`, and `[H3]` for version 1 compatibility only.

### Figures

```text
[FIGURE src="research_overview.png" caption="Общая схема исследования" id=fig:overview number=auto]
```

Caption text must be an attribute or explicit child block. The parser must not guess captions from the next plain line in version 2.

### Tables

```text
[TABLE caption="Источники информации" id=tbl:sources number=auto]
| Author | Year | Result |
| Petrov | 2023 | Method |
[TABLE_END]
```

The first row is the header unless `header=false` is set. All rows must have the same number of cells unless the syntax later introduces explicit colspan support.

### Lists

```text
[LIST type=bullet]
[-] first item
[-] second item
[LIST_END]
```

Lettered and numbered list forms must support SFU list rules from the formatting documents.

### Formulas

```text
[FORMULA id=eq:sample number=auto]
E = mc^2
[FORMULA_END]
[FORMULA_EXPLANATION] где E - energy
```

Formula support must include numbering modes required by the formatting profile.

### References

```text
[REF target=fig:overview]
[SOURCE number=1] Petrov A.V. Title. Moscow, 2023.
```

References must be represented in the AST so the validator can check required references to tables, figures, formulas, and sources.

### Appendices and page breaks

```text
[PAGE_BREAK]
[APPENDIX id=app:a title="Исходные данные"]
```

Appendix numbering must be profile-aware.

## Escaping and literal text

The syntax must define an escape rule for text that starts with `[`. A literal block is required:

```text
[RAW]
[This line is not a marker]
[RAW_END]
```

## Diagnostics

The parser must detect and report:

- Cyrillic lookalike letters inside markers;
- unknown marker names;
- duplicate IDs;
- missing required block endings;
- malformed attributes;
- invalid table shape;
- image paths outside the allowed asset roots;
- unsupported syntax version.
