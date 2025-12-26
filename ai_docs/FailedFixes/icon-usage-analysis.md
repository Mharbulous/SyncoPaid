# Icon Usage Analysis

**Date**: 2025-12-26
**Status**: RESOLVED - Using pre-generated PNG for feedback state

## Icon Inventory

| Icon File | Used? | Purpose |
|-----------|-------|---------|
| `stopwatch-pictogram-green.ico` | Yes | Active tracking state |
| `stopwatch-pictogram-faded.ico` | Yes | Inactive/quitting states |
| `stopwatch-paused.ico` | Yes | Paused state |
| `stopwatch-feedback.png` | Yes | Feedback flash (pre-generated 64x64 PNG) |
| `SYNCOPaiD.ico` | Yes | Main window icon + exe icon |

## System Tray Icon Flow

```mermaid
flowchart TD
    subgraph States["Tray Icon States"]
        ON["state = 'on'"]
        PAUSED["state = 'paused'"]
        INACTIVE["state = 'inactive'"]
        FEEDBACK["state = 'feedback'"]
        QUITTING["state = 'quitting'"]
    end

    subgraph Icons["Icon Files"]
        GREEN["stopwatch-pictogram-green.ico"]
        FADED["stopwatch-pictogram-faded.ico"]
        PAUSE_ICO["stopwatch-paused.ico"]
        FEEDBACK_PNG["stopwatch-feedback.png"]
    end

    subgraph Processing["Image Processing"]
        LOAD_ICO["PIL Image.open()\nconvert('RGBA')\nresize(64x64)\ninfo.clear()"]
        LOAD_PNG["PIL Image.open()\nconvert('RGBA')"]
        SLEEP_OVL["add_sleep_overlay()"]
        PAUSE_OVL["add_pause_overlay()"]
    end

    subgraph Output["Final Icon"]
        PYSTRAY["pystray Icon"]
    end

    ON --> GREEN --> LOAD_ICO --> PYSTRAY
    FEEDBACK --> FEEDBACK_PNG --> LOAD_PNG --> PYSTRAY
    PAUSED --> PAUSE_ICO --> LOAD_ICO --> PAUSE_OVL --> PYSTRAY
    INACTIVE --> FADED --> LOAD_ICO --> SLEEP_OVL --> PYSTRAY
    QUITTING --> FADED
```

## Main Window Icon Flow

```mermaid
flowchart LR
    subgraph Source["Icon Source"]
        SYNCO["SYNCOPaiD.ico"]
    end

    subgraph Usage["Usage Locations"]
        WINDOW["Main Window\n(main_ui_utilities.py:54)"]
        EXE["Executable Icon\n(SyncoPaid.spec:56)"]
    end

    SYNCO --> WINDOW
    SYNCO --> EXE
```

## PyInstaller Bundle

```mermaid
flowchart TD
    subgraph Bundled["Bundled in .exe (SyncoPaid.spec)"]
        B1["SYNCOPaiD.ico"]
        B2["stopwatch-pictogram-faded.ico"]
        B3["stopwatch-paused.ico"]
        B4["stopwatch-pictogram-green.ico"]
        B5["stopwatch-feedback.png"]
    end

    style B5 fill:#ccffcc
```

## Resolution

The orange ICO invisibility issue was resolved by using a **pre-generated PNG** instead of:
- Loading orange ICO files directly (all failed)
- Runtime recoloring of green ICO (worked but was "ad hoc")

### Why PNG Works

1. PNG format is simpler and doesn't have ICO's multi-size complexity
2. The PNG is pre-generated at 64x64 (exact size needed for system tray)
3. No ICO metadata that could conflict with pystray's serialization

### Files Removed

The following orphaned files were deleted:
- `stopwatch-pictogram-orange.ico` - rendered invisible on Windows
- `stopwatch-pictogram-orange2.ico` - regeneration attempt, also invisible

### Root Cause (Unconfirmed)

The exact root cause of why orange ICO files rendered invisible was never identified. Likely hypotheses:
- PIL-saved ICOs differ from Inkscape-created ICOs in ways Windows rejects
- Color-specific rendering issues in Windows icon handling
- ICO metadata conflicts with pystray's serialization

The PNG solution bypasses all these potential issues.
