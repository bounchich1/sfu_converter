# SFU Standard Audit And Project Assessment

## Scope

This document summarizes the high-signal requirements from `sfu-stu-7.5-07.pdf` and compares them with the current state of the converter in this repository.

Sources used:
- `C:\Users\ilya7\Downloads\sfu-stu-7.5-07.pdf`
- `src/config.py`
- `src/converter.py`
- `src/utils_image_insert.py`
- `src/validator.py`
- `src/main.py`
- `src/menu.py`
- `README.md`
- `tests/`

The focus is the text-document portion of the standard, not the full graphic-material section for engineering drawings and posters.

---

## Essential Rules From `СТУ 7.5-07-2021`

### 1. Document structure

Key rules from the PDF:
- Typical text documents may contain: title page, abstract, contents, introduction, main part, conclusion, list of abbreviations, list of used sources, appendices.
- The title page and main part are mandatory.
- Other structural elements depend on the document type and assignment.
- Each structural element starts on a new page.
- Structural-element headings such as `СОДЕРЖАНИЕ`, `ВВЕДЕНИЕ`, `ЗАКЛЮЧЕНИЕ`, `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ`, `ПРИЛОЖЕНИЕ` are centered, uppercase, bold, without numbering, and separated from following text by one blank line.

High-impact consequence for the project:
- The converter must understand document-level structure, not only paragraph styling.

### 2. General page layout for unframed reports

Key rules from the PDF:
- A4, one-sided printing.
- Font: `Times New Roman`, size `14 pt`.
- Line spacing: single or `1.5`.
- First-line indent: `12.5 mm`.
- Alignment: justified.
- Margins for standard unframed student reports:
  - left: `30 mm`
  - top: `20 mm`
  - bottom: `20 mm`
  - right: `10 mm`
- For landscape pages:
  - left/right: `20 mm`
  - top: `30 mm`
  - bottom: `10 mm`

High-impact consequence for the project:
- The converter already approximates the common unframed portrait layout, but it does not distinguish portrait and landscape rules or framed-document rules.

### 3. Pagination

Key rules from the PDF:
- Page numbering is continuous across the whole document.
- The title page is included in the page count but does not display a page number.
- For unframed pages, the page number is centered at the bottom and uses `Times New Roman 14 pt`.

High-impact consequence for the project:
- This is a document-level requirement and cannot be solved only by paragraph formatting.

### 4. Heading hierarchy and numbering

Key rules from the PDF:
- Main body text is divided into sections, subsections, points, and subpoints.
- Numbering pattern:
  - section: `1`
  - subsection: `1.1`
  - point: `1.1.1`
  - subpoint: `1.1.1.1`
- Headings are bold, without trailing periods, without hyphenation, and separated from body text by one blank line.
- Lists use:
  - hyphens for simple lists
  - lowercase letters with `)` when referenced in text
  - digits with `)` for deeper nesting

High-impact consequence for the project:
- The current marker system supports three heading styles but does not implement section numbering, nested list rules, or formal distinction between section/subsection/point semantics.

### 5. Tables

Key rules from the PDF:
- Tables are placed after the first reference or on the next page.
- Caption format: `Таблица <номер> - <наименование>`.
- Caption is placed above the table, aligned from the left, without paragraph indent.
- Table numbering may be continuous or within a section.
- Appendix tables use appendix-prefixed numbering such as `Таблица А.1`.
- Table headers use bold text and centered alignment.
- Tables may continue across pages with `Продолжение таблицы ...` and `Окончание таблицы ...`.
- Recommended table font size: `10-12 pt Times New Roman`.
- If all values are in one unit, the unit can be written above the table on the right.
- Table footnotes are allowed.

High-impact consequence for the project:
- The current implementation only covers simple single-page grid tables with a caption.

### 6. Figures and illustrations

Key rules from the PDF:
- Figures are placed after the first reference or on the next page.
- The figure must be readable and centered within the printable area.
- The caption is below the image and uses the form `Рисунок <номер> - <наименование>`.
- Explanatory data, if present, is placed above the caption.
- Multi-page figures have sheet numbering such as `Рисунок 1, лист 2`.
- Appendix figures use numbering such as `Рисунок А.1`.

High-impact consequence for the project:
- The current implementation supports manual image insertion and manual captions but not numbering, references, appendix logic, or multi-page handling.

### 7. Formulas

Key rules from the PDF:
- Each formula is on its own line with one blank line above and below.
- Formula numbering is placed at the right in parentheses.
- Appendix formulas use appendix-prefixed numbering such as `(А.1)`.
- Symbol explanations are placed immediately below the formula and start with `где` without a colon.

High-impact consequence for the project:
- There is no formula support in the current converter.

### 8. Citations and bibliography

Key rules from the PDF:
- Bibliographic references must follow GOST.
- Allowed citation modes:
  - inline bibliographic reference
  - footnote reference
  - numbered source-list reference in square brackets such as `[13]` or `[20, с. 29]`
- The source list goes before appendices.
- Entries are numbered and use a consistent ordering strategy:
  - alphabetic
  - thematic
  - chronological

High-impact consequence for the project:
- The current converter treats bibliography as plain paragraphs and does not provide citation or bibliography logic.

### 9. Appendices

Key rules from the PDF:
- Appendices are placed at the end of the document.
- Each appendix starts on a new page.
- Appendices are lettered using Russian letters, with exclusions defined by the standard.
- Each appendix has its own title.
- Appendices may contain their own section numbering.
- Appendix pages belong to the same continuous document pagination.

High-impact consequence for the project:
- Appendix support is currently absent as a first-class feature.

### 10. Report-type-specific title pages

Key rules from the PDF:
- The standard includes mandatory title-page templates in appendices for specific document types.
- Appendix `М` defines the title page for lab reports, practical reports, and project-completion reports.

High-impact consequence for the project:
- Template selection cannot remain optional and manual if the goal is real standard compliance.

---

## Current Project State

### Current architecture

The repository currently consists of:
- `src/converter.py`: a line-based parser plus DOCX writer.
- `src/config.py`: formatting constants.
- `src/utils_image_insert.py`: image preprocessing and insertion helpers.
- `src/validator.py`: a simple validator for a few formatting rules.
- `src/menu.py` and `src/main.py`: interactive CLI entry point.
- `templates/`: manual `.docx` templates.
- `examples/`: source `.txt` inputs.

### Current input format

Supported markers:
- `[H1]`
- `[H2]`
- `[H3]`
- `[IMAGE]`
- `[IMAGE=<filename>]`
- `[TABLE_START]`
- `[TABLE_CAPTION]`
- `[TABLE_END]`

Current content model:
- everything is processed as a flat stream of lines
- there is no typed document AST
- there is no document profile for report type

### Current output model

The converter:
- loads a template if one is explicitly chosen
- otherwise creates a blank document
- applies base margins
- adds paragraphs, images, and simple tables in order

The project is therefore a formatting helper, not yet a standards-aware document generator.

---

## What Is Implemented

### Implemented well enough for basic reports

- Base font setup for normal text: `Times New Roman 14`.
- Justified body paragraphs.
- First-line indent close to the required `12.5 mm`.
- Basic H1/H2/H3 paragraph styling.
- Left/right/top/bottom margin setup for the common unframed portrait case.
- Image insertion with centering and optional caption below.
- Table creation from pipe-delimited rows.
- Table captions placed above tables.
- Optional use of a prepared DOCX template.
- Interactive batch conversion through the console menu.

### Implemented partially

- Validation exists, but checks only a narrow subset of formatting.
- Image handling is operational, but depends on input examples actually having matching files in `images/`.
- The template mechanism can produce title pages, but only if the template already contains the right content and layout.
- Table styling approximates the standard but does not implement continuation rules or reduced font sizes.

---

## What Is Not Implemented

### Missing document semantics

- No representation of structural elements as first-class document nodes.
- No awareness of document type:
  - lab report
  - practical report
  - course work
  - thesis
  - explanatory note
- No automatic title-page generation from metadata.
- No automatic page breaks for major structural elements.
- No automatic table of contents generation.
- No automatic page numbering.

### Missing numbering and cross-reference logic

- No automatic numbering of sections.
- No automatic numbering of subsections and deeper hierarchy.
- No automatic numbering of tables.
- No automatic numbering of figures.
- No appendix-prefixed numbering.
- No cross-reference support.

### Missing content domains

- No formulas.
- No bibliography formatting.
- No citation formatting.
- No appendix system.
- No abbreviations list generation.
- No support for nested enumerations according to the standard.

### Missing validator coverage

- No validation of:
  - pagination
  - page-number position
  - structure order
  - section numbering
  - table continuation labels
  - figure numbering
  - appendix numbering
  - bibliography format
  - formula layout

---

## Concrete Gaps And Problems In The Current Codebase

### 1. The parser is line-oriented and too weak for the standard

`src/converter.py` reads the input file line by line and acts immediately. This prevents:
- two-pass numbering
- cross-references
- appendix-aware numbering
- TOC generation based on semantic structure
- validation against document order rules

### 2. File IO is hardcoded around repository folders

The converter reads only from `examples/` and writes only to `results/`. This makes testing, automation, and external usage harder than necessary.

### 3. Validation is heuristic and currently produces false negatives

Observed issue:
- the validator treats centered paragraphs as headings, so left-aligned `H2` and `H3` headings are checked as ordinary paragraphs and fail the first-line-indent rule.

Consequence:
- a document generated by the converter can fail validation even when it matches the converter's own intended formatting.

### 4. Test coverage is not trustworthy yet

Problems identified:
- some end-to-end tests create inputs in paths that the converter does not read from
- image behavior is validated mostly with a manual script instead of real assertions
- local pytest runs in this environment also hit temporary-directory permission issues, which hides the real project signal

### 5. Example corpus quality is inconsistent

Some example reports reference image filenames that do not exist in `images/`, so the output document can contain placeholder error text instead of figures.

### 6. The standard distinguishes framed and unframed documents, but the project mostly handles only one case

Current configuration matches the common unframed portrait document. It does not model:
- framed explanatory notes with title blocks
- landscape page rules
- per-document-profile layout decisions

---

## Recommended Target Architecture

The project should evolve toward this pipeline:

1. `TXT/Markdown-like source`
2. `lexer/parser`
3. `document AST`
4. `numbering and cross-reference pass`
5. `profile-aware layout/render pass`
6. `DOCX writer`
7. `post-generation validator`

Core design rules:
- separate parsing from rendering
- separate document semantics from formatting constants
- allow per-document profiles
- keep numbering and references in a dedicated pass
- keep validation semantic, not heuristic

---

## Detailed Roadmap Summary

### Phase 1. Stabilize the project foundation

Goals:
- remove hardcoded path assumptions
- make tests meaningful
- split parsing from rendering

Deliverables:
- path-agnostic converter API
- parser module
- working pytest setup
- realistic fixture-based regression tests

### Phase 2. Introduce semantic document structure

Goals:
- parse the input into typed blocks instead of writing DOCX on the fly
- encode structure explicitly

Deliverables:
- AST classes for:
  - document
  - section
  - paragraph
  - list
  - table
  - figure
  - bibliography
  - appendix
- metadata block for report type and title-page data

### Phase 3. Add report profiles and structural generation

Goals:
- support lab/practical/project reports first
- generate mandatory sections and page breaks correctly

Deliverables:
- report profile configuration
- title-page generator for Appendix `М`
- structural-element page breaks
- page numbering support

### Phase 4. Add numbering and references

Goals:
- support formal numbering from the standard

Deliverables:
- section/subsection numbering
- table numbering
- figure numbering
- appendix numbering
- cross-reference placeholders and resolution

### Phase 5. Add domain-specific content features

Goals:
- cover the major missing document domains

Deliverables:
- formulas
- bibliography formatting
- citation handling
- appendix rendering
- abbreviations list rendering
- nested enumerations

### Phase 6. Upgrade validation to standard-level checks

Goals:
- validate the document against the standard as a document, not as independent paragraphs

Deliverables:
- structure-aware validator
- numbering checks
- caption checks
- pagination checks
- bibliography checks
- appendix checks

### Phase 7. Improve tooling and usability

Goals:
- make the project usable outside the interactive menu

Deliverables:
- argument-driven CLI
- profile selection
- validation mode
- batch mode
- better error reporting

---

## Recommended Implementation Order

Recommended order of execution:

1. Fix API and testability first.
2. Build parser and AST second.
3. Add report profile support for one document type first:
   - `Appendix М` lab/practical/project report
4. Add numbering and page-break logic.
5. Add bibliography and appendix support.
6. Add formulas last, because they require the most rendering-specific work.
7. Only after the model is stable, strengthen the validator.

Why this order:
- numbering and validation depend on structure
- structure depends on a parser/AST
- title pages and page numbering are core compliance features
- formulas and advanced table behavior are expensive and should be added after the basic architecture is correct

---

## Near-Term Priorities

The next milestone should not be "support everything in the PDF."

The next milestone should be:

1. make the converter testable and path-agnostic
2. parse input into a semantic model
3. implement one real report profile end-to-end
4. prove it with a generated sample and a validator report

The best first supported profile is:
- report according to Appendix `М`
- unframed pages
- title page
- section headings
- figures
- tables
- bibliography as a numbered source list

That scope is large enough to matter and small enough to finish.
