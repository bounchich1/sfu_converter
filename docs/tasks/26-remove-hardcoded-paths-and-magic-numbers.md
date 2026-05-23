# Task 26: Remove Hardcoded Paths and Magic Numbers

## Priority: Medium
## Phase: Phase 7 (DRY hardening)
## Affected files: `src/sfu_converter/menu.py`, `src/sfu_converter/converter.py`, `src/sfu_converter/validator.py`, `src/sfu_converter/main.py`
## References: `docs/technical requirements/07_dry_maintainability.md`

## Summary

Remove all hardcoded directory paths and magic numbers scattered across the codebase. Centralize into configuration.

## Issues to Fix

### 1. Hardcoded directory paths in `menu.py`

**Current:**
```python
# menu.py uses string literals:
examples_dir = os.path.join(base_dir, 'examples')
templates_dir = os.path.join(base_dir, 'templates')
results_dir = os.path.join(base_dir, 'results')
```

**Fix:** Move to configuration:
```python
# config.py or settings.py
class PathConfig:
    EXAMPLES_DIR = 'examples'
    TEMPLATES_DIR = 'templates'
    RESULTS_DIR = 'results'
    IMAGES_DIR = 'images'
    LOGS_DIR = 'logs'
    LOG_FILENAME = 'converter.log'
```

### 2. Magic number in `validator.py`

**Current (line 73):**
```python
expected_indent_pt = 1.25 * 28.3465  # Magic: cm-to-pt factor
```

**Fix:**
```python
from docx.shared import Cm
expected_indent_pt = Cm(1.25).pt
```

### 3. Hardcoded `'converter.log'` in `main.py`

**Fix:** Use `PathConfig.LOG_FILENAME`.

### 4. Fragile filename manipulation in `menu.py`

**Current:**
```python
txt_file.replace('.txt', '.docx')  # Breaks with "file.txt.backup.txt"
```

**Fix:**
```python
Path(txt_file).with_suffix('.docx')
```

### 5. `os.system('cls'/'clear')` in `menu.py`

**Fix:** Replace with `os.system` alternative or use `subprocess` with shell=False:
```python
import subprocess
import shutil

def clear_screen():
    if shutil.which('cls'):
        subprocess.run(['cmd', '/c', 'cls'], check=False)
    elif shutil.which('clear'):
        subprocess.run(['clear'], check=False)
```

Or simply use ANSI escape:
```python
def clear_screen():
    print('\033[2J\033[H', end='', flush=True)
```

### 6. Image caption detection patterns

**Current in converter.py:**
```python
if next_line.startswith('Рисунок') or next_line.startswith('Figure'):
```

**Fix:** Make configurable:
```python
CAPTION_PREFIXES = ['Рисунок', 'Figure', 'Рис.']
```

## Tests

- No raw string literals for directory names outside config
- `PathConfig` values are used consistently
- `Cm(1.25).pt` equals `1.25 * 28.3465` (regression test)
- `Path.with_suffix` handles edge cases
- grep for magic numbers: `28.3465`, `36000` should not appear

## Verification

1. `grep -rn '28.3465\|36000\|examples/' src/` returns only config references
2. All tests pass
3. Application behavior unchanged
