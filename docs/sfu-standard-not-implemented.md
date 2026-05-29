# STU 7.5-07 implementation gaps

This audit records what is not implemented, or only partially implemented, in
the TXT to DOCX converter compared with the supplied SFU standard files:

- `docs/sfu-stu-7.5-07.pdf`
- `docs/sfu-stu-7.5-07-291121-s-podp.-ot-03.07.2024.doc`
- extracted requirement notes in `docs/formatting requirements/`

The converter currently implements a useful common subset of the standard, but
it is not a complete STU 7.5-07 document generator. In particular, the renderer
has broader support than the validator, and document-type profiles are mostly
metadata wrappers over the same common rules.

## Summary

Current implementation status:

- Common body formatting is mostly implemented: A4 portrait margins, Times New
  Roman 14 pt, black text, first-line indent, justified paragraphs, and basic
  line spacing.
- Several common block types are partially implemented: headings, structural
  sections, lists, tables, figures, formulas, bibliography entries, appendices,
  page numbering, table of contents field, and generic title page generation.
- Document-type-specific formatting is not implemented end to end.
- Profile selection is not wired through conversion or validation: the CLI
  accepts `--profile`, but `TextToDocxConverter.convert_file()` still renders
  through a default common profile, and `StyleValidator` still validates through
  the common profile.
- The rule registry marks all common rules as renderer-implemented, but many
  of those rules are only partial implementations of the standard text, not full
  compliance with every detail in STU 7.5-07.
- Validator coverage is incomplete: 18 of the 31 common rules currently have
  `validator_status=not_supported`.
- `explain-syntax` is implemented from parser metadata, but `parse`, `lint`,
  `list-profiles`, and `export-schema` are still CLI stubs.

## Document-type profiles

Profiles exist in `src/sfu_converter/registry/profiles.py`, but every
document-specific profile uses `COMMON_RULES` only. The extra requirement files
are listed as `source_docs`, but their document-specific rules are not
translated into executable registry rules. The `coursework` and
`graduation_qualification_work` profiles also do not yet list every inherited
requirement document required by `docs/technical requirements/05_formatting_traceability.md`.

Affected profiles:

- `lab_practical_project_reports`
- `practice_reports`
- `research_reports`
- `coursework`
- `graduation_qualification_work`
- `small_written_works`
- `graphic_and_demonstration_materials`
- `project_designations`

Missing behavior:

- Different mandatory title-page forms per document type.
- Different required metadata fields per document type.
- VKR-specific assignment, abstract, reviewer, consultant, and norm-control
  requirements.
- Course project explanatory-note framed sheets and title blocks.
- Practice, research, lab/practical/project-report-specific structures.
- Graphic and demonstration material requirements.
- Project designation rules and title-block field generation.

## CLI and profile wiring

The command-line interface exposes more concepts than it currently implements.

Missing or incomplete CLI behavior:

- `--profile` is accepted by `convert`, `validate-docx`, and `lint`, but
  conversion and validation do not use the selected profile.
- `parse` is a stub and returns "Not yet implemented".
- `lint` is a stub and returns "Not yet implemented".
- `list-profiles` is a stub and returns "Not yet implemented".
- `export-schema` is a stub and returns "Not yet implemented".
- `explain-syntax` is implemented, but only emits syntax metadata; it does not
  describe profile compatibility or unsupported formatting families.
- Unsupported formatting families are not emitted as structured
  `not_supported` diagnostics during conversion.

Relevant files:

- `src/sfu_converter/cli.py`
- `src/sfu_converter/converter.py`
- `src/sfu_converter/registry/profiles.py`

## Title pages

The standard requires a title page for every text document. The exact form
depends on document type:

- `Приложение Б`: master dissertation.
- `Приложение В`: diploma project.
- `Приложение Г`: diploma work.
- `Приложение Д`: bachelor work.
- `Приложение И`: course project/course work.
- `Приложение К`: practice report.
- `Приложение Л`: master's research-work report.
- `Приложение М`: laboratory work, practical work, and project-completion report.
- `Приложение Н`: referat, calculation work, control work, and essay.

Current implementation:

- `[TITLE_PAGE]` renders a generic page from metadata.
- The generated page includes common fields such as ministry, university,
  institute, department, subject, title, supervisor, student, city, and year.
- First-page footer is blank, so the printed title-page number is suppressed.

Not implemented:

- Exact appendix-specific layouts.
- Profile-specific title page selection.
- Mandatory/optional metadata validation per title-page form.
- Approval blocks where required.
- VKR reviewer, consultant, and norm-controller title-page variants.
- VKR continuation/additional title page forms.
- Exact signature/table positioning from the standard's appendix forms.
- Automatic failure when required title-page metadata is missing.

Relevant file:

- `src/sfu_converter/infrastructure/docx_renderer.py`

## Page setup and page numbering

Implemented:

- A4 portrait margins without a frame: left 30 mm, top 20 mm, bottom 20 mm,
  right 10 mm.
- Bottom-center PAGE field in Times New Roman 14 pt.
- First page footer is blank.

Not implemented or partial:

- Landscape orientation margins: left/right 20 mm, top 30 mm, bottom 10 mm.
- Mixed portrait/landscape sections.
- Pages with frames and title blocks.
- Page number placement in title-block field 7 for framed sheets.
- Validation of page-number fields.
- Validation of skipped title-page page number.

## Structural document composition

Implemented:

- Structural headings such as `ВВЕДЕНИЕ`, `ЗАКЛЮЧЕНИЕ`, and
  `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` are detected and rendered specially.
- Structural sections start on a new page in the renderer.

Not implemented or partial:

- Enforcement that title page and main part are always present.
- Enforcement of required/optional sections by document type.
- Placement checks for sections such as abbreviations before sources.
- Structured list of abbreviations as two aligned columns.
- Department-methodical-document requirements, which the standard delegates
  outside the common rules.
- Validation that every structural section starts on a new page.

## Section and heading numbering

Implemented:

- Auto-numbering for H1-H3 headings: `1`, `1.1`, `1.1.1`.
- Heading period removal for auto-numbered headings.
- Basic heading formatting.

Not implemented or partial:

- Subpoint numbering at the fourth level: `1.1.1.1`.
- Explicit distinction between sections, subsections, points, and subpoints.
- Rule that point headings are only used when a subsection contains multiple
  points divided into subpoints.
- Validation of no word hyphenation in headings.
- Validation that headings are concise or semantically match contents.
- Detection of manually numbered headings for consistency.
- Appendix-prefixed heading numbering such as `А.1`.

## Table of contents

Implemented:

- `[TOC]` and `СОДЕРЖАНИЕ` can insert a Word TOC field.
- Headings receive Word heading styles so Word can populate the TOC.

Not implemented or partial:

- The converter does not calculate or render final TOC entries itself.
- The generated TOC requires Word or a compatible editor to update fields.
- Dot leaders, exact indentation, continuation-line indentation, and page
  numbers are delegated to Word and are not validated.
- Contents are not conditionally suppressed/recommended based on document
  length of 24 pages or less.
- Contents entries are not checked against actual document headings.
- Appendix ranges and grouped `Приложения` entries are not implemented.
- Mandatory course-work contents example from `Приложение Т` is not implemented.

## Lists and enumerations

Implemented:

- Bullet-like SFU hyphen list items.
- Lettered list items using Russian lowercase letters.
- Numbered list items using `1)`, `2)`.
- Basic punctuation normalization for list items.

Not implemented or partial:

- Nested list rendering with two-character indentation shift for numeric nested
  items relative to lettered items.
- Parser support for real nested list structure.
- Validation of list marker order, indentation, and punctuation.
- Validation of references to list items.
- Exclusion rules for Russian letters in list markers are not explicitly
  validated.

## Tables

Implemented:

- Basic DOCX table creation from pipe rows.
- Optional table caption above the table.
- Caption normalized to `Таблица N - Name` style with a dash separator.
- Header row is bold and centered.
- Table text uses 12 pt, which falls inside the recommended 10-12 pt range.
- Header row is marked to repeat on following pages.

Not implemented or partial:

- Double line between table head and body.
- Full table border requirements beyond Word's `Table Grid` default.
- Table placement after first reference or on the next page.
- Automatic reference checking: every table must be referenced in text.
- Section-based table numbering.
- Appendix table numbering such as `Таблица А.1`.
- Unit labels above the table on the right in 12 pt.
- Per-column/per-row unit formatting.
- Numbering row replacement for continued tables.
- `Продолжение таблицы ...` and `Окончание таблицы ...` labels.
- Splitting large tables across pages or side-by-side.
- Table footnotes inside the table above the closing line.
- Italic letter designations from GOST 2.321.
- Validation of table captions, headers, continuation labels, units, borders,
  and references.

## Figures and illustrations

Implemented:

- Basic image insertion.
- Basic centered figure captions.
- Maximum image width from configuration.
- Missing image placeholder text.

Not implemented or partial:

- Automatic figure numbering when only a caption name is supplied.
- Section-based figure numbering.
- Appendix figure numbering such as `Рисунок А.1`.
- Validation that every figure is referenced in text.
- Placement after first reference or on the next page.
- Explanatory data below the illustration and above the figure caption.
- Recommended 12 pt font for explanatory data.
- Multi-page figure captions such as `лист 1` and `Рисунок 1, лист 2`.
- Checks that the image is readable, clear, and uses a suitable diagram type.
- ESKD/SPDS drawing compliance.
- Validation of figure spacing, captions, numbering, and image placement.

## Formulas

Implemented:

- Formula block rendering.
- Continuous auto-numbering in parentheses.
- Right-aligned number using a tab stop.
- Formula explanation paragraph with no first-line indent.

Not implemented or partial:

- Formula paragraph indent from the standard is ambiguous in the current
  registry: `common.formula.body` uses `indent_cm=0`.
- Section-based formula numbering such as `(1.1)`.
- Appendix formula numbering such as `(А.1)`.
- Rules for formulas inside tables or illustration explanatory data being
  unnumbered.
- Automatic line breaking at operation signs with repeated operation sign.
- Separate explanation lines for each symbol and coefficient.
- Validation that the first explanation starts with `где` without a colon.
- Validation that repeated symbols are only explained once.
- Handling consecutive formulas separated by commas.
- Cross-references to formulas.
- Handwritten formula allowance is out of scope and not represented.

## Bibliographic references and source list

Implemented:

- Basic numbered bibliography entries after the sources heading.
- Paragraph formatting for bibliography entries.
- V2 `[SOURCE number=N]` syntax.

Not implemented or partial:

- GOST R 7.0.100 bibliographic-description validation.
- GOST 7.80 heading validation.
- GOST 7.11 and GOST R 7.0.12 abbreviation validation.
- Grouping method validation: alphabetical, systematic/order of mention, or
  chronological.
- Enforcement that grouping methods are not mixed.
- Separate alphabetical sequence for non-Russian sources.
- `Приложение У` examples are not encoded as templates or validators.
- In-text bibliographic reference parsing and validation.
- Exact fragment references such as `[20, с. 29]`.
- Multivolume references such as `[18, т. 1, с. 75]`.
- Multiple source groups separated by semicolons.
- Footnote references and footnote formatting.

## Appendices

Implemented:

- Basic appendix heading on a new page.
- Allowed appendix-letter set excludes the disallowed letters in the common
  parser path.
- Optional appendix type and subtitle in the V1 appendix parser path.

Not implemented or partial:

- V2 appendix parser does not currently preserve `letter` and `type`
  attributes into the `AppendixNode`.
- Automatic appendix lettering.
- Enforcement that appendices appear at the end of the text document.
- Validation that every appendix has a heading.
- Appendix-internal section, subsection, point, and subpoint numbering.
- Appendix-prefixed table, figure, and formula numbering.
- Continued appendix labels: `Продолжение приложения` and
  `Окончание приложения`.
- A3, A3x4, A4x4, A2, and A1 appendix sheet formats.
- Separate independent appendix documents inserted with their own title page.
- Appendix references in text.
- Validation of appendix ordering, lettering, headings, and references.

## Graphic and demonstration materials

The converter is a TXT-to-DOCX renderer and does not currently implement the
standard's graphic-material workflow.

Not implemented:

- Drawings and schemes with title blocks.
- Posters.
- Slides.
- Folding and storage requirements.
- Graphic material title-block forms from `Приложение С`.
- Sheet formats and scales from referenced GOST rules.
- Drawing fonts and ESKD/SPDS-specific layout requirements.

Related requirement files:

- `docs/formatting requirements/graphic_and_demonstration_materials.md`
- `docs/formatting requirements/project_designations.md`

## Project designations and framed sheets

Not implemented:

- Diploma/course project explanatory-note sheet forms.
- Main title-block forms.
- Letter-numeric project designations.
- Title-block field meanings.
- Document codes from `Приложение Х`.
- Page numbering inside title-block field 7.
- Profile-specific behavior for diploma projects and course projects.

## Validator gaps

The validator is not equivalent to the renderer or to the full standard.

Currently unsupported validator rule families include:

- Page numbering.
- Heading blank-line spacing.
- Lists.
- Figure captions and figure spacing.
- Image placement.
- Formula body, explanation, and spacing.
- Bibliography entries.
- Table captions and table spacing.
- Table cell padding.
- Table body details.

Observed issue:

- A generated document can fail validation because caption paragraphs and
  missing-image placeholders are treated as normal body paragraphs rather than
  as figure/table-specific paragraphs.

Needed validator work:

- Classify paragraph roles before applying rules.
- Validate footer/page-number fields.
- Validate table, figure, formula, bibliography, appendix, and TOC rules by
  rule ID.
- Emit `not_supported` diagnostics for unsupported rule families instead of
  silently skipping them.
- Validate selected document profile, not only common formatting.

## Registry and traceability gaps

Implemented:

- Common rule records exist with stable rule IDs and source references.
- Profiles list source requirement documents.

Not implemented or partial:

- Document-specific requirement files are not converted into profile-specific
  rule records.
- The registry does not model many standard details, such as table
  continuations, title-block fields, exact title pages, source-list grouping,
  graphic materials, or footnotes.
- `renderer_status=implemented` is too coarse for several rules because the
  renderer implements only a basic subset of the corresponding standard
  section.
- There is no generated coverage matrix tying every requirement line to parser,
  renderer, validator, and tests.

## Testing gaps

The test suite covers the implemented subset, but it does not prove full
standard compliance.

Missing test coverage areas:

- Profile-specific output for every document type.
- Exact title-page appendix forms.
- Landscape pages and framed sheets.
- TOC visual formatting and updated page numbers.
- Table continuations and appendix table numbering.
- Multi-page figures and explanatory data.
- Formula section/appendix numbering and symbol explanation rules.
- Bibliographic GOST formatting.
- Footnotes.
- Graphic materials and project designation sheets.
- Validator diagnostics for every registered rule.
- End-to-end conversion with `--profile` proving profile-specific behavior.

## Recommended implementation order

1. Wire `--profile` through conversion and validation.
2. Implement CLI `list-profiles`, `parse`, `lint`, and `export-schema`.
3. Split common registry rules from document-specific profile rules.
4. Replace generic title page generation with profile-specific title-page
   templates or exact layout generators.
5. Fix validator paragraph-role classification so generated captions, lists,
   formulas, and bibliography entries validate against their own rule families.
6. Add structured `not_supported` diagnostics for every unimplemented standard
   family.
7. Implement missing document-type requirements one profile at a time.
8. Add an automated coverage matrix from requirement documents to parser,
   renderer, validator, and tests.
