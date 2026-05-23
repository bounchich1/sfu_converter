# Clean architecture requirements

## Architecture goal

The project must be organized so that parsing, formatting decisions, DOCX rendering, validation, CLI IO, and filesystem access can be changed and tested independently. The domain and application layers must not import `python-docx`, `argparse`, terminal menu code, or concrete filesystem adapters.

## Required layers

| Layer | Responsibility | May depend on |
| --- | --- | --- |
| Domain | Document AST, syntax-independent rules, diagnostics, formatting rule identifiers, value objects | Python standard library only |
| Application | Use cases: parse, lint, convert, validate, export schema, load profile | Domain and abstract ports |
| Interface | CLI, interactive menu, JSON/text presenters | Application and domain |
| Infrastructure | `python-docx` renderer, filesystem, image loading, template loading, Markdown/YAML rule registry | Application ports and domain |

Dependency direction must always point inward. Infrastructure and interface code may call application services, but application services must never import concrete CLI or DOCX classes.

## Required domain model

The domain model must include immutable or side-effect-free representations for:

- `Document` with metadata, blocks, syntax version, and source map.
- Block types: paragraph, heading, table, figure, formula, list, page break, appendix, bibliography entry, raw warning block.
- `FormattingProfile` with document type and applicable rule IDs.
- `FormattingRule` with ID, severity, source document, source section, and machine-readable parameters.
- `Diagnostic` with code, message, severity, source span, rule ID when applicable, and suggested fix when available.
- `ConversionResult` with output path, emitted diagnostics, applied profile, and generated artifact metadata.

## Required use cases

- `ParseText`: TXT source to AST plus diagnostics.
- `LintText`: parse and validate syntax without writing DOCX.
- `RenderDocx`: AST and formatting profile to DOCX bytes or file output.
- `ConvertTextToDocx`: orchestrates parse, lint, render, and post-render validation.
- `ValidateDocx`: validates an existing DOCX against a formatting profile.
- `ListProfiles`: exposes available formatting profiles.
- `ExportSchemas`: emits JSON schemas for CLI results and AST.
- `ComposeWithTemplate`: loads an existing DOCX template, preserves selected prefix pages or sections, and appends generated content at an explicit insertion point.

## Required ports

Application services must depend on abstract ports for:

- Source file loading and output writing.
- Formatting rule/profile repository.
- Template repository.
- Image asset resolution.
- DOCX rendering.
- DOCX validation/extraction.
- Logging/event reporting.

## Template composition requirements

The rewrite must support user-provided DOCX templates for already-correct title pages, assignment pages, approvals, or other front matter. A template may be used as an immutable prefix so the converter adds generated content only after page 1, after page 2, at the end of the template, or at a named bookmark/content-control insertion point.

Required behavior:

- Template pages selected for preservation must not be reformatted, restyled, renumbered, or otherwise mutated by the converter.
- The converter must copy or preserve the template's sections, headers, footers, margins, title blocks, page numbering fields, and embedded media unless the user explicitly selects an override mode.
- Generated content must start at the requested insertion point with a page or section break when required by the formatting profile.
- The template adapter must report a diagnostic if the requested insertion point cannot be found.
- The validator must be able to validate either the whole output document or only the generated part, depending on CLI options.
- The template feature must be available through the same application use cases as normal conversion, not through a separate rendering path.

Concrete adapters belong in infrastructure. Tests must be able to replace every adapter with in-memory fakes.

## Error and diagnostic policy

Recoverable problems must become diagnostics, not unstructured exceptions. Examples: unknown marker, missing image, malformed table row, unsupported formatting rule, and invalid metadata. Exceptions are reserved for programmer errors or infrastructure failures that cannot be represented in the output contract.

Every diagnostic must have:

- stable code such as `TXT_UNKNOWN_MARKER`;
- severity: `info`, `warning`, `error`, or `fatal`;
- source location when available;
- optional rule ID;
- optional suggestion.

## Compatibility policy

The current README syntax is version 1. The rewrite must support it during migration. New syntax must be versioned and selectable by CLI flag or document marker. Compatibility adapters must translate old syntax into the same AST as new syntax rather than maintaining a second rendering path.
