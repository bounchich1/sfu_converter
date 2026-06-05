# Task 23: Validate Enumeration Lists (Dash, Lettered, Nested Numeric)

## Priority: Medium
## Phase: Phase 3/5 (Parser + validator)
## Standard reference
- PDF §7.4 (p. 18): three list styles — dash (`—`), lettered Russian
  (`а)`, `б)`, …) excluding `ё з й о ч ь ы ъ`, and nested numeric
  (`1)`, `2)`, …). Nested numeric lists indent +2 characters past their
  lettered parent.
- Audit *7.4 Деление текста* — lettered marker validation MISSING; nested
  preservation PARTIAL.

## Affected files
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/list_layout.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_list_layout.py` *(new)*
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

The parser recognises bullet, numbered and lettered lists. Lettered marker
generation already excludes the disallowed letters. Nested lists are
recognised by the renderer but the parser flattens nested structure;
validators do not check indentation or alphabetical order.

## Implementation

1. Extend `ListNode` to a recursive structure: `items: tuple[ListItemNode |
   ListNode, ...]` so lettered lists can carry nested numeric children.
2. Parser preserves nesting based on indent (V1) or explicit `level`
   attribute (V2 `[LIST type=lettered level=1]`).
3. Renderer applies hanging indent matching §7.4:
   - dash list: indent 1.25 cm, hanging 0.5 cm;
   - lettered list: indent 1.25 cm, hanging 0.5 cm, marker `а)`;
   - nested numeric inside lettered: extra +0.5 cm indent (=2 characters
     at TNR 14).
4. Validator additions:
   - `common.list.lettered`: all markers must be lower-case Russian
     letters in the alphabet `абвгдежиклмнпрстуфхцшщэюя` (no ё, з, й, о,
     ч, ь, ы, ъ);
   - `common.list.marker_alphabetical`: enforce ascending letter order;
     skipping a letter triggers `LIST_MARKER_OUT_OF_ORDER`;
   - `common.list.nested_numeric`: numeric children of lettered items
     must use `1)`, `2)`, … and indent +0.5 cm beyond the parent;
   - reject mixing `1.`, `1.1.` with `а)` markers within the same list.
5. Flip the matching registry rules to `IMPLEMENTED`.

## Tests

- Parsing
  ```
  - первый пункт
  - второй пункт
    1) подпункт один
    2) подпункт два
  ```
  yields a `ListNode(BULLET)` whose second item contains a nested
  `ListNode(NUMBERED)`.
- A lettered list using `и)` triggers `LIST_MARKER_DISALLOWED_LETTER`.
- `а)` followed by `в)` triggers `LIST_MARKER_OUT_OF_ORDER`.
- Nested `1)` indented less than +0.5 cm triggers
  `common.list.nested_numeric`.

## Verification

```bash
python -m pytest tests/test_list_layout.py tests/test_v1_parser.py \
                 tests/test_v2_parser.py tests/test_docx_renderer.py \
                 tests/test_docx_validator.py
```

## Notes / dependencies

- Independent of references; runs alongside Task 17 (formula explanation
  uses the same hanging-indent helpers).
