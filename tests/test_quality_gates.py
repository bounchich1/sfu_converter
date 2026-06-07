from pathlib import Path

import tomllib

from sfu_converter.domain.formatting import RuleStatus
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
    pytest_command = next(
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("- run: python -m pytest")
    )
    for flag in (
        "--cov=sfu_converter",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=100",
    ):
        assert flag in pytest_command


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
