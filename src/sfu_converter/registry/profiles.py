"""Formatting profiles defined for each SFU document family.

Each profile lists the source documents from which its rules are derived plus
the resolved tuple of :class:`FormattingRule` objects. The ``common`` profile
holds the shared baseline; document-specific profiles inherit those rules and
will gain additional ones as further docs are translated to the registry.
"""

from __future__ import annotations

from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.registry.rules import COMMON_RULES

_COMMON_DOC = "docs/formatting requirements/common.md"


def _profile(
    name: str,
    display_name: str,
    extra_docs: tuple[str, ...] = (),
) -> FormattingProfile:
    return FormattingProfile(
        name=name,
        display_name=display_name,
        source_docs=(_COMMON_DOC, *extra_docs),
        rules=COMMON_RULES,
    )


PROFILES: dict[str, FormattingProfile] = {
    "common": FormattingProfile(
        name="common",
        display_name="Common formatting rules",
        source_docs=(_COMMON_DOC,),
        rules=COMMON_RULES,
    ),
    "lab_practical_project_reports": _profile(
        "lab_practical_project_reports",
        "Lab / Practical / Project Reports",
        ("docs/formatting requirements/lab_practical_project_reports.md",),
    ),
    "practice_reports": _profile(
        "practice_reports",
        "Practice Reports",
        ("docs/formatting requirements/practice_reports.md",),
    ),
    "research_reports": _profile(
        "research_reports",
        "Research-Work Reports",
        ("docs/formatting requirements/research_reports.md",),
    ),
    "coursework": _profile(
        "coursework",
        "Course Project / Course Work",
        ("docs/formatting requirements/coursework.md",),
    ),
    "graduation_qualification_work": _profile(
        "graduation_qualification_work",
        "Graduation Qualification Work (VKR)",
        ("docs/formatting requirements/graduation_qualification_work.md",),
    ),
    "small_written_works": _profile(
        "small_written_works",
        "Referat / Control Work / Calculation-Graphic Work / Essay",
        ("docs/formatting requirements/small_written_works.md",),
    ),
    "graphic_and_demonstration_materials": _profile(
        "graphic_and_demonstration_materials",
        "Graphic and Demonstration Materials",
        ("docs/formatting requirements/graphic_and_demonstration_materials.md",),
    ),
    "project_designations": _profile(
        "project_designations",
        "Project Designations",
        ("docs/formatting requirements/project_designations.md",),
    ),
}
