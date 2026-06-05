# Task 19: Implement Footnote References (Subscript, Separator Line, Smaller Font)

## Priority: Medium
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.9 (p. 26–27): footnote references use a superscript marker, a
  separator line, and a smaller font for the footnote text.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_footnotes.py` *(new)*
- `tests/test_docx_renderer.py`
- `tests/test_v2_parser.py`

## Current state

There is no footnote node, no parser support, no renderer output for
footnotes. Style checks are absent.

## Implementation

1. Add `FootnoteNode(marker, text, source)` and `FootnoteAnchor(marker)` to
   the AST. `FootnoteAnchor` lives inside body text runs.
2. V2 syntax: inline `[FN id=1 text="Описание"]` produces an anchor and
   queues the matching footnote on the same page. Authors may also write
   the explicit pair `[FN_ANCHOR id=1]` and `[FN_BODY id=1] text [/FN_BODY]`
   when finer placement is needed.
3. `python-docx` does not expose footnotes via its high-level API. Provide
   a small XML helper in `infrastructure/footnotes.py` that:
   - registers `word/footnotes.xml` if absent (using a frozen template);
   - inserts a `<w:footnoteReference>` run inside the anchor paragraph;
   - appends a `<w:footnote>` element to `footnotes.xml` with the required
     content and a 12 pt body, single line spacing.
4. Renderer wires the helper. Anchor markers are superscript via a custom
   `SFUFootnoteAnchor` character style.
5. Validator confirms:
   - footnote text is 12 pt or smaller and single line spacing;
   - separator line is the default (do not override it);
   - every anchor matches a footnote and vice versa.
6. Add registry records and flip
   `common.reference.footnote.renderer_status=IMPLEMENTED`/
   `validator_status=IMPLEMENTED`.

## Tests

- A document with `[FN id=1 text="Источник"]` produces a superscript `1`
  in the body and a `<w:footnote>` element.
- Two anchors referencing the same `id` produce diagnostics
  `FOOTNOTE_DUPLICATE`.
- Footnote text rendered at 16 pt produces
  `common.reference.footnote` validator diagnostic.

## Verification

```bash
python -m pytest tests/test_footnotes.py tests/test_docx_renderer.py tests/test_v2_parser.py
```

## Notes / dependencies

- Independent of bibliography GOST records (Task 18).
