"""Tests for the formatting rule registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.formatting import (
    FormattingProfile,
    FormattingRule,
    RuleSeverity,
    RuleStatus,
)
from sfu_converter.registry import (
    COMMON_RULES,
    PROFILES,
    RULES_BY_ID,
    build_legacy_config,
    get_profile,
    get_rule,
    iter_profiles,
    iter_rules,
)
from sfu_converter.registry.loader import rules_with_status


REPO_ROOT = Path(__file__).resolve().parents[1]


def assert_close(actual, expected) -> None:
    assert abs(actual - expected) < 1000


def test_every_rule_id_is_unique():
    ids = [rule.id for rule in COMMON_RULES]
    assert len(ids) == len(set(ids))


def test_every_rule_source_doc_exists_on_disk():
    for rule in COMMON_RULES:
        path = REPO_ROOT / rule.source_doc
        assert path.exists(), f"Missing source doc for {rule.id}: {path}"


def test_every_profile_source_doc_exists_on_disk():
    for profile in PROFILES.values():
        for source_doc in profile.source_docs:
            path = REPO_ROOT / source_doc
            assert path.exists(), f"Missing source doc for profile {profile.name}: {path}"


def test_rule_id_naming_convention():
    for rule in COMMON_RULES:
        parts = rule.id.split(".")
        assert len(parts) >= 3, f"Rule id should follow doc.section.element: {rule.id}"
        assert all(parts), f"Empty segment in rule id: {rule.id}"


def test_rules_by_id_is_complete():
    assert set(RULES_BY_ID) == {rule.id for rule in COMMON_RULES}


def test_iter_helpers_match_collections():
    assert list(iter_rules()) == list(COMMON_RULES)
    assert list(iter_profiles()) == list(PROFILES.values())


def test_get_rule_returns_matching_entry():
    rule = get_rule("common.text.font.name")
    assert isinstance(rule, FormattingRule)
    assert rule.parameters["font_name"] == "Times New Roman"


def test_get_rule_missing_raises():
    with pytest.raises(KeyError):
        get_rule("does.not.exist")


def test_get_profile_returns_profile():
    profile = get_profile("common")
    assert isinstance(profile, FormattingProfile)
    assert profile.rules == COMMON_RULES


def test_profiles_inherit_common_rules():
    for profile in PROFILES.values():
        for rule in COMMON_RULES:
            assert rule in profile.rules, (
                f"Profile {profile.name} missing common rule {rule.id}"
            )


def test_rules_with_status_filters_by_renderer():
    not_supported = rules_with_status(renderer=RuleStatus.NOT_SUPPORTED)
    assert any(rule.id == "common.page.numbering" for rule in not_supported)
    assert all(rule.renderer_status is RuleStatus.NOT_SUPPORTED for rule in not_supported)


def test_required_severity_is_used_for_core_rules():
    font_size_rule = get_rule("common.text.font.size")
    assert font_size_rule.severity is RuleSeverity.REQUIRED


def test_legacy_config_dict_matches_sibfu_config_attributes():
    legacy = build_legacy_config()

    assert legacy["FONT_NAME"] == SIBFUConfig.FONT_NAME == "Times New Roman"
    assert legacy["FONT_SIZE"] == SIBFUConfig.FONT_SIZE == Pt(14)
    assert legacy["FONT_COLOR_RGB"] == SIBFUConfig.FONT_COLOR_RGB == (0, 0, 0)
    assert legacy["LINE_SPACING_NORMAL"] == SIBFUConfig.LINE_SPACING_NORMAL == 1.5
    assert legacy["ALIGNMENT"] == SIBFUConfig.ALIGNMENT == WD_ALIGN_PARAGRAPH.JUSTIFY

    assert_close(legacy["FIRST_LINE_INDENT"], Cm(1.25))
    assert_close(SIBFUConfig.FIRST_LINE_INDENT, Cm(1.25))


def test_legacy_config_margins_match_standard():
    margins = build_legacy_config()["MARGINS"]
    assert_close(margins["top"], Cm(2))
    assert_close(margins["bottom"], Cm(2))
    assert_close(margins["left"], Cm(3))
    assert_close(margins["right"], Cm(1))


def test_legacy_config_image_block_preserves_keys():
    image = build_legacy_config()["IMAGE"]
    assert set(image.keys()) >= {
        "line_spacing",
        "alignment",
        "width",
        "height",
        "dpi",
        "format",
        "max_width",
    }
    assert image["alignment"] == WD_ALIGN_PARAGRAPH.CENTER
    assert image["width"] is None
    assert image["height"] is None
    assert image["dpi"] == (96, 96)
    assert_close(image["max_width"], Cm(15))


def test_heading_blocks_round_trip_through_config():
    legacy = build_legacy_config()
    assert legacy["H1"]["align"] == WD_ALIGN_PARAGRAPH.CENTER
    assert legacy["H1"]["bold"] is True
    assert legacy["H2"]["align"] == WD_ALIGN_PARAGRAPH.LEFT
    assert legacy["H2"]["bold"] is True
    assert legacy["H3"]["bold"] is False
