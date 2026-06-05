# PDF vs Converter Implementation

Detailed per-rule status is generated from the registry in:

- [SFU standard coverage matrix](sfu-standard-coverage-matrix.md)

The previous hand-maintained table was removed because it drifted from the
registry after profile expansion and validator work. Use this file only for
manual audit context that the matrix cannot infer from code.

## Source Material

- `docs/sfu-stu-7.5-07.pdf`
- `docs/sfu-stu-7.5-07-291121-s-podp.-ot-03.07.2024.doc`
- extracted requirement notes in `docs/formatting requirements/`

## Manual Audit Scope

The generated matrix answers:

- which rules exist;
- which profiles include each rule;
- which source document and heading each rule references;
- parser, renderer, and validator support status;
- which test modules carry rule markers.

Manual PDF review is still required for:

- whether a registry rule fully captures the source standard text;
- whether a generated DOCX visually matches appendix forms and framed sheets;
- whether external GOST references need separate implementation tasks;
- whether a `partial` or `implemented` status should be downgraded after a
  stricter interpretation of the PDF.

## Refresh

```bash
python -m sfu_converter export-coverage --format md > docs/sfu-standard-coverage-matrix.md
```

After refreshing, review the matrix diff together with any registry changes.
