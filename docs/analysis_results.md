# SFU Converter: Docs vs Source Analysis

## Inconsistencies Found

### 🔴 Critical Bugs (Code Contradicts Standard)

| # | Issue | Location | Expected (from docs) | Actual (in code) |
|---|-------|----------|---------------------|-------------------|
| 1 | **Image max_width is 100x too small** | [config.py:111](file:///m:/sfu_converter-main/src/config.py#L111) | ~`Cm(15)` (fits in text area) | `Cm(1.5)` — images render at postage-stamp size |
| 2 | **EMU conversion 10x error** | [utils_image_insert.py:81,126,136](file:///m:/sfu_converter-main/src/utils_image_insert.py#L81) | `360000` EMU = 1 cm | Code uses `36000`, producing 10x scaling |
| 3 | **Right margin violates standard** | [config.py:100](file:///m:/sfu_converter-main/src/config.py#L100) | `Cm(1)` (10mm per STU 7.5-07-2021) | `Cm(1.5)` (15mm) |

### 🟡 Doc-to-Code Inconsistencies

| # | Issue | Details |
|---|-------|---------|
| 4 | **README references non-existent files** | [README.md:140-141](file:///m:/sfu_converter-main/README.md#L140-L141) references `docs/sfu-standard-audit.md` and `docs/superpowers/plans/2026-04-18-sfu-standard-compliance.md` — neither exist |
| 5 | **`validate_line_spacing()` defined but never called** | [validator.py:80](file:///m:/sfu_converter-main/src/validator.py#L80) defines the method, but [validate_file()](file:///m:/sfu_converter-main/src/validator.py#L93-L144) never invokes it — line spacing is silently unvalidated |
| 6 | **Header detection false positives** | [validator.py:26-31](file:///m:/sfu_converter-main/src/validator.py#L26-L31) — `_is_header_paragraph()` only checks center alignment, so image captions and other centered elements are misidentified as headers |
| 7 | **Magic number instead of proper conversion** | [validator.py:73](file:///m:/sfu_converter-main/src/validator.py#L73) — `1.25 * 28.3465` hardcoded instead of using `Cm(1.25).pt` |
| 8 | **Only first run validated** | [validator.py:119](file:///m:/sfu_converter-main/src/validator.py#L119) — `para.runs[0]` only checks first run, missing mixed formatting |

### 🟠 Documentation Quality Issues

The **formatting requirements** and **technical requirements** are actually **well-written** — they are detailed, structured, and internally consistent. No badly written requirements were found.

However:
- The technical requirements describe a comprehensive rewrite (clean architecture, AST, CLI, 100% coverage) that the current code is **very far from achieving**
- The formatting requirements document 20+ formatting rules that remain **completely unimplemented**

---

## Feature Implementation Gap

### ✅ Implemented
| Feature | Status |
|---------|--------|
| Times New Roman 14pt | ✅ |
| Justified body text | ✅ |
| First-line indent 1.25cm | ✅ |
| Line spacing 1.5 | ✅ |
| H1/H2/H3 headings | ✅ |
| Image insertion with caption | ✅ |
| Table creation with headers | ✅ |
| Page margins (with wrong right margin) | ⚠️ |

### ❌ Not Implemented (required by STU 7.5-07-2021)
| Feature | Priority |
|---------|----------|
| Page numbering (Arabic, centered bottom, 14pt) | High |
| Structural sections (ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ etc.) | High |
| Section/subsection numbering (1, 1.1, 1.1.1) | High |
| Table of contents | Medium |
| Title page generation | Medium |
| Lists/enumerations (hyphens, letters, numbers) | Medium |
| Inline bold/italic formatting | Medium |
| Formulas (centered, numbered, explanations) | Medium |
| Bibliography/source list | Medium |
| Appendices (letter designation) | Medium |
| Table font 10-12pt | Medium |
| Multi-page table "Продолжение таблицы" header | Medium |
| Heading: no period at end | Low |
| Heading: no word hyphenation | Low |
| Landscape orientation | Low |
| Footnotes | Low |

---

## Architecture & Refactoring Gaps

| Area | Issue |
|------|-------|
| **No CLI** | Interactive menu only — no `argparse`, no automation |
| **No AST** | Parsing and DOCX rendering coupled in `_render_lines()` |
| **No package structure** | Not pip-installable, no `pyproject.toml` |
| **DRY violations** | 13-branch `if/elif` in `_set_paragraph_format()` |
| **String-based dispatch** | Typos silently produce unstyled paragraphs |
| **No coverage tooling** | `pytest-cov` not installed |
| **Misplaced test utilities** | Cyrillic checker/fixer in `tests/` are not tests |
| **Standalone test script** | `test_picture_insert.py` uses `print()`, not `pytest` |
| **No version pinning** | `requirements.txt` has no versions |

---

## Task Plan: 28 Tasks Created

Tasks are in [`docs/tasks/`](file:///m:/sfu_converter-main/docs/tasks) numbered 01-28:

### 🔴 Immediate Fixes (Tasks 01-02)
- **01** — Fix critical image/margin bugs (3 bugs)
- **02** — Fix README broken doc references

### 🏗️ Infrastructure (Tasks 03-05)
- **03** — Set up installable package structure (`pyproject.toml`)
- **04** — Add coverage tooling and dev dependencies
- **05** — Fix test infrastructure (convert scripts to pytest, move utilities)

### 🧱 Architecture (Tasks 06-09)
- **06** — Create domain AST model (dataclasses for all block types)
- **07** — Extract V1 parser from `converter.py`
- **08** — Add CLI foundation (`argparse` with all commands)
- **09** — Extract renderer behind abstract ports

### 📐 Formatting Registry (Tasks 10-11)
- **10** — Implement formatting rule registry with rule IDs and profiles
- **11** — Refactor `_set_paragraph_format()` to data-driven dispatch

### ✨ Features (Tasks 12-22)
- **12** — Page numbering
- **13** — Structural sections (ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ, etc.)
- **14** — Section/subsection numbering (1, 1.1, 1.1.1)
- **15** — List formatting (bullet, lettered, numbered)
- **16** — Inline text formatting (bold/italic)
- **17** — Enhanced table formatting (font size, multi-page, captions)
- **18** — Formula support (centered, numbered, explanations)
- **19** — Bibliography / source list
- **20** — Appendices
- **21** — Table of contents
- **22** — Title page generation

### 🔌 Template & Syntax (Tasks 23-24)
- **23** — Template composition (preserve title pages, insertion points)
- **24** — V2 TXT syntax (explicit, agent-friendly)

### ✅ Quality (Tasks 25-28)
- **25** — Rewrite validator with rule IDs and fix bugs
- **26** — Remove hardcoded paths and magic numbers
- **27** — DRY hardening and documentation generation
- **28** — Enforce 100% statement+branch coverage gate
