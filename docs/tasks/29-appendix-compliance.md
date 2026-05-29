# Task 29: Implement Appendix Compliance (Auto-Letter, Continuation Labels, Sheet Formats, Independent-Document Appendix)

## Priority: High
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.11 (p. 26–28): appendices designated with Russian capital letters,
  skipping `Ё З Й О Ч Ь Ы Ъ`. Auto-letter assignment when omitted.
  Continuation labels `Продолжение приложения А` / `Окончание приложения
  А`. Sheet formats А3, А3×4, А4×4, А2, А1 permitted. Independent-document
  appendix has its own title page and continued page numbering. Section
  numbering inside appendix: `А.1`, `А.1.1`, `А.1.1.1`, `А.1.1.1.1`.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/appendix.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_appendix.py` *(new)*
- `tests/test_v1_parser.py`
- `tests/test_v2_parser.py`
- `tests/test_docx_validator.py`

## Current state

`AppendixNode` carries an explicit letter; rendering reorders nothing.
Auto-letter assignment, continuation labels, alternative sheet formats,
independent-document mode, and `А.1` numbering for internal sections are
MISSING. V2 parser does not preserve `letter`/`type` attributes onto
`AppendixNode`.

## Implementation

1. V2 parser must pass `letter`, `appendix_type` (`mandatory | recommended
   | reference`), and `subtitle` straight into `AppendixNode`. Fix the
   regression noted in the audit row "V2 parser preserves `letter`/`type`
   attributes on `AppendixNode` — MISSING".
2. Auto-letter helper: when `AppendixNode.letter is None`, assign the next
   Russian capital skipping `Ё З Й О Ч Ь Ы Ъ`. Emit
   `APPENDIX_AUTOLETTER_ASSIGNED` (info) so the author sees what landed.
3. Continuation logic: when an appendix renders across multiple Word
   pages, insert `Продолжение приложения А` above the second page and
   `Окончание приложения А` above the final page (only when ≥ 2 pages).
4. Sheet-format selection: V2 attribute `sheet=A3|A3x4|A4x4|A2|A1`.
   Renderer wraps each appendix in its own Word section (Task 24
   provides the section helper).
5. Internal section numbering: when the appendix is entered, Task 09's
   `NumberingContext.enter_appendix(letter)` redefines heading numbering
   so H1 → `А.1`, H2 → `А.1.1`, …, H4 → `А.1.1.1.1`.
6. Independent-document appendix: V2 attribute `independent=true` adds
   the per-appendix title page (re-uses the dispatcher from Task 10 with
   the appendix's own metadata block) and continues page numbering
   across the boundary (unlike Form А, which is suppressed).
7. Validator additions:
   - `common.appendix.auto_letter` confirms the rendered letter sequence;
   - `common.appendix.continuation_label` confirms the continuation
     headers;
   - `common.appendix.section_numbering` validates section numbers;
   - `common.appendix.in_text_reference` confirms appendices are
     referenced from body text (uses the graph from Task 20).
8. Flip the matching `*.renderer_status` and `*.validator_status` to
   `IMPLEMENTED`.

## Tests

- `[APPENDIX]` with no letter assigned after `Б` becomes `В`.
- Skip rule: after `Е` the next auto-letter is `Ж` (`Ё` is excluded).
- A 3-page appendix renders `Продолжение приложения А` and `Окончание
  приложения А` headers.
- H1 inside appendix `А` renders `А.1`; H4 renders `А.1.1.1.1`.
- `[APPENDIX letter=А independent=true]` renders its own title page and
  keeps page numbering monotonic across the boundary.
- An appendix never referenced in body triggers
  `common.appendix.in_text_reference`.

## Verification

```bash
python -m pytest tests/test_appendix.py tests/test_v1_parser.py \
                 tests/test_v2_parser.py tests/test_docx_validator.py
```

## Notes / dependencies

- Depends on Task 09 (numbering), Task 10 (title page dispatcher), Task
  20 (reference graph), Task 24 (sheet formats).
