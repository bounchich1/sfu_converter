# STU 7.5-07 Implementation Gaps

This document no longer maintains per-rule implementation status by hand.
The source of truth is the generated coverage matrix:

- [SFU standard coverage matrix](sfu-standard-coverage-matrix.md)
- Rule metadata: `src/sfu_converter/registry/rules.py`
- Profile membership: `src/sfu_converter/registry/profiles.py`
- Source requirements: `docs/formatting requirements/`

## Refresh

```bash
python -m sfu_converter export-coverage --format md > docs/sfu-standard-coverage-matrix.md
```

CI and local quality gates should treat a matrix diff as a documentation drift
signal.

## Human Notes

The matrix captures rule IDs, profile membership, source documents, source
sections, parser support, renderer status, validator status, and test markers.
It does not replace human review for:

- visual fidelity of title-page forms, framed sheets, drawings, posters, and
  slide outputs;
- standard rationale and implementation priority;
- external GOST/STU interpretation where the registry rule is intentionally
  narrower than the source text;
- UX and operational choices for CLI workflows.

## Current Priority Order

1. Keep adding profile fixtures that exercise complete documents end to end.
2. Add exact visual/structural checks for title pages and framed sheets.
3. Expand parser metadata when new syntax blocks are introduced, so matrix
   parser-support status stays meaningful.
4. Add test markers for each newly implemented rule in the module that proves
   the behavior.
5. Regenerate the matrix whenever rule status, profile membership, or source
   traceability changes.
