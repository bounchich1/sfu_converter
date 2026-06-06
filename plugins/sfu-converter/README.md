# sfu-converter plugin

Claude Code plugin: agent skill for generating Siberian Federal University (СФУ) academic reports in V2 TXT syntax and converting to DOCX via the `sfu-converter` CLI.

## What it does

Triggers when user asks for SFU-formatted documents (lab work, coursework, VKR, practice / research reports). Skill writes V2 TXT, lints with `sfu-converter lint`, fixes diagnostics, converts to DOCX with `sfu-converter convert --validate-output`.

## Install (Claude Code)

```text
/plugin marketplace add Nikita2005qwe/sfu_converter
/plugin install sfu-converter@sfu-converter
```

## Prerequisite: install the CLI

Plugin only ships the skill. CLI must be installed separately:

```bash
git clone https://github.com/Nikita2005qwe/sfu_converter.git
cd sfu_converter
pip install -e ".[dev]"
```

After install, `sfu-converter --help` must work in the shell Claude Code uses.

## Skill source

Single skill: `skills/sfu-converter/SKILL.md`. See it for full V2 syntax reference, profile table, diagnostic-fix table, and idiomatic skeletons (lab / coursework / VKR).

## Usage

After install, in any project:

```
сделай лабу №3 на тему «Реализация REST API на FastAPI».
Студент: Иванов И.И., группа КИ22-01, руководитель Петров А.В., год 2025.
```

Skill auto-triggers, asks for missing metadata, writes TXT, lints, converts.
