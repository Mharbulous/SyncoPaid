# Icon Usage Analysis

**Date**: 2025-12-26
**Purpose**: Document how ICO files are used in the codebase to understand the feedback icon issue.

## Icon Inventory

| Icon File | Used? | Purpose |
|-----------|-------|---------|
| `stopwatch-pictogram-green.ico` | ✓ | Active tracking state + feedback recolor source |
| `stopwatch-pictogram-faded.ico` | ✓ | Inactive/quitting states |
| `stopwatch-paused.ico` | ✓ | Paused state |
| `SYNCOPaiD.ico` | ✓ | Main window icon + exe icon |
| `stopwatch-pictogram-orange.ico` | ✗ | **UNUSED** - renders invisible |
| `stopwatch-pictogram-orange2.ico` | ✗ | **UNUSED** - regeneration attempt, also invisible |

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

    subgraph Icons["ICO Files"]
        GREEN["stopwatch-pictogram-green.ico"]
        FADED["stopwatch-pictogram-faded.ico"]
        PAUSE_ICO["stopwatch-paused.ico"]
        ORANGE["stopwatch-pictogram-orange.ico"]
    end

    subgraph Processing["Image Processing"]
        LOAD["PIL Image.open()"]
        CONVERT["convert('RGBA')"]
        RESIZE["resize(64x64)"]
        CLEAR["info.clear()"]
        RECOLOR["recolor_green_to_orange()"]
        SLEEP_OVL["add_sleep_overlay()"]
        PAUSE_OVL["add_pause_overlay()"]
    end

    subgraph Output["Final Icon"]
        PYSTRAY["pystray Icon"]
    end

    ON --> GREEN
    FEEDBACK --> GREEN
    PAUSED --> PAUSE_ICO
    INACTIVE --> FADED
    QUITTING --> FADED

    GREEN --> LOAD
    FADED --> LOAD
    PAUSE_ICO --> LOAD

    ORANGE -.->|"BROKEN: renders invisible"| LOAD

    LOAD --> CONVERT --> RESIZE --> CLEAR

    CLEAR --> RECOLOR
    CLEAR --> SLEEP_OVL
    CLEAR --> PAUSE_OVL
    CLEAR --> PYSTRAY

    RECOLOR -->|"feedback state only"| PYSTRAY
    SLEEP_OVL -->|"inactive state only"| PYSTRAY
    PAUSE_OVL -->|"paused state only"| PYSTRAY
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
    end

    subgraph NotBundled["NOT Bundled (orphaned files)"]
        N1["stopwatch-pictogram-orange.ico"]
        N2["stopwatch-pictogram-orange2.ico"]
    end

    style N1 fill:#ffcccc
    style N2 fill:#ffcccc
```

## The Feedback Icon Problem

```mermaid
flowchart TD
    subgraph Problem["Why Orange ICO Files Fail"]
        CLICK["User left-clicks tray"]
        WANT["Want: orange flash for 1 second"]

        subgraph Attempted["Approaches Tried"]
            A1["Use stopwatch-pictogram-orange.ico"]
            A2["Regenerate from SVG → orange2.ico"]
            A3["PIL-generate new ICO file"]
        end

        subgraph Results["Results"]
            R1["INVISIBLE"]
            R2["INVISIBLE"]
            R3["INVISIBLE"]
        end

        A1 --> R1
        A2 --> R2
        A3 --> R3
    end

    subgraph Workaround["Current Workaround"]
        W1["Load green ICO"]
        W2["Recolor pixels in memory"]
        W3["Pass to pystray"]
        WORKS["WORKS ✓"]

        W1 --> W2 --> W3 --> WORKS
    end

    style R1 fill:#ffcccc
    style R2 fill:#ffcccc
    style R3 fill:#ffcccc
    style WORKS fill:#ccffcc
```

## Key Insight

The issue is NOT with:
- The orange color values
- The ICO file structure
- The PIL processing pipeline

The issue IS with:
- Any orange ICO **file** loaded from disk → invisible
- But modifying pixels **in memory** after loading green ICO → works

This suggests something about how these specific orange ICO files were created/saved that Windows/pystray doesn't like, but we haven't identified the root cause.
