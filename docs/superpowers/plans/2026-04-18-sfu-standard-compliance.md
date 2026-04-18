# SFU Standard Compliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current line-based formatter into a standards-aware SFU report generator for unframed student reports, starting with the Appendix `М` profile.

**Architecture:** Replace direct line-to-DOCX rendering with a two-stage pipeline: parse source text into a document AST, then render through a profile-aware DOCX builder with a numbering pass. Keep validation separate and semantic so it can check structure, numbering, captions, and pagination rules instead of only paragraph styles.

**Tech Stack:** Python, `python-docx`, Pillow, pytest, Markdown documentation.

---

## File Map

### Existing files to modify

- `M:\sfu_converter-main\src\converter.py`
  - current line-based parsing and rendering
  - should be reduced to orchestration or replaced by smaller modules
- `M:\sfu_converter-main\src\config.py`
  - current global formatting constants
  - should evolve into profile-aware layout constants
- `M:\sfu_converter-main\src\validator.py`
  - current heuristic validator
  - should become semantic and structure-aware
- `M:\sfu_converter-main\src\main.py`
  - current entry point
- `M:\sfu_converter-main\src\menu.py`
  - current interactive menu
- `M:\sfu_converter-main\tests\test_converter.py`
  - needs path-contract fixes and real end-to-end tests
- `M:\sfu_converter-main\tests\test_validator.py`
  - needs semantic-validator coverage
- `M:\sfu_converter-main\README.md`
  - needs updated capabilities and usage docs

### New files to create

- `M:\sfu_converter-main\src\models.py`
  - AST and metadata models
- `M:\sfu_converter-main\src\parser.py`
  - converts source text into AST
- `M:\sfu_converter-main\src\profiles.py`
  - report types and their layout/structure rules
- `M:\sfu_converter-main\src\numbering.py`
  - numbering and cross-reference registry
- `M:\sfu_converter-main\src\renderer.py`
  - renders AST into DOCX
- `M:\sfu_converter-main\src\title_pages.py`
  - title-page generators, starting with Appendix `М`
- `M:\sfu_converter-main\src\citations.py`
  - bibliography and citation helpers
- `M:\sfu_converter-main\tests\test_parser.py`
  - parser tests
- `M:\sfu_converter-main\tests\test_profiles.py`
  - profile/title-page tests
- `M:\sfu_converter-main\tests\test_numbering.py`
  - numbering tests
- `M:\sfu_converter-main\tests\fixtures\`
  - stable sample inputs and expected behaviors

---

### Task 1: Fix The Public Conversion Contract

**Files:**
- Modify: `M:\sfu_converter-main\src\converter.py`
- Modify: `M:\sfu_converter-main\src\main.py`
- Modify: `M:\sfu_converter-main\src\menu.py`
- Test: `M:\sfu_converter-main\tests\test_converter.py`

- [ ] **Step 1: Write failing tests for path-agnostic conversion**

Add tests that call the converter with explicit input and output paths instead of assuming `examples/` and `results/`.

Expected test scenarios:
- convert a file from a temp directory
- save output to a temp directory
- keep compatibility with current menu-driven repo folders

- [ ] **Step 2: Run the focused test command**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_converter.py --basetemp=M:\sfu_converter-main\.tmp\pytest-contract
```

Expected:
- existing tests fail because the converter hardcodes repo directories

- [ ] **Step 3: Refactor the converter entry points**

Introduce an API like:

```python
def convert_file(
    self,
    input_file: Path,
    output_file: Path,
    template: str | None = None,
) -> str:
    ...
```

Keep a thin compatibility wrapper for menu usage.

- [ ] **Step 4: Re-run the focused tests**

Run the same command and confirm the contract tests pass.

- [ ] **Step 5: Update the menu layer**

Keep menu-specific path selection in `menu.py`, not in the core converter.

- [ ] **Step 6: Commit**

```powershell
git add src/converter.py src/main.py src/menu.py tests/test_converter.py
git commit -m "refactor: make conversion API path-agnostic"
```

### Task 2: Add A Semantic AST And Parser

**Files:**
- Create: `M:\sfu_converter-main\src\models.py`
- Create: `M:\sfu_converter-main\src\parser.py`
- Modify: `M:\sfu_converter-main\src\converter.py`
- Test: `M:\sfu_converter-main\tests\test_parser.py`

- [ ] **Step 1: Write parser tests first**

Cover:
- heading parsing
- paragraphs
- figures with and without image files
- tables with captions
- structural markers and metadata blocks if added

- [ ] **Step 2: Run parser tests and verify failure**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_parser.py --basetemp=M:\sfu_converter-main\.tmp\pytest-parser
```

Expected:
- failure because parser modules do not exist yet

- [ ] **Step 3: Define AST models**

Add small focused models such as:

```python
@dataclass
class ParagraphBlock:
    text: str

@dataclass
class HeadingBlock:
    level: int
    text: str

@dataclass
class FigureBlock:
    image_path: str | None
    caption: str | None

@dataclass
class TableBlock:
    caption: str | None
    rows: list[list[str]]
```

- [ ] **Step 4: Implement the parser**

Convert raw text lines into a list of AST blocks instead of writing DOCX immediately.

- [ ] **Step 5: Rewire `converter.py` to use the parser**

`converter.py` should orchestrate:
- read input
- parse to AST
- pass AST to renderer

- [ ] **Step 6: Re-run parser tests**

Run the command from Step 2 and confirm green results.

- [ ] **Step 7: Commit**

```powershell
git add src/models.py src/parser.py src/converter.py tests/test_parser.py
git commit -m "feat: add semantic document parser"
```

### Task 3: Introduce Report Profiles

**Files:**
- Create: `M:\sfu_converter-main\src\profiles.py`
- Modify: `M:\sfu_converter-main\src\config.py`
- Modify: `M:\sfu_converter-main\src\converter.py`
- Test: `M:\sfu_converter-main\tests\test_profiles.py`

- [ ] **Step 1: Write tests for profile selection**

Cover:
- default unframed report profile
- Appendix `М` lab/practical/project profile
- invalid profile selection

- [ ] **Step 2: Run the profile tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_profiles.py --basetemp=M:\sfu_converter-main\.tmp\pytest-profiles
```

Expected:
- failure because profile logic is not implemented

- [ ] **Step 3: Create profile definitions**

Profile objects should define:
- margin rules
- page-number rules
- required structural elements
- title-page generator
- numbering mode

- [ ] **Step 4: Move raw constants behind profile accessors**

Instead of one global config, use profile-aware settings.

- [ ] **Step 5: Re-run the profile tests**

Confirm the profile tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/profiles.py src/config.py src/converter.py tests/test_profiles.py
git commit -m "feat: add document profiles for SFU report types"
```

### Task 4: Implement Title Pages And Structural Elements

**Files:**
- Create: `M:\sfu_converter-main\src\title_pages.py`
- Create: `M:\sfu_converter-main\src\renderer.py`
- Modify: `M:\sfu_converter-main\src\converter.py`
- Test: `M:\sfu_converter-main\tests\test_converter.py`

- [ ] **Step 1: Add failing tests for Appendix `М` title-page generation**

Test:
- required fields are rendered
- title page is first
- title page is included in pagination but has no visible number
- structural elements start on new pages

- [ ] **Step 2: Run the title-page tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_converter.py -k title --basetemp=M:\sfu_converter-main\.tmp\pytest-title
```

Expected:
- failure because title-page generation does not exist

- [ ] **Step 3: Create the title-page builder**

Start with Appendix `М` only:
- university name
- institute
- department
- document type
- theme
- teacher block
- student block
- city and year

- [ ] **Step 4: Add structural-element rendering**

Add explicit handling for:
- title page
- contents heading
- introduction
- conclusion
- bibliography heading
- appendices heading

- [ ] **Step 5: Re-run focused tests**

Confirm the new title/structure tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/title_pages.py src/renderer.py src/converter.py tests/test_converter.py
git commit -m "feat: generate SFU structural elements and title page"
```

### Task 5: Add Numbering And Reference Registry

**Files:**
- Create: `M:\sfu_converter-main\src\numbering.py`
- Modify: `M:\sfu_converter-main\src\models.py`
- Modify: `M:\sfu_converter-main\src\renderer.py`
- Test: `M:\sfu_converter-main\tests\test_numbering.py`

- [ ] **Step 1: Write failing numbering tests**

Cover:
- section numbering
- subsection numbering
- figure numbering
- table numbering
- appendix-prefixed numbering

- [ ] **Step 2: Run the numbering test file**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_numbering.py --basetemp=M:\sfu_converter-main\.tmp\pytest-numbering
```

Expected:
- failure because numbering module does not exist

- [ ] **Step 3: Implement a numbering pass**

Suggested public shape:

```python
class NumberingRegistry:
    def assign(self, document: DocumentModel) -> DocumentModel:
        ...
```

Responsibilities:
- assign display numbers
- track per-section counters
- switch to appendix counters when appendices begin

- [ ] **Step 4: Update rendering to use assigned numbers**

Render captions and headings from numbered AST nodes, not from raw user text alone.

- [ ] **Step 5: Re-run numbering tests**

Confirm numbering expectations pass.

- [ ] **Step 6: Commit**

```powershell
git add src/numbering.py src/models.py src/renderer.py tests/test_numbering.py
git commit -m "feat: add numbering for sections tables and figures"
```

### Task 6: Upgrade Tables And Figures To Standard-Level Behavior

**Files:**
- Modify: `M:\sfu_converter-main\src\renderer.py`
- Modify: `M:\sfu_converter-main\src\utils_image_insert.py`
- Modify: `M:\sfu_converter-main\src\config.py`
- Test: `M:\sfu_converter-main\tests\test_converter.py`

- [ ] **Step 1: Add failing tests for table and figure formatting**

Cover:
- left-aligned table caption above table
- reduced table font size `10-12 pt`
- centered bold table header
- figure caption below image
- missing-image behavior that does not silently corrupt numbering

- [ ] **Step 2: Run focused figure/table tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_converter.py -k "table or image or figure" --basetemp=M:\sfu_converter-main\.tmp\pytest-objects
```

Expected:
- failures or weak assertions in current behavior

- [ ] **Step 3: Implement renderer improvements**

Required upgrades:
- table caption numbering from registry
- table font size override
- figure caption numbering from registry
- reserved place for explanatory text blocks
- clear continuation hook points for future multi-page support

- [ ] **Step 4: Re-run focused tests**

Confirm the figure/table tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/renderer.py src/utils_image_insert.py src/config.py tests/test_converter.py
git commit -m "feat: align table and figure rendering with SFU rules"
```

### Task 7: Add Bibliography, Appendices, And Formula Support

**Files:**
- Create: `M:\sfu_converter-main\src\citations.py`
- Modify: `M:\sfu_converter-main\src\models.py`
- Modify: `M:\sfu_converter-main\src\parser.py`
- Modify: `M:\sfu_converter-main\src\renderer.py`
- Test: `M:\sfu_converter-main\tests\test_parser.py`
- Test: `M:\sfu_converter-main\tests\test_converter.py`

- [ ] **Step 1: Write failing tests for bibliography, appendices, and formulas**

Cover:
- source list heading before appendices
- numbered bibliography entries
- appendix page starts
- appendix numbering such as `А.1`
- formula block spacing and numbering

- [ ] **Step 2: Run the relevant tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_parser.py tests/test_converter.py -k "bibliography or appendix or formula" --basetemp=M:\sfu_converter-main\.tmp\pytest-domains
```

Expected:
- failures because these domains are missing

- [ ] **Step 3: Extend the source format and AST**

Add explicit block types for:
- bibliography list
- appendix
- formula

- [ ] **Step 4: Implement rendering**

Requirements:
- bibliography appears before appendices
- appendices start on a new page
- formula blocks render with spacing and numbering hooks

- [ ] **Step 5: Re-run the domain tests**

Confirm the new tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/citations.py src/models.py src/parser.py src/renderer.py tests/test_parser.py tests/test_converter.py
git commit -m "feat: add bibliography appendices and formulas"
```

### Task 8: Replace The Heuristic Validator

**Files:**
- Modify: `M:\sfu_converter-main\src\validator.py`
- Modify: `M:\sfu_converter-main\src\converter.py`
- Modify: `M:\sfu_converter-main\tests\test_validator.py`

- [ ] **Step 1: Write failing semantic-validator tests**

Cover:
- H2/H3 are not treated as normal body paragraphs
- numbered captions are validated
- bibliography placement is validated
- appendix numbering is validated
- page-number presence is validated where possible

- [ ] **Step 2: Run validator tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_validator.py --basetemp=M:\sfu_converter-main\.tmp\pytest-validator
```

Expected:
- current validator either misses required checks or reports false negatives

- [ ] **Step 3: Refactor validator inputs**

Validator should inspect:
- semantic tags from the AST or rendered metadata
- paragraph style plus numbering expectations
- document order rules

- [ ] **Step 4: Re-run validator tests**

Confirm the validator tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/validator.py src/converter.py tests/test_validator.py
git commit -m "refactor: make validator semantic and standards-aware"
```

### Task 9: Final Integration, Docs, And Full Verification

**Files:**
- Modify: `M:\sfu_converter-main\README.md`
- Modify: `M:\sfu_converter-main\docs\sfu-standard-audit.md`
- Modify: `M:\sfu_converter-main\examples\`
- Test: full test suite

- [ ] **Step 1: Update README and usage docs**

Document:
- supported profiles
- source syntax
- current limitations
- validation workflow

- [ ] **Step 2: Fix or replace broken example assets**

Ensure example inputs only reference files that actually exist.

- [ ] **Step 3: Run the full suite**

Run:

```powershell
.venv\Scripts\python.exe -m pytest -q tests --basetemp=M:\sfu_converter-main\.tmp\pytest-full
```

Expected:
- all tests pass

- [ ] **Step 4: Generate a sample Appendix `М` report and validate it**

Run the converter on a canonical sample and then run the validator on the output.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs examples src tests
git commit -m "docs: finalize SFU compliance roadmap and usage"
```

---

## Spec Coverage Check

Covered by the plan:
- unframed page layout rules
- structural elements
- title-page generation for Appendix `М`
- numbering rules for sections, tables, figures, appendices
- figure and table caption handling
- bibliography placement and numbering
- appendix handling
- formula support
- semantic validation

Intentionally deferred:
- framed explanatory-note layouts with engineering title blocks
- advanced multi-page table/figure continuation labels in full depth
- full GOST bibliography formatting breadth across all source types
- slide/poster/graphic-material generation

These deferred items should be planned as a follow-on phase after Appendix `М` unframed reports are stable.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-18-sfu-standard-compliance.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, with review between tasks
2. Inline Execution - execute tasks in this session in batches with checkpoints

Which approach?
