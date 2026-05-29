# DRY and maintainability requirements

## Single sources of truth

The rewrite must remove duplicated business rules. Each concept must have one canonical representation:

| Concept | Canonical source |
| --- | --- |
| TXT grammar | Parser grammar/spec module |
| Syntax help | Generated from grammar/spec metadata |
| CLI JSON contracts | JSON schema definitions |
| Formatting rules | Structured rule registry linked to `docs/formatting requirements/` |
| Renderer styles | Formatting profile and rule registry |
| Validator checks | Formatting rule IDs and rule parameters |
| Diagnostics | Diagnostic catalog |
| Examples | Golden fixture corpus |

If two files need the same rule, one file must import or generate from the canonical source.

## Forbidden duplication

The codebase must not contain:

- separate regex sets for the same marker language;
- repeated `if/elif` style chains in parser, renderer, and validator;
- formatting constants repeated in config, renderer, tests, and docs;
- CLI result structures hand-built differently by each command;
- hard-coded `examples/`, `results/`, `images/`, or `templates/` paths outside configuration/adapters;
- separate validation messages for the same diagnostic code;
- copied formatting prose from documentation into implementation comments.

## Required maintainability controls

- Add import-boundary tests to enforce clean architecture dependencies.
- Add duplicate-code checks suitable for Python.
- Add linting and formatting tools with stable configuration.
- Keep modules focused. A module that mixes parsing, rendering, IO, and validation must be split.
- Keep public APIs typed and documented.
- Generate CLI help and syntax documentation from metadata where practical.
- Make every supported formatting rule discoverable by CLI.

## Review checklist

Every implementation change must answer:

- Which canonical source owns the new rule or syntax?
- Which tests prove the new behavior?
- Which formatting requirement document is linked, if any?
- Does this add another way to express an existing concept?
- Does this duplicate a constant, message, regex, or path convention?

Any duplicated rule must be fixed before merge.

