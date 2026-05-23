# Task 03: Set Up Installable Package Structure

## Priority: High
## Phase: Phase 1 (Package and baseline CLI)
## Affected files: NEW `pyproject.toml`, NEW `src/sfu_converter/__init__.py`, NEW `src/sfu_converter/__main__.py`, MOVE all existing `src/*.py` into `src/sfu_converter/`

## Summary

Convert the flat `src/` directory into a proper installable Python package `sfu_converter` so that `python -m sfu_converter` works and the project can be installed with `pip install -e .`.

## Detailed Steps

### 1. Create `pyproject.toml` in project root

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "sfu-converter"
version = "0.1.0"
description = "TXT to DOCX converter with SFU formatting standards"
requires-python = ">=3.10"
dependencies = [
    "python-docx>=1.1.0",
    "Pillow>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "coverage[toml]>=7.0",
]

[project.scripts]
sfu-converter = "sfu_converter.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["sfu_converter"]
branch = true

[tool.coverage.report]
fail_under = 0
show_missing = true
```

### 2. Create package directory structure

```
sfu_converter-main/
├── src/
│   └── sfu_converter/
│       ├── __init__.py          # Package marker, version
│       ├── __main__.py          # python -m sfu_converter entry point
│       ├── main.py              # Existing main.py (updated imports)
│       ├── config.py            # Existing config.py
│       ├── converter.py         # Existing converter.py (updated imports)
│       ├── menu.py              # Existing menu.py (updated imports)
│       ├── utils_image_insert.py # Existing (updated imports)
│       └── validator.py         # Existing validator.py (updated imports)
```

### 3. Create `src/sfu_converter/__init__.py`

```python
"""SFU TXT-to-DOCX converter."""
__version__ = "0.1.0"
```

### 4. Create `src/sfu_converter/__main__.py`

```python
"""Entry point for python -m sfu_converter."""
from sfu_converter.main import main

if __name__ == "__main__":
    main()
```

### 5. Update all internal imports

Every `from config import SIBFUConfig` becomes `from sfu_converter.config import SIBFUConfig`, and similarly for all cross-module imports. Specifically:

- `converter.py`: `from config import` → `from sfu_converter.config import`
- `converter.py`: `from utils_image_insert import` → `from sfu_converter.utils_image_insert import`
- `validator.py`: `from config import` → `from sfu_converter.config import`
- `menu.py`: update any local imports
- `main.py`: update all local imports, remove `sys.path` hacks if any

### 6. Update `requirements.txt` (keep for backward compat)

```
python-docx>=1.1.0
Pillow>=10.0.0
```

### 7. Update test imports

All test files must change from `from converter import` to `from sfu_converter.converter import`, etc. Remove any `sys.path.insert` hacks from test files.

### 8. Add `setuptools` package discovery to `pyproject.toml`

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

## Verification

1. `pip install -e .` succeeds
2. `python -m sfu_converter` starts the interactive menu
3. `sfu-converter` command is available (from project.scripts)
4. `python -m pytest tests/` — all existing tests pass
5. Imports work without `sys.path` hacks
