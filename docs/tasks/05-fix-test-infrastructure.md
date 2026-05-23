# Task 05: Fix Test Infrastructure

## Priority: Medium
## Phase: Phase 1
## Affected files: `tests/test_picture_insert.py`, `tests/check_cyrillic_markers.py`, `tests/fix_cyrillic_markers.py`

## Summary

Three files in `tests/` are not proper pytest tests and/or are misplaced utilities. Fix them.

## Issue 1: `test_picture_insert.py` is a standalone script, not pytest

This file uses `print()` statements and has no `test_` functions or assertions. It generates output files.

### Fix

Rewrite as proper pytest test class:

```python
# tests/test_picture_insert.py
import pytest
from pathlib import Path
from PIL import Image
from docx import Document
from sfu_converter.utils_image_insert import (
    convert_image_to_rgb,
    calculate_image_dimensions,
    save_image_to_buffer,
    insert_image,
)
from sfu_converter.config import SIBFUConfig


@pytest.fixture
def sample_image(tmp_path):
    """Create a small test PNG image."""
    img = Image.new('RGB', (200, 100), color='red')
    path = tmp_path / 'test.png'
    img.save(str(path))
    return path


@pytest.fixture
def rgba_image(tmp_path):
    """Create a test RGBA image with transparency."""
    img = Image.new('RGBA', (200, 100), color=(255, 0, 0, 128))
    path = tmp_path / 'test_rgba.png'
    img.save(str(path))
    return path


class TestConvertImageToRgb:
    def test_rgb_passthrough(self, sample_image):
        img = Image.open(str(sample_image))
        result = convert_image_to_rgb(img)
        assert result.mode == 'RGB'

    def test_rgba_conversion(self, rgba_image):
        img = Image.open(str(rgba_image))
        result = convert_image_to_rgb(img)
        assert result.mode == 'RGB'


class TestCalculateImageDimensions:
    def test_dimensions_within_max_width(self):
        # Test that images wider than max_width are scaled down
        from docx.shared import Cm
        width, height = calculate_image_dimensions(
            original_size=(1000, 500),
            width=None,
            height=None,
            max_width=Cm(15),
            dpi=96
        )
        assert width is not None
        assert height is not None


class TestInsertImage:
    def test_insert_into_document(self, sample_image, tmp_path):
        import logging
        doc = Document()
        config = SIBFUConfig.IMAGE
        logger = logging.getLogger('test')
        insert_image(doc, str(sample_image), config, logger)
        output = tmp_path / 'output.docx'
        doc.save(str(output))
        assert output.exists()
```

## Issue 2: Cyrillic utilities are misplaced in `tests/`

`check_cyrillic_markers.py` and `fix_cyrillic_markers.py` are maintenance/diagnostic tools, not tests.

### Fix

1. Create `src/sfu_converter/tools/` directory
2. Move both files there:
   - `src/sfu_converter/tools/__init__.py`
   - `src/sfu_converter/tools/check_cyrillic_markers.py`
   - `src/sfu_converter/tools/fix_cyrillic_markers.py`
3. Update README references to new locations
4. Add proper `if __name__ == '__main__'` guards
5. Write actual pytest tests for the cyrillic detection/fix logic in `tests/test_cyrillic_tools.py`

## Verification

1. `python -m pytest tests/` — all tests pass including rewritten picture tests
2. `python -m sfu_converter.tools.check_cyrillic_markers` still works
3. No standalone scripts remain in `tests/` (only proper pytest files)
