# Main Window Structure

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The main window is the primary interface for SyncoPaid. It uses a traditional Windows desktop layout: menu bar for navigation and commands, a toolbar for quick controls, and a content area that changes based on the selected view.

---

## Window Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SyncoPaid - Time Tracking                                      [─] [□] [✕] │
├─────────────────────────────────────────────────────────────────────────────┤
│  File    Edit    View    Tools    Help                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  TOOLBAR                                                              │  │
│  │  ┌──────────────┐  ┌────────────────────────────┐                     │  │
│  │  │ ▶ Tracking   │  │ Today ▼ (date picker)      │                     │  │
│  │  │   [Pause]    │  │                            │                     │  │
│  │  └──────────────┘  └────────────────────────────┘                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                                                                             │
│                            CONTENT AREA                                     │
│                                                                             │
│                    (View switched via View menu)                            │
│                                                                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  STATUS BAR                                                                 │
│  Tracking: Active │ Uncategorized: 3 activities                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Window Components

### Title Bar

Standard Windows title bar with application name and window controls.

### Menu Bar

Traditional menu bar providing access to all features and view switching. See [Menu Bar](2025-12-25-Menu-Bar.md) for details.

| Menu | Purpose |
|------|---------|
| File | Import folders, export data, settings, exit |
| Edit | Undo/redo, selection, activity editing |
| View | Switch views (Timeline, Activities), toggle toolbar/status bar |
| Tools | Tracking control, AI categorization |
| Help | Documentation, shortcuts, about |

### Toolbar

Quick-access controls that persist across all views. Can be toggled via View → Toolbar.

| Component | Function |
|-----------|----------|
| Tracking Toggle | Start/Pause tracking with visual status indicator |
| Date Picker | Filter current view by date or date range |

### Content Area

Main workspace that displays the selected view. Switch views using the View menu:

| View | Purpose | Shortcut |
|------|---------|----------|
| Timeline | Visual time-block view of activities (default) | Ctrl+1 |
| Activities | Table/list view of all activities | Ctrl+2 |

### Status Bar

Information bar at bottom of window. Can be toggled via View → Status Bar.

| Element | Description |
|---------|-------------|
| Tracking Status | Shows Active/Paused/Idle |
| Uncategorized Count | Number of activities needing AI categorization |

---

## Window States

### Default State
- Opens to Timeline view
- Toolbar visible
- Status bar visible
- Date picker set to "Today"

### Minimized to Tray
- Window hidden
- Application continues running in system tray
- Tracking continues if active

### Restored from Tray
- Window returns to previous size and position
- View state preserved

---

## Related

- [Menu Bar](2025-12-25-Menu-Bar.md) - Menu structure and shortcuts
- [System Tray](2025-12-25-System-Tray.md) - Tray icon and quick actions
- [Timeline View](2025-12-25-Timeline-View.md) - Default view
