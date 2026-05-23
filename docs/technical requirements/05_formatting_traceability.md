# Formatting traceability requirements

## Formatting documents

The converter must maintain direct traceability to:

- [common.md](<../formatting requirements/common.md>)
- [coursework.md](<../formatting requirements/coursework.md>)
- [graduation_qualification_work.md](<../formatting requirements/graduation_qualification_work.md>)
- [graphic_and_demonstration_materials.md](<../formatting requirements/graphic_and_demonstration_materials.md>)
- [lab_practical_project_reports.md](<../formatting requirements/lab_practical_project_reports.md>)
- [practice_reports.md](<../formatting requirements/practice_reports.md>)
- [project_designations.md](<../formatting requirements/project_designations.md>)
- [research_reports.md](<../formatting requirements/research_reports.md>)
- [small_written_works.md](<../formatting requirements/small_written_works.md>)

## Rule registry

Every implemented formatting rule must be represented by a structured rule record with:

- stable rule ID, for example `common.page.margins.portrait`;
- source document path;
- source section heading;
- severity: required, recommended, or advisory;
- supported document profiles;
- machine-readable parameters;
- renderer support status;
- validator support status;
- tests that prove the rule.

Implementation code must not hard-code rule meaning without a rule ID.

## Profile mapping

Each output document must be converted with a formatting profile. Required initial profiles:

| Profile | Required source docs |
| --- | --- |
| `common` | `common.md` |
| `lab_practical_project_reports` | `common.md`, `lab_practical_project_reports.md` |
| `practice_reports` | `common.md`, `practice_reports.md` |
| `research_reports` | `common.md`, `research_reports.md` |
| `coursework` | `common.md`, `coursework.md`, `project_designations.md` |
| `small_written_works` | `common.md`, `small_written_works.md` |
| `graduation_qualification_work` | `common.md`, `graduation_qualification_work.md`, `graphic_and_demonstration_materials.md`, `project_designations.md` |

Profile names exposed by CLI must match this registry.

## Minimum rule coverage

The first production-ready rewrite must cover these rule families:

- page size, orientation, and margins;
- base font, size, color, line spacing, paragraph indent, and alignment;
- page numbering;
- structural sections and heading formatting;
- section, subsection, point, and subpoint numbering;
- contents generation or contents compatibility;
- tables, table captions, table headers, and table references;
- illustrations, captions, numbering, and references;
- formulas, numbering, and explanations;
- list formatting;
- bibliography/source list formatting;
- appendices;
- title page metadata requirements by document type.

Unsupported rule families must appear in CLI diagnostics as `not_supported` until implemented. Silent omission is forbidden.

## Validator traceability

Every validation issue must include the rule ID and source formatting document when applicable. Example JSON shape:

```json
{
  "code": "FORMAT_MARGIN_LEFT",
  "severity": "error",
  "ruleId": "common.page.margins.portrait",
  "source": "docs/formatting requirements/common.md#page-and-paper-setup",
  "message": "Left margin is 20 mm, expected 30 mm"
}
```

## Documentation synchronization

When a formatting document changes, the rule registry and tests must be checked in the same change. CI must fail when a referenced formatting document or section no longer exists.

