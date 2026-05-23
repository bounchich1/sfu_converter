# Technical requirements index

This directory defines the target technical requirements for the TXT-to-DOCX converter rewrite and growth phase. It is based on the current project state in `src/`, the current README syntax, and the formatting rules in `docs/formatting requirements/`.

## Non-negotiable goals

- Provide a non-interactive CLI interface suitable for AI-agent automation.
- Rewrite toward clean architecture with explicit domain, application, interface, and infrastructure boundaries.
- Reach and enforce 100% automated test coverage for production code.
- Keep a strong, traceable connection to the formatting requirements documents.
- Provide an easy TXT syntax for AI agents that converts predictably to DOCX.
- Support DOCX templates whose finished title pages or front matter are preserved while generated content is appended after page 1, page 2, the full template, or a named insertion point.
- Remove DRY violations by making syntax, formatting rules, diagnostics, and CLI contracts single-source.

## Document map

- [01_current_state.md](01_current_state.md) - analysis of the current codebase, syntax, tests, and gaps.
- [02_clean_architecture.md](02_clean_architecture.md) - target architecture, dependency rules, use cases, and ports.
- [03_agent_cli.md](03_agent_cli.md) - required CLI commands, machine-readable IO, and exit-code contract.
- [04_txt_syntax.md](04_txt_syntax.md) - versioned TXT syntax requirements and compatibility with the README syntax.
- [05_formatting_traceability.md](05_formatting_traceability.md) - rule IDs, profile mapping, and traceability to formatting docs.
- [06_testing_coverage.md](06_testing_coverage.md) - 100% coverage policy, test pyramid, and quality gates.
- [07_dry_maintainability.md](07_dry_maintainability.md) - anti-duplication requirements and maintainability controls.
- [08_migration_roadmap.md](08_migration_roadmap.md) - phased rewrite plan with acceptance criteria.

## Canonical source rule

The formatting documents remain the human-readable source for SFU formatting policy. Technical requirements must reference them instead of copying their full content. Implementation code must reference structured rule IDs derived from those documents, not hand-coded prose or duplicated constants.
