# Task 27: DRY Hardening and Documentation Generation

## Priority: Low
## Phase: Phase 7 (DRY hardening)
## Affected files: Various
## References: `docs/technical requirements/07_dry_maintainability.md`

## Summary

Final pass to eliminate all remaining duplication and add automated documentation generation.

## Actions

### 1. Import boundary tests

Create `tests/test_architecture.py`:
```python
import ast
import importlib
from pathlib import Path

def test_domain_has_no_infrastructure_imports():
    """Domain layer must not import python-docx, argparse, or infrastructure."""
    domain_dir = Path('src/sfu_converter/domain')
    forbidden = {'docx', 'argparse', 'sfu_converter.infrastructure', 'sfu_converter.cli'}
    
    for py_file in domain_dir.glob('*.py'):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split('.')[0] not in forbidden, \
                        f"{py_file.name} imports forbidden module: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module.split('.')[0] not in forbidden, \
                        f"{py_file.name} imports from forbidden module: {node.module}"

def test_application_has_no_docx_imports():
    """Application layer must not import python-docx."""
    app_dir = Path('src/sfu_converter/application')
    if not app_dir.exists():
        return
    for py_file in app_dir.glob('*.py'):
        content = py_file.read_text()
        assert 'from docx' not in content, f"{py_file.name} imports docx"
        assert 'import docx' not in content, f"{py_file.name} imports docx"
```

### 2. Duplicate code detection

Add `pylint` or `flake8` with duplicate code detection:
```bash
pip install pylint
pylint --disable=all --enable=duplicate-code src/sfu_converter/
```

Or use `jscpd`:
```bash
npx jscpd src/sfu_converter/ --min-lines 5 --min-tokens 50
```

### 3. Generate CLI help from metadata

The `explain-syntax` command should generate output from the parser's metadata:
```python
def cmd_explain_syntax(args):
    version = args.syntax_version
    syntax_spec = get_syntax_spec(version)  # Generated from parser metadata
    if args.format == 'json':
        print(json.dumps(syntax_spec))
    else:
        for block in syntax_spec['blocks']:
            print(f"  {block['name']}: {block['description']}")
            print(f"  Example: {block['example']}")
```

### 4. Ensure no formatting constants outside registry

Grep for any remaining `Pt(14)`, `Cm(1.25)`, `'Times New Roman'` outside the config/registry module. All should be references to the canonical source.

### 5. Add linting configuration

Add to `pyproject.toml`:
```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B"]
```

## Tests

- Import boundary tests pass
- No duplicate code detected above threshold
- `explain-syntax` output matches parser capabilities
- grep for hardcoded constants returns only registry/config

## Verification

1. `python -m pytest tests/test_architecture.py` passes
2. `ruff check src/` has no errors
3. No formatting constants outside registry
