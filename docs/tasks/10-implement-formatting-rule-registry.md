# Task 10: Implement Formatting Rule Registry

## Priority: High
## Phase: Phase 4 (Formatting rule registry)
## Affected files: NEW `src/sfu_converter/registry/`, MODIFY `src/sfu_converter/config.py`
## References: `docs/technical requirements/05_formatting_traceability.md`

## Summary

Replace the hardcoded `SIBFUConfig` class with a structured rule registry where every formatting constant is traceable to a specific section in `docs/formatting requirements/`. This is the canonical source of truth for all formatting decisions.

## Detailed Implementation

### 1. Create registry directory

```
src/sfu_converter/registry/
├── __init__.py
├── rules.py          # Rule definitions
├── profiles.py       # Profile definitions
└── loader.py         # Registry loader
```

### 2. Define rules in `registry/rules.py`

Each rule maps to a specific section in the formatting docs:

```python
from ..domain.formatting import FormattingRule, RuleSeverity, RuleStatus

COMMON_RULES = [
    FormattingRule(
        id="common.page.margins.portrait",
        source_doc="docs/formatting requirements/common.md",
        source_section="Page and paper setup",
        severity=RuleSeverity.REQUIRED,
        parameters={'top_mm': 20, 'bottom_mm': 20, 'left_mm': 30, 'right_mm': 10},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.NOT_SUPPORTED,
        description="A4 portrait with margins: top 20mm, bottom 20mm, left 30mm, right 10mm",
    ),
    FormattingRule(
        id="common.text.font.name",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'font_name': 'Times New Roman'},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.IMPLEMENTED,
        description="Body text font: Times New Roman",
    ),
    FormattingRule(
        id="common.text.font.size",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'font_size_pt': 14},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.IMPLEMENTED,
        description="Body text font size: 14pt",
    ),
    FormattingRule(
        id="common.text.font.color",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'color_rgb': [0, 0, 0]},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.NOT_SUPPORTED,
        description="Body text color: black",
    ),
    FormattingRule(
        id="common.text.alignment",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'alignment': 'justify'},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.NOT_SUPPORTED,
        description="Body text alignment: justified",
    ),
    FormattingRule(
        id="common.text.indent.first_line",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'indent_cm': 1.25},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.IMPLEMENTED,
        description="First line indent: 1.25cm",
    ),
    FormattingRule(
        id="common.text.line_spacing",
        source_doc="docs/formatting requirements/common.md",
        source_section="Core text formatting",
        severity=RuleSeverity.REQUIRED,
        parameters={'spacing': 1.5},
        renderer_status=RuleStatus.IMPLEMENTED,
        validator_status=RuleStatus.NOT_SUPPORTED,
        description="Line spacing: 1.5",
    ),
    FormattingRule(
        id="common.page.numbering",
        source_doc="docs/formatting requirements/common.md",
        source_section="Page numbering",
        severity=RuleSeverity.REQUIRED,
        parameters={'position': 'bottom_center', 'font_size_pt': 14, 'format': 'arabic'},
        renderer_status=RuleStatus.NOT_SUPPORTED,
        validator_status=RuleStatus.NOT_SUPPORTED,
        description="Arabic page numbers centered at bottom, 14pt",
    ),
    # ... continue for all rules from common.md
    # Headings, tables, figures, lists, formulas, bibliography, appendices, etc.
]
```

### 3. Define profiles in `registry/profiles.py`

```python
from ..domain.formatting import FormattingProfile
from .rules import COMMON_RULES

PROFILES = {
    'common': FormattingProfile(
        name='common',
        display_name='Common formatting rules',
        source_docs=('docs/formatting requirements/common.md',),
        rules=tuple(COMMON_RULES),
    ),
    'lab_practical_project_reports': FormattingProfile(
        name='lab_practical_project_reports',
        display_name='Lab / Practical / Project Reports',
        source_docs=(
            'docs/formatting requirements/common.md',
            'docs/formatting requirements/lab_practical_project_reports.md',
        ),
        rules=tuple(COMMON_RULES),  # + LAB_RULES
    ),
    # ... add all profiles from 05_formatting_traceability.md
}
```

### 4. Migrate `config.py` to use registry

Keep `SIBFUConfig` as a compatibility layer that reads from the registry:

```python
class SIBFUConfig:
    """Compatibility layer. New code should use the rule registry directly."""
    @classmethod
    def from_profile(cls, profile_name: str) -> 'SIBFUConfig':
        # Build config from registry rules
        ...
```

## Tests

- Every rule ID references an existing `source_doc` file
- Every profile maps to valid source docs
- Registry can list all rules and their statuses
- Rules with `NOT_SUPPORTED` status are properly reported
- CLI `list-profiles` returns all defined profiles

## Verification

1. `python -m sfu_converter list-profiles --format json` outputs all profiles
2. Rule IDs follow the `{doc}.{section}.{element}` naming convention
3. No formatting constants exist outside the registry (except `SIBFUConfig` compat layer)
