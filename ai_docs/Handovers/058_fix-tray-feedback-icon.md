# Handover: Tray Feedback Icon Renders Invisible

**Branch**: `claude/fix-tray-icon-flash-4mUdP`
**Status**: Working runtime workaround in place, root cause unknown

## Problem

Left-clicking the system tray icon should flash orange for 1 second. Instead, any orange ICO file loaded from disk renders as invisible/blank on Windows.

## Current State

**Working workaround**: Runtime recoloring in `src/syncopaid/tray_icons.py:110-162`
- Loads `stopwatch-pictogram-green.ico` (works)
- Applies `recolor_green_to_orange()` pixel transformation in memory
- Result displays correctly as orange

**User dislikes this approach** - considers it "ad hoc and inelegant"

## Key Files

| File | Relevance |
|------|-----------|
| `src/syncopaid/tray_icons.py` | Icon loading, state mapping, recolor function |
| `src/syncopaid/tray_feedback.py` | Triggers feedback on left-click |
| `ai_docs/FailedFixes/tray-feedback-icon-invisible.md` | Previous investigation notes |
| `ai_docs/FailedFixes/icon-usage-analysis.md` | Mermaid diagrams of icon usage |

## Orphaned Files (Not Used)

- `src/syncopaid/assets/stopwatch-pictogram-orange.ico` - original, renders invisible
- `src/syncopaid/assets/stopwatch-pictogram-orange2.ico` - regenerated from SVG, also invisible

## What Fails

| Approach | Result |
|----------|--------|
| Load `stopwatch-pictogram-orange.ico` directly | Invisible |
| Regenerate orange ICO from SVG | Invisible |
| Generate ICO with PIL.save() from recolored pixels | Invisible |

## What Works

| Approach | Result |
|----------|--------|
| Load green ICO, recolor pixels in memory, pass to pystray | Orange icon displays correctly |
| Use `stopwatch-paused.ico` for feedback | Works, but same as pause state |

## Verified NOT the Cause

- File corruption (MD5 matches known working commit f4edfde5)
- ICO structure (9 images, 16-256px, 32bpp, valid headers)
- SVG source (identical structure to green, just different fill color)
- `image.info.clear()` call (tested without, no change)
- PIL pixel processing (all pixels valid, non-transparent count correct)

## Untested Theories

1. **ICO creation tool matters**: Working icons created by Inkscape/dedicated tool, failing ones possibly created differently
2. **PIL ICO save format**: PIL-saved ICOs have different internal format that Windows rejects
3. **Color profile/ICC data**: Orange ICO may have embedded color profile Windows doesn't handle
4. **Windows icon cache**: Unlikely but not definitively ruled out

## Technical Details

Orange vs green ICO comparison:
- Identical structure (9 sizes, BMP format, same offsets)
- File sizes differ slightly at 256x256 (PNG compressed)
- Both have `orNT` PNG chunk (non-standard, Inkscape-related)

Green center pixel: `(209, 255, 171, 255)`
Orange center pixel after recolor: `(255, 135, 0, 255)`

## Next Steps to Investigate

1. Create orange ICO using Inkscape directly (not PIL) - does it work?
2. Compare binary diff of working `stopwatch-paused.ico` vs failing `stopwatch-pictogram-orange.ico`
3. Test with different pystray/Pillow versions
4. Check if issue reproduces on different Windows machines

## Build Info

- PyInstaller 6.17.0
- Python 3.13.7
- Pillow (version in venv)
- pystray (version in venv)
- Windows 11 (10.0.26200)
