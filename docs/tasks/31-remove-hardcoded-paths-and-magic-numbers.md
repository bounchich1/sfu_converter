# Task 31: Remove Hard-Coded Paths and Magic Numbers; Centralise Constants

## Priority: Medium
## Phase: Phase 7 (Hygiene)
## Standard reference
- Internal hygiene only — backed by the audit's *Suggested implementation
  order* §12 ("special structural blocks" — keeping constants and
  metadata sources in one place keeps future profile additions sane).

## Affected files
- `src/sfu_converter/config.py`
- `src/sfu_converter/converter.py`
- `src/sfu_converter/infrastructure/docx_renderer.py`
- `src/sfu_converter/infrastructure/docx_validator.py`
- `src/sfu_converter/infrastructure/title_pages/*.py`
- `src/sfu_converter/registry/loader.py`
- `tests/test_dry_configuration.py`
- `tests/test_config.py`

## Current state

`converter.py:108` references `get_profile("common")` as a literal string.
Strings such as `"ПРИЛОЖЕНИЕ"`, em dashes used in `Таблица N — Name`,
`Рисунок N — Name`, tab-stop positions for formula numbers (16.5 cm), the
list of excluded Russian letters, the structural section names, the city
defaults, etc. live in several places.

## Implementation

1. Move every literal that appears in more than one file into
   `domain/constants.py`. At minimum:
   - structural section titles (already in `StructuralSectionType` — keep
     the enum as the single source of truth);
   - excluded appendix letters (single set: `("Ё", "З", "Й", "О", "Ч",
     "Ь", "Ы", "Ъ")`);
   - punctuation: `EM_DASH = "—"`, `EN_DASH = "–"`;
   - default city/year placeholders;
   - default profile name (`"common"`);
   - tab-stop positions and indents (read from `common.formula.body`
     parameters instead of hard-coded `Cm(16.5)`).
2. Replace direct string literals in renderer / validator / title-page
   modules with constants or rule lookups.
3. Update `tests/test_dry_configuration.py` to grep for the forbidden
   patterns and assert they only occur inside `domain/constants.py` or the
   rule registry.
4. Add a `tests/test_no_magic_numbers.py` (small) that walks the source
   files via AST and rejects raw `Cm(<float>)` calls outside of
   `infrastructure/section_setup.py` and constants module.

## Tests

- AST scan finds no `Cm(0.5)` style literals outside the whitelisted
  modules.
- `domain/constants.EXCLUDED_APPENDIX_LETTERS` matches the auto-letter
  helper from Task 29.
- Removing `"common"` from `converter.py` does not regress existing
  tests once Task 01 is in place.

## Verification

```bash
python -m pytest tests/test_dry_configuration.py tests/test_no_magic_numbers.py
```

## Notes / dependencies

- Should land after Task 01 (profile plumbing) so the `"common"`
  reference can be dropped without breaking dispatch.
