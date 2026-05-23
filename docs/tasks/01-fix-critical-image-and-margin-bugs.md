# Task 01: Fix Critical Image and Margin Bugs

## Priority: CRITICAL
## Phase: Immediate hotfix
## Affected files: `src/config.py`, `src/utils_image_insert.py`

## Summary

Three critical numerical bugs cause images to render at postage-stamp size and page margins to violate the SFU standard.

## Bug 1: IMAGE max_width is 100x too small

**File:** `src/config.py`, line 111
**Current:** `'max_width': Cm(1.5)` (1.5 cm ≈ 0.6 inches)
**Expected:** `'max_width': Cm(15)` (15 cm — fits within the text area of a page with 3cm left + 1cm right margin on A4)
**Impact:** All inserted images are scaled down to ~1.5cm wide, making them unreadable.

### Fix
```python
# src/config.py, line 111
# BEFORE:
'max_width': Cm(1.5),
# AFTER:
'max_width': Cm(15),
```

## Bug 2: EMU-to-cm conversion uses wrong divisor (10x error)

**File:** `src/utils_image_insert.py`, lines 81, 126, 136
**Current:** Divides by `36000` (comment says "36000 EMU = 1 cm")
**Correct:** 1 cm = 360,000 EMU (not 36,000). Since `Cm()` constructor multiplies by 360,000, passing `emu / 36000` into `Cm()` produces a value 10x too large.

### Fix
Replace all three occurrences:

```python
# Line 81
# BEFORE:
return Cm(emu / 36000)  # 36000 EMU = 1 cm
# AFTER:
return Cm(emu / 360000)  # 360000 EMU = 1 cm

# Line 126
# BEFORE:
height = Cm(width.emu * aspect_ratio / 36000)
# AFTER:
height = Cm(width.emu * aspect_ratio / 360000)

# Line 136
# BEFORE:
width = Cm(height.emu * inv_aspect / 36000)
# AFTER:
width = Cm(height.emu * inv_aspect / 360000)
```

## Bug 3: Right margin violates SFU standard

**File:** `src/config.py`, line 100
**Current:** `'right': Cm(1.5)` (15mm)
**Expected:** `'right': Cm(1)` (10mm per STU 7.5-07-2021, documented in `docs/formatting requirements/common.md`)

### Fix
```python
# src/config.py, line 100
# BEFORE:
'right': Cm(1.5)
# AFTER:
'right': Cm(1)
```

## Verification

1. Run existing tests: `python -m pytest tests/`
2. Convert a sample file with an image and verify the image fills most of the page width
3. Open the resulting DOCX and check right margin is 1cm in Page Setup
4. Compare IMAGE max_width against page text area: A4 width (21cm) - left margin (3cm) - right margin (1cm) = 17cm. Value of 15cm leaves comfortable padding.

## Tests to add

- Unit test asserting `SIBFUConfig.IMAGE['max_width'] == Cm(15)`
- Unit test asserting `SIBFUConfig.MARGINS['right'] == Cm(1)`
- Unit test for `_from_emu_to_cm` verifying `_from_emu_to_cm(360000) == Cm(1)`
- Unit test for `calculate_image_dimensions` with known pixel sizes verifying output is sane (not 10x scaled)
