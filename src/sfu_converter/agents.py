"""Установка навыков sfu-converter в поддерживаемые AI-агенты.

Команды агентов забирают плагин из репозитория на GitHub, поэтому локальные
файлы при установке не требуются. Все сообщения и интерактивное меню — на
русском языке.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

REPO = "bounchich1/sfu_converter"
PLUGIN_ID = "sfu-converter"


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    command: str
    mechanism: str


PROVIDERS: tuple[Provider, ...] = (
    Provider("claude", "Claude Code", "claude", "claude plugin install"),
    Provider("codex", "Codex CLI", "codex", "npx skills add -a codex"),
)

Runner = Callable[[str, list[str]], int]
Emitter = Callable[[str], None]
Which = Callable[[str], str | None]
Prompt = Callable[[str], str]


def _provider(provider_id: str) -> Provider | None:
    for provider in PROVIDERS:
        if provider.id == provider_id:
            return provider
    return None


def _install_commands(provider: Provider) -> list[tuple[str, list[str]]]:
    if provider.id == "claude":
        return [
            ("claude", ["plugin", "marketplace", "add", REPO]),
            ("claude", ["plugin", "install", f"{PLUGIN_ID}@{PLUGIN_ID}"]),
        ]
    return [("npx", ["-y", "skills", "add", REPO, "-a", "codex", "--yes", "--all"])]


def _default_run(command: str, args: list[str]) -> int:
    try:
        return subprocess.run([command, *args], check=False).returncode
    except FileNotFoundError:
        return 127


def detect_available(which: Which = shutil.which) -> list[Provider]:
    return [provider for provider in PROVIDERS if which(provider.command)]


def install_provider(
    provider: Provider,
    *,
    dry_run: bool,
    run: Runner = _default_run,
    emit: Emitter = print,
) -> bool:
    emit(f">> {provider.label} ({provider.mechanism})")
    for command, args in _install_commands(provider):
        printable = f"{command} {' '.join(args)}"
        if dry_run:
            emit(f"  демо-запуск: {printable}")
            continue
        emit(f"  $ {printable}")
        if run(command, args) != 0:
            emit(f"  [x] Не удалось установить {provider.label}")
            return False
    if not dry_run:
        emit(f"  [ok] Готово: {provider.label}")
    return True


def select_providers_interactive(
    providers: Sequence[Provider],
    *,
    prompt: Prompt = input,
    emit: Emitter = print,
) -> list[Provider]:
    emit("Доступные агенты:")
    for index, provider in enumerate(providers, 1):
        emit(f"  {index}. {provider.label}")
    emit(f"  A. Установить во все ({len(providers)})")
    emit("  0. Отмена")

    choice = prompt("Выберите агенты (номера через запятую или 'a'): ").strip().lower()

    if choice in {"", "0"}:
        return []
    if choice == "a":
        return list(providers)

    selected: list[Provider] = []
    for token in choice.split(","):
        token = token.strip()
        if not token.isdigit():
            continue
        index = int(token) - 1
        if 0 <= index < len(providers) and providers[index] not in selected:
            selected.append(providers[index])
    return selected


def _print_list(emit: Emitter) -> None:
    emit("Поддерживаемые агенты:")
    for provider in PROVIDERS:
        emit(f"  {provider.id:<7} {provider.label:<12} {provider.mechanism}")


def run_agents(
    action: str = "install",
    *,
    only: Iterable[str] = (),
    install_all: bool = False,
    dry_run: bool = False,
    which: Which = shutil.which,
    run: Runner = _default_run,
    prompt: Prompt = input,
    emit: Emitter = print,
) -> int:
    if action == "list":
        _print_list(emit)
        return 0

    only = tuple(only)
    if only:
        selected: list[Provider] = []
        for agent_id in only:
            provider = _provider(agent_id)
            if provider is None:
                emit(f"Неизвестный агент: {agent_id}")
                return 2
            selected.append(provider)
    else:
        available = detect_available(which=which)
        if not available:
            emit("Поддерживаемые агенты не найдены. Установите Claude Code или Codex CLI.")
            return 1
        if install_all:
            selected = available
        else:
            selected = select_providers_interactive(available, prompt=prompt, emit=emit)
            if not selected:
                emit("Установка отменена.")
                return 0

    installed: list[str] = []
    failed: list[str] = []
    for provider in selected:
        if install_provider(provider, dry_run=dry_run, run=run, emit=emit):
            installed.append(provider.id)
        else:
            failed.append(provider.id)

    if installed:
        emit("Установлено: " + ", ".join(installed))
    if failed:
        emit("Ошибки: " + ", ".join(failed))
        return 1
    return 0
