# System Tray Entry Point

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The system tray is the primary entry point for all user interactions. SyncoPaid runs in the background and uses the system tray icon to indicate status and provide quick access.

---

## System Tray Diagram

```
                              ┌──────────────┐
                              │  APP LAUNCH  │
                              │ (Background) │
                              └──────┬───────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SYSTEM TRAY                                      │
│                                                                             │
│    Status Icons:                                                            │
│    ● Green    = Tracking Active                                             │
│    ● Orange   = Paused                                                      │
│    ● Faded    = Idle (5+ min no activity)                                   │
│                                                                             │
│         ┌─────────┐                                                         │
│         │    ◉    │                                                         │
│         └────┬────┘                                                         │
│              │                                                              │
│      ┌───────┴───────┐                                                      │
│      │               │                                                      │
│      ▼               ▼                                                      │
│  LEFT-CLICK      RIGHT-CLICK                                                │
│      │               │                                                      │
│      │          ┌────┴────────────┐                                         │
│      │          │ ▶ Start/Pause   │ ◄── Toggle tracking (no window)         │
│      │          │ 📊 Open Window  │ ◄── Same as left-click                  │
│      │          │ ✕ Quit          │ ◄── Exit app completely                 │
│      │          └─────────────────┘                                         │
│      │                                                                      │
│      ▼                                                                      │
│  Opens Main Window                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interaction Summary

| Action | Result |
|--------|--------|
| Left-click tray icon | Opens Main Window (Timeline view) |
| Right-click → Start/Pause | Toggles tracking without opening window |
| Right-click → Open Window | Opens Main Window (same as left-click) |
| Right-click → Quit | Exits application completely |

---

## Status Icon States

| Icon | State | Description |
|------|-------|-------------|
| 🟢 Green | Active | Tracking is running, capturing window activity |
| 🟠 Orange | Paused | Tracking is paused by user |
| ⚪ Faded | Idle | No user activity detected for 5+ minutes |

---

## Related

- [Main Window](2025-12-25-Main-Window.md) - Opens on left-click
- [Menu Bar](2025-12-25-Menu-Bar.md) - Full menu access in main window
