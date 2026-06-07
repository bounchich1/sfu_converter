import sys

from sfu_converter import agents


def make_emit():
    lines: list[str] = []
    return lines, lines.append


def test_provider_lookup_returns_provider_or_none():
    assert agents._provider("claude").label == "Claude Code"
    assert agents._provider("codex").label == "Codex CLI"
    assert agents._provider("unknown") is None


def test_detect_available_filters_by_command_presence():
    present = {"claude"}

    available = agents.detect_available(which=lambda command: "/path" if command in present else None)

    assert [provider.id for provider in available] == ["claude"]


def test_install_commands_claude_uses_marketplace_then_install():
    commands = agents._install_commands(agents._provider("claude"))

    assert commands == [
        ("claude", ["plugin", "marketplace", "add", agents.REPO]),
        ("claude", ["plugin", "install", f"{agents.PLUGIN_ID}@{agents.PLUGIN_ID}"]),
    ]


def test_install_commands_codex_uses_npx_skills_add():
    commands = agents._install_commands(agents._provider("codex"))

    assert commands == [("npx", ["-y", "skills", "add", agents.REPO, "-a", "codex", "--yes", "--all"])]


def test_install_provider_dry_run_does_not_invoke_runner():
    lines, emit = make_emit()
    calls = []

    ok = agents.install_provider(
        agents._provider("codex"),
        dry_run=True,
        run=lambda command, args: calls.append((command, args)) or 0,
        emit=emit,
    )

    assert ok is True
    assert calls == []
    assert any("демо" in line for line in lines)


def test_install_provider_runs_each_command_on_success():
    lines, emit = make_emit()
    calls = []

    ok = agents.install_provider(
        agents._provider("claude"),
        dry_run=False,
        run=lambda command, args: calls.append((command, args)) or 0,
        emit=emit,
    )

    assert ok is True
    assert [command for command, _ in calls] == ["claude", "claude"]
    assert any("Готово" in line for line in lines)


def test_install_provider_stops_and_reports_failure():
    lines, emit = make_emit()
    calls = []

    def run(command, args):
        calls.append((command, args))
        return 1

    ok = agents.install_provider(agents._provider("claude"), dry_run=False, run=run, emit=emit)

    assert ok is False
    assert len(calls) == 1
    assert any("Не удалось" in line for line in lines)


def test_select_providers_interactive_cancel_returns_empty():
    lines, emit = make_emit()

    selected = agents.select_providers_interactive(list(agents.PROVIDERS), prompt=lambda _: "0", emit=emit)

    assert selected == []


def test_select_providers_interactive_all_returns_every_provider():
    lines, emit = make_emit()

    selected = agents.select_providers_interactive(list(agents.PROVIDERS), prompt=lambda _: "A", emit=emit)

    assert selected == list(agents.PROVIDERS)


def test_select_providers_interactive_numbers_dedupe_and_skip_invalid():
    providers = list(agents.PROVIDERS)
    lines, emit = make_emit()

    selected = agents.select_providers_interactive(providers, prompt=lambda _: "1, 1, 9, x", emit=emit)

    assert selected == [providers[0]]


def test_select_providers_interactive_empty_input_returns_empty():
    lines, emit = make_emit()

    selected = agents.select_providers_interactive(list(agents.PROVIDERS), prompt=lambda _: "", emit=emit)

    assert selected == []


def test_run_agents_list_prints_all_providers():
    lines, emit = make_emit()

    code = agents.run_agents("list", emit=emit)

    assert code == 0
    assert any("claude" in line for line in lines)
    assert any("codex" in line for line in lines)


def test_run_agents_only_rejects_unknown_agent():
    lines, emit = make_emit()

    code = agents.run_agents("install", only=("ghost",), emit=emit)

    assert code == 2
    assert any("Неизвестный агент" in line for line in lines)


def test_run_agents_only_installs_selected_bypassing_detection():
    lines, emit = make_emit()
    calls = []

    code = agents.run_agents(
        "install",
        only=("codex",),
        which=lambda command: None,
        run=lambda command, args: calls.append(command) or 0,
        emit=emit,
    )

    assert code == 0
    assert calls == ["npx"]
    assert any("Установлено" in line for line in lines)


def test_run_agents_reports_no_agent_detected():
    lines, emit = make_emit()

    code = agents.run_agents("install", which=lambda command: None, emit=emit)

    assert code == 1
    assert any("не найдены" in line for line in lines)


def test_run_agents_all_installs_every_detected_agent():
    lines, emit = make_emit()
    calls = []

    code = agents.run_agents(
        "install",
        install_all=True,
        which=lambda command: "/path",
        run=lambda command, args: calls.append(command) or 0,
        emit=emit,
    )

    assert code == 0
    assert calls == ["claude", "claude", "npx"]


def test_run_agents_interactive_cancel_returns_zero():
    lines, emit = make_emit()

    code = agents.run_agents(
        "install",
        which=lambda command: "/path",
        prompt=lambda _: "0",
        emit=emit,
    )

    assert code == 0
    assert any("отменена" in line.lower() for line in lines)


def test_run_agents_interactive_install_reports_failure_exit_code():
    lines, emit = make_emit()

    code = agents.run_agents(
        "install",
        which=lambda command: "/path",
        prompt=lambda _: "1",
        run=lambda command, args: 1,
        emit=emit,
    )

    assert code == 1
    assert any("Ошибки" in line for line in lines)


def test_default_run_returns_process_exit_code():
    assert agents._default_run(sys.executable, ["-c", "raise SystemExit(0)"]) == 0


def test_default_run_missing_command_returns_127():
    assert agents._default_run("sfu-converter-no-such-binary-xyz", []) == 127
