# System Tray Entry Point

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The system tray is the primary entry point for all user interactions. SyncoPaid runs in the background and uses the system tray icon to indicate status and provide quick access.

**Key Design Principle:** Left-click is optimized for the most frequent action lawyers need—marking task transitions.

---

## Time Markers

Time markers are timestamps that indicate when the user switched tasks or was interrupted. They serve a critical workflow purpose:

**Why Time Markers Matter:**
- Lawyers are frequently interrupted and don't always have time to open an app and log what happened
- A single click on the tray icon instantly records the moment of transition
- AI can later use these markers to more precisely identify when work on one matter ended and another began
- Markers help distinguish billable work from interruptions (phone calls, colleague questions, etc.)

**How It Works:**
1. User is working on Task A
2. Phone rings—user clicks tray icon → time marker recorded
3. User handles phone call (Task B)
4. Call ends—user clicks tray icon → time marker recorded
5. User resumes Task A
6. Later, AI uses window activity + time markers to accurately categorize: "Task A (9:00-9:23), Phone call (9:23-9:31), Task A resumed (9:31-10:15)"

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
│      │          │ 📊 Open Window  │ ◄── Opens Main Window                   │
│      │          │ ✕ Quit          │ ◄── Exit app completely                 │
│      │          └─────────────────┘                                         │
│      │                                                                      │
│      ▼                                                                      │
│  Records Time Marker                                                        │
│  (Brief visual confirmation)                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interaction Summary

| Action | Result |
|--------|--------|
| Left-click tray icon | Records a time marker (task transition/interruption) |
| Right-click → Start/Pause | Toggles tracking without opening window |
| Right-click → Open Window | Opens Main Window (Timeline view) |
| Right-click → Quit | Exits application completely |

---

## Time Marker Visual Feedback

When a time marker is recorded, the user receives brief visual confirmation:

```
┌─────────────────────────────────────┐
│  After left-click:                  │
│                                     │
│  ┌─────────┐                        │
│  │    ◉    │  ← Icon briefly        │
│  └─────────┘    pulses/flashes      │
│       │                             │
│       ▼                             │
│  ┌─────────────────────┐            │
│  │ ✓ Marker recorded   │ ← Tooltip  │
│  │   9:23 AM           │   (fades)  │
│  └─────────────────────┘            │
│                                     │
└─────────────────────────────────────┘
```

The feedback is:
- **Non-intrusive:** No window opens, no dialog to dismiss
- **Quick:** Appears for ~1.5 seconds then fades
- **Informative:** Shows timestamp so user knows it worked

---

## Status Icon States

| Icon | State | Description |
|------|-------|-------------|
| 🟢 Green | Active | Tracking is running, capturing window activity |
| 🟠 Orange | Paused | Tracking is paused by user |
| ⚪ Faded | Idle | No user activity detected for 5+ minutes |

---

## Related

- [Main Window](2025-12-25-Main-Window.md) - Opens via right-click menu
- [Menu Bar](2025-12-25-Menu-Bar.md) - Full menu access in main window
