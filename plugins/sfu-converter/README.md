# sfu-converter plugin

Claude Code plugin: a **multi-skill pack** for generating Siberian Federal University (СФУ)
academic documents in V2 TXT syntax and converting them to DOCX via the `sfu-converter` CLI.

## What it does

Triggers when the user asks for an SFU-formatted document. The matching profile skill shows the
document's **heading structure**, asks **who writes the opening sections** (user-provided vs
generated), writes V2 TXT, lints with `sfu-converter lint`, fixes error-level diagnostics, then converts with
`sfu-converter convert`.

## Skills

| Skill             | Document type                                    | Profile                          |
|-------------------|--------------------------------------------------|----------------------------------|
| `sfu-common`      | Shared syntax, lint/convert loop, diagnostics    | (base, loads with any profile)   |
| `sfu-report-lab`  | Лабораторная / практическая / проектная (default)| `lab_practical_project_reports`  |
| `sfu-coursework`  | Курсовая работа / курсовой проект                | `coursework`                     |
| `sfu-vkr`         | ВКР / диплом / магистерская диссертация          | `graduation_qualification_work`  |
| `sfu-research`    | Отчёт о НИР                                       | `research_reports`               |
| `sfu-practice`    | Отчёт по практике                                | `practice_reports`               |
| `sfu-small-works` | Реферат / контрольная / РГЗ / эссе               | `small_written_works`            |

Shared, profile-independent material lives in [`references/`](references/): `v2-syntax.md`,
`diagnostics.md`, `cli.md`, `metadata.md`. Profile skills stay short and link to these.

## Install (Claude Code)

```text
/plugin marketplace add Nikita2005qwe/sfu_converter
/plugin install sfu-converter@sfu-converter
```

## Prerequisite: install the CLI

The plugin ships only the skills. Install the converter separately (one line):

```bash
pipx install sfu-converter
# до выхода на PyPI: pipx install git+https://github.com/Nikita2005qwe/sfu_converter.git
```

After install, `sfu-converter --help` must work in the shell Claude Code uses. Full per-agent
matrix: [`docs/installation.md`](../../docs/installation.md).

## Usage

```text
сделай лабу №3 на тему «Реализация REST API на FastAPI».
Студент: Иванов И. И., группа КИ22-01, руководитель Петров А. В., год 2025.
```

The right profile skill auto-triggers, shows the heading structure, asks how to fill the first
sections, writes TXT, lints, and converts.
