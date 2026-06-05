# Task 25: Implement Project Designation Codes (Letter-Numeric Format and Code Dictionary)

## Priority: High (required for ДП/КП)
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §9 (p. 29–30): letter-numeric designation `ДП-23.05.02 ХХХХХХ.ХХХ СБ`
  per ГОСТ 2.201, optional year insertion `ДП-23.05.02-2021 …`, or
  `ДП-08.05.01 ПЗ` per ГОСТ Р 21.101. The code is placed in graph 2 of
  every sheet's main inscription.
- PDF Приложение Х (p. 61): document-code dictionary
  (`ПЗ, РР, ПМ, И, Д, ВС, ВП, ТБ, ТУ, СБ, ВО, ТЧ, ГЧ, МЭ, МЧ, УЧ, МК, КТП,
  ОК, ВОБ, ВМ, С, ЛС, ТХ, ГП, ГТ, АР, АС, АИ, КЖ, КМ, КМД, КД, ВК, ОВ, ТМ,
  ГСВ, ГР, НВ, НК, ТС, АД, ТР`) plus schema codes `Э / Г / П / К / В / Л /
  Р / Е / С` and type numbers `1-7` and `0`.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/attributes.py`
- `src/sfu_converter/infrastructure/main_inscription.py`
- `src/sfu_converter/infrastructure/project_designation.py` *(new)*
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_project_designation.py` *(new)*
- `tests/test_v2_parser.py`
- `tests/test_docx_validator.py`

## Current state

The registry has stub rules for project designations but no parser, no
validator, no renderer integration.

## Implementation

1. Add `ProjectDesignationNode(prefix, specialty_code, group_code,
   document_code, year=None, schema_code=None, schema_type=None)`. The
   metadata block of the document may carry one designation; framed
   sections also accept their own `[DESIGNATION ...]` element.
2. V2 syntax:
   ```
   [DESIGNATION prefix=ДП specialty=23.05.02 group=ХХХХХХ.ХХХ
                document=СБ year=2021]
   ```
3. `project_designation.format(node)` produces the canonical string:
   - GOST 2.201: `<prefix>-<specialty> <group> <document>` with optional
     `-<year>` after `<specialty>`.
   - GOST R 21.101: `<prefix>-<specialty> <document>` (no group code).
4. Code dictionary stored as `CODE_DICTIONARY: dict[str, str]` mapping
   `ПЗ → "Пояснительная записка"`, etc. Validator uses it to:
   - reject unknown `document` codes;
   - reject unknown schema codes/types;
   - confirm `year` (if present) is four digits and within
     `[1900, current_year + 1]`.
5. Renderer: when a section's main inscription is rendered (Task 24), pass
   the formatted designation into graph 2.
6. Validator additions:
   - `project_designations.code.format`: regex check on the assembled
     string;
   - `project_designations.code.dictionary`: code must be in the
     dictionary;
   - `project_designations.letter_numeric_designation`: presence of the
     designation in graph 2 of every sheet of a ДП/КП.
7. Flip:
   - `project_designations.code.format` → `IMPLEMENTED`,
   - `project_designations.code.dictionary` → `IMPLEMENTED`,
   - `project_designations.letter_numeric_designation` → `IMPLEMENTED`.

## Tests

- `[DESIGNATION prefix=ДП specialty=23.05.02 group=ABCDEF.001 document=СБ
   year=2021]` formats as `ДП-23.05.02-2021 ABCDEF.001 СБ`.
- `document=ZZ` produces a code-dictionary diagnostic listing the closest
  matches.
- A coursework profile without any `ProjectDesignationNode` produces
  `project_designations.letter_numeric_designation` warning.
- Year `1899` triggers the year range diagnostic.
- Schema code `Х5` (unknown letter) triggers schema diagnostic.

## Verification

```bash
python -m pytest tests/test_project_designation.py tests/test_v2_parser.py \
                 tests/test_docx_validator.py
```

## Notes / dependencies

- Pair with Task 24 (frame + main inscription).
