# Task 09: Extract Renderer Behind Ports

## Priority: High
## Phase: Phase 5 (Renderer and validator rewrite)
## Affected files: NEW `src/sfu_converter/ports/`, NEW `src/sfu_converter/infrastructure/`, MODIFY `src/sfu_converter/converter.py`
## References: `docs/technical requirements/02_clean_architecture.md`

## Summary

Move DOCX rendering logic out of `converter.py` into infrastructure adapters behind abstract ports. The application layer must not import `python-docx`.

## Detailed Implementation

### 1. Create port interfaces

```
src/sfu_converter/ports/
├── __init__.py
├── renderer.py       # Abstract renderer port
├── file_io.py        # Abstract file I/O port
├── image_resolver.py # Abstract image resolver
└── template.py       # Abstract template port
```

#### `ports/renderer.py`

```python
from abc import ABC, abstractmethod
from ..domain.ast_nodes import Document
from ..domain.formatting import FormattingProfile
from ..domain.diagnostics import Diagnostic


class RendererPort(ABC):
    @abstractmethod
    def render(self, document: Document, profile: FormattingProfile,
               template_path: str | None = None) -> bytes:
        """Render Document AST to DOCX bytes."""
        ...

    @abstractmethod
    def render_to_file(self, document: Document, profile: FormattingProfile,
                       output_path: str, template_path: str | None = None) -> list[Diagnostic]:
        """Render Document AST to a DOCX file."""
        ...
```

### 2. Create infrastructure adapter

```
src/sfu_converter/infrastructure/
├── __init__.py
├── docx_renderer.py  # python-docx implementation of RendererPort
└── filesystem.py     # Concrete file I/O
```

#### `infrastructure/docx_renderer.py`

Move all `python-docx` specific code from `converter.py` here:
- `_set_run_style()` → method on adapter
- `_set_paragraph_format()` → method on adapter
- `_add_empty_paragraph()` → method on adapter
- `_insert_image()` → method on adapter
- `_create_table()` → method on adapter
- `_setup_document_margins()` → method on adapter
- `_load_template()` / `_initialize_document()` → method on adapter

The adapter accepts AST nodes and a FormattingProfile, not raw text lines.

### 3. Create application use case

```python
# src/sfu_converter/application/convert.py
from ..domain.ast_nodes import Document
from ..domain.diagnostics import Diagnostic
from ..domain.formatting import FormattingProfile
from ..ports.renderer import RendererPort
from ..parser.base import BaseParser


class ConvertTextToDocx:
    def __init__(self, parser: BaseParser, renderer: RendererPort):
        self._parser = parser
        self._renderer = renderer

    def execute(self, source: str, profile: FormattingProfile,
                output_path: str, template_path: str | None = None,
                filename: str | None = None) -> list[Diagnostic]:
        result = self._parser.parse(source, filename)
        diagnostics = list(result.diagnostics)
        render_diags = self._renderer.render_to_file(
            result.document, profile, output_path, template_path
        )
        diagnostics.extend(render_diags)
        return diagnostics
```

### 4. Keep `converter.py` as compatibility wrapper

During migration, `TextToDocxConverter` wraps the new use case:
```python
class TextToDocxConverter:
    def convert_file(self, input_file, output_file, template=None):
        source = Path(input_file).read_text(encoding='utf-8')
        use_case = ConvertTextToDocx(V1Parser(), DocxRenderer(self.config))
        use_case.execute(source, default_profile, output_file, template, input_file)
```

## Dependency Rule

- `domain/` → no external imports
- `ports/` → imports only `domain/`
- `application/` → imports `domain/` and `ports/` (abstract only)
- `infrastructure/` → imports `domain/`, `ports/`, and `python-docx`
- `cli.py` → wires infrastructure into application

## Tests

- Unit test `DocxRenderer` with known AST input → verify DOCX structure
- Test `ConvertTextToDocx` use case with mock renderer
- Import boundary test: verify `application/` never imports `python-docx`
- Integration test: full pipeline from TXT to DOCX

## Verification

1. All existing tests still pass
2. `python -m pytest` — no regressions
3. `grep -r "from docx" src/sfu_converter/application/` returns nothing
4. `grep -r "from docx" src/sfu_converter/domain/` returns nothing
