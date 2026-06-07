import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO = "bounchich1/sfu_converter"
OLD_REPO = "Nikita2005qwe/sfu_converter"
EXPECTED_SKILLS = [
    "sfu-common",
    "sfu-coursework",
    "sfu-practice",
    "sfu-report-lab",
    "sfu-research",
    "sfu-small-works",
    "sfu-vkr",
]


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    if shutil.which("node") is None:
        pytest.skip("Node.js is required to run the agent installer")

    return subprocess.run(
        ["node", "bin/install.js", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_package_json_declares_single_node_installer_bin():
    package_path = Path("package.json")

    assert package_path.is_file()

    package = json.loads(package_path.read_text(encoding="utf-8"))

    assert package["name"] == "sfu-converter-agent-installer"
    assert package["bin"] == {"sfu-converter-agent-install": "bin/install.js"}
    assert "bin/install.js" in package["files"]
    assert "plugins/sfu-converter" in package["files"]
    assert ".claude-plugin/marketplace.json" in package["files"]
    assert "install.sh" in package["files"]
    assert "install.ps1" in package["files"]


def test_installer_shims_exist():
    assert Path("install.sh").is_file()
    assert Path("install.ps1").is_file()
    assert Path("bin/install.js").is_file()
    assert Path("bin/install.js").read_text(encoding="utf-8").startswith("#!/usr/bin/env node")


def test_codex_skills_are_present_with_frontmatter():
    skills_root = Path("plugins/sfu-converter/skills")

    assert sorted(path.name for path in skills_root.iterdir() if path.is_dir()) == EXPECTED_SKILLS
    assert Path("plugins/sfu-converter/references").is_dir()

    for skill_name in EXPECTED_SKILLS:
        skill_path = skills_root / skill_name / "SKILL.md"
        body = skill_path.read_text(encoding="utf-8")

        assert body.startswith("---\n")
        frontmatter = body.split("---", 2)[1]
        assert f"name: {skill_name}" in frontmatter
        assert "description:" in frontmatter


def test_codex_dry_run_installs_all_plugin_skills():
    result = run_installer("--dry-run", "--only", "codex", "--no-color")

    assert result.returncode == 0, result.stderr
    assert f"npx -y skills add {REPO} -a codex --yes --all" in result.stdout


def test_claude_dry_run_installs_plugin_from_canonical_repo():
    result = run_installer("--dry-run", "--only", "claude", "--no-color")

    assert result.returncode == 0, result.stderr
    assert f"claude plugin marketplace add {REPO}" in result.stdout
    assert "claude plugin install sfu-converter@sfu-converter" in result.stdout


def test_public_installation_files_use_canonical_repo_slug():
    checked_paths = [
        Path("README.md"),
        Path("docs/installation.md"),
        Path("plugins/sfu-converter/README.md"),
        Path("plugins/sfu-converter/.claude-plugin/plugin.json"),
        Path(".claude-plugin/marketplace.json"),
        Path("pyproject.toml"),
    ]

    for path in checked_paths:
        content = path.read_text(encoding="utf-8")

        assert OLD_REPO not in content, path

    assert REPO in Path("docs/installation.md").read_text(encoding="utf-8")
    assert REPO in Path("plugins/sfu-converter/.claude-plugin/plugin.json").read_text(encoding="utf-8")
