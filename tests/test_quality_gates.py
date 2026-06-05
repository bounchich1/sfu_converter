from pathlib import Path
import tomllib

from sfu_converter.domain.formatting import RuleStatus
from sfu_converter.registry import ALL_RULES
from sfu_converter.registry.coverage import build_rows


def test_pyproject_enforces_ruff_and_coverage_gates():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["coverage"]["run"]["branch"] is True
    assert pyproject["tool"]["coverage"]["report"]["fail_under"] == 100
    assert pyproject["tool"]["coverage"]["report"]["show_missing"] is True
    assert pyproject["tool"]["coverage"]["report"]["skip_empty"] is True
    assert pyproject["tool"]["ruff"]["line-length"] == 120
    assert pyproject["tool"]["ruff"]["target-version"] == "py310"
    assert pyproject["tool"]["ruff"]["lint"]["select"] == ["E", "F", "W", "I", "N", "UP", "B"]


def test_ci_runs_coverage_gate_on_windows_and_linux():
    workflow_path = Path(".github/workflows/test.yml")
    workflow = workflow_path.read_text(encoding="utf-8")

    assert "name: Tests" in workflow
    assert "ubuntu-latest" in workflow
    assert "windows-latest" in workflow
    assert 'pip install -e ".[dev]"' in workflow
    assert (
        "python -m pytest --cov=sfu_converter --cov-branch "
        "--cov-report=term-missing --cov-fail-under=100"
    ) in workflow
    assert "python -m pytest --cov=sfu_converter --cov-branch --cov-report=xml" in workflow


def test_implemented_rules_have_traceability_markers():
    missing = [
        row.rule_id
        for row in build_rows()
        if (
            row.renderer_status == RuleStatus.IMPLEMENTED.value
            or row.validator_status == RuleStatus.IMPLEMENTED.value
        )
        and not row.test_modules
    ]

    assert missing == []


def test_rule_sources_resolve_to_markdown_headings():
    cache: dict[str, set[str]] = {}
    for rule in ALL_RULES:
        source_path = Path(rule.source_doc)
        assert source_path.exists(), f"{rule.id} source doc missing: {rule.source_doc}"
        if rule.source_doc not in cache:
            headings = set()
            for line in source_path.read_text(encoding="utf-8").splitlines():
                if line.lstrip().startswith("#"):
                    headings.add(_slug(line.lstrip("#").strip()))
            cache[rule.source_doc] = headings
        assert _slug(rule.source_section) in cache[rule.source_doc], (
            f"{rule.id} source section {rule.source_section!r} not found in {rule.source_doc}"
        )


def _slug(value: str) -> str:
    return "-".join(" ".join(value.casefold().split()).split(" "))
