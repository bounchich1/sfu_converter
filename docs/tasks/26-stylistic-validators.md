# Task 26: Implement §7.3 Stylistic Validators (Abbreviation Introduction, Heading Abbreviations, Unit Consistency)

## Priority: Medium
## Phase: Phase 5 (Validator)
## Standard reference
- PDF §7.3 (p. 14–18): abbreviations must be introduced at first use
  (`информационно-аналитический комплекс (ИАК)`); abbreviations are
  forbidden in headings and in figure / table captions; physical units
  must follow ГОСТ 8.417 (consistent unit per quantity throughout).
- Audit *7.3 Изложение текста* — fully MISSING.

## Affected files
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/application/style_check.py` *(new)*
- `src/sfu_converter/application/units.py` *(new)*
- `src/sfu_converter/registry/rules.py`
- `tests/test_style_check.py` *(new)*
- `tests/test_units.py` *(new)*
- `tests/test_docx_validator.py`

## Current state

There is no stylistic validator beyond paragraph alignment / indent. None
of the §7.3 rules are checked.

## Implementation

1. `application/style_check.py`:
   - `find_abbreviations(blocks) -> list[(short, long, span)]`: matches
     `<long> (<SHORT>)` regex, where `<SHORT>` is two or more uppercase
     letters; reports the introduction site.
   - For every later occurrence of `<SHORT>` without a preceding
     introduction, emit `STYLE_ABBREVIATION_NOT_INTRODUCED`.
   - For every `<SHORT>` that appears inside a `HeadingNode`,
     `TableCaptionNode`, `FigureCaptionNode`, or table/figure caption
     paragraph, emit `STYLE_ABBREVIATION_IN_HEADING`.
2. `application/units.py`:
   - Curate a small dictionary of common quantities → SI units consistent
     with ГОСТ 8.417 (mass → кг/г, time → с/мин/ч, frequency → Гц,
     pressure → Па/МПа, temperature → °C/К, energy → Дж/кВт·ч, length →
     м/мм, etc.).
   - Detect numeric tokens followed by units in body text. When the same
     quantity is expressed in two different units within the same
     paragraph or section, emit `STYLE_UNIT_INCONSISTENT`
     (`data.quantity`, `data.units`, `data.spans`).
3. Run the checks via the application layer for both `convert` and
   `lint`. Diagnostics include source spans.
4. Registry flips:
   - `common.style.abbreviation_introduction` → `IMPLEMENTED`
     (validator);
   - `common.style.no_abbreviations_in_headings` → `IMPLEMENTED`;
   - `common.style.unit_consistency` → `IMPLEMENTED`.

## Tests

- A document mentioning `ИАК` before any `(ИАК)` introduction produces
  `STYLE_ABBREVIATION_NOT_INTRODUCED` once for the first occurrence.
- A heading text `Описание ИАК и ЦОД` produces
  `STYLE_ABBREVIATION_IN_HEADING` referencing both abbreviations.
- A document mentioning `5 кг` and later `200 г` for the same labeled
  quantity (`mass`) triggers `STYLE_UNIT_INCONSISTENT` (case where the
  paragraph carries an explicit `quantity=mass` annotation).

## Verification

```bash
python -m pytest tests/test_style_check.py tests/test_units.py tests/test_docx_validator.py
```

## Notes / dependencies

- Abbreviation detection feeds Task 14 (auto-generated `СПИСОК
  СОКРАЩЕНИЙ`).
