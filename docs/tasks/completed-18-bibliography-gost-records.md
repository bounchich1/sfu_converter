# Task 18: Implement GOST R 7.0.100/7.80 Bibliography Records and Grouping

## Priority: High
## Phase: Phase 5 (Renderer + validator)
## Standard reference
- PDF §7.10 (p. 27): bibliography format per ГОСТ Р 7.0.100 / 7.80,
  abbreviations per ГОСТ 7.11 / Р 7.0.12, single grouping method
  (alphabetical, systematic, or chronological), Russian entries first
  followed by foreign-language entries alphabetically.
- PDF Приложение У (p. 58–60): record templates for normative documents,
  patents, books (1/2/3/4 authors), volumes, dissertations, electronic
  resources, journal articles.
- Audit *7.10 Список использованных источников* — every record validation,
  grouping, and template item is MISSING.

## Affected files
- `src/sfu_converter/domain/ast_nodes.py`
- `src/sfu_converter/parser/v1_parser.py`
- `src/sfu_converter/parser/v2_parser.py`
- `src/sfu_converter/parser/attributes.py`
- `src/sfu_converter/infrastructure/bibliography.py` *(new)*
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/registry/rules.py`
- `tests/test_bibliography.py` *(new)*
- `tests/test_v2_parser.py`
- `tests/test_docx_renderer.py`
- `tests/test_docx_validator.py`

## Current state

`BibliographyEntryNode` carries `number` and free-form `text`. The renderer
formats them as a numbered, justified, indented paragraph. There is no
record-type model, no record-level validation, no grouping enforcement, no
language ordering check.

## Implementation

1. Add a record-type enum and dataclasses in `domain/ast_nodes.py`:

   ```python
   class SourceRecordType(Enum):
       NORMATIVE = auto()
       PATENT = auto()
       BOOK_ONE_AUTHOR = auto()
       BOOK_TWO_AUTHORS = auto()
       BOOK_THREE_AUTHORS = auto()
       BOOK_FOUR_PLUS_AUTHORS = auto()
       VOLUME = auto()
       DISSERTATION = auto()
       ELECTRONIC = auto()
       ARTICLE = auto()

   @dataclass(frozen=True)
   class SourceRecordNode:
       number: int
       record_type: SourceRecordType
       fields: Mapping[str, str]
       language: str  # "ru", "en", ...
   ```

2. V2 parser supports
   `[SOURCE number=1 type=book_two_authors lang=ru]
       authors="Иванов И. И., Петров П. П."
       title="Анализ данных"
       city="Красноярск" publisher="СФУ" year=2023 pages=320
   [/SOURCE]`
   plus the legacy `[SOURCE number=N]` shorthand for free-text entries
   (creates a `BibliographyEntryNode` for backward compatibility).
3. `bibliography.format_record(record)` produces a single string per
   ГОСТ Р 7.0.100 layout. Ten formatters (one per type) live alongside it.
4. Renderer composes the bibliography section:
   - apply selected grouping method from
     `common.bibliography.grouping_method` (default: alphabetical);
   - emit `common.bibliography.russian_first` warning when language
     ordering is violated;
   - emit each record as a numbered paragraph styled
     `SFUBibliographyEntry`.
5. Validator checks:
   - record-level: required fields per record type (e.g. PATENT requires
     `country`, `number`, `title`, `mki`, `applicant`, `applied_date`,
     `published_date`);
   - missing or wrongly-ordered separators (space-em-dash-space, slashes,
     colons in titles per ГОСТ);
   - mixed grouping methods → `common.bibliography.grouping_method`
     warning citing both detected methods;
   - language ordering → `common.bibliography.russian_first`.
6. Flip:
   - `common.bibliography.gost_record` → `IMPLEMENTED`,
   - `common.bibliography.gost_abbreviations` → `IMPLEMENTED`,
   - `common.bibliography.grouping_method` → `IMPLEMENTED`,
   - `common.bibliography.russian_first` → `IMPLEMENTED`.

## Tests

- A `BOOK_TWO_AUTHORS` record renders as
  `Иванов, И. И. Анализ данных / И. И. Иванов, П. П. Петров. — Красноярск:
  СФУ, 2023. — 320 с.`
- A `PATENT` record missing `applicant` produces a diagnostic listing the
  missing field.
- A bibliography mixing alphabetical and chronological grouping produces a
  single warning with both methods named.
- An English entry placed before a Russian one produces
  `common.bibliography.russian_first`.

## Verification

```bash
python -m pytest tests/test_bibliography.py tests/test_v2_parser.py \
                 tests/test_docx_renderer.py tests/test_docx_validator.py
```

## Notes / dependencies

- Pair with Task 20 (reference graph). Records expose their numbers so
  `[N]` references resolve to a known record type.
