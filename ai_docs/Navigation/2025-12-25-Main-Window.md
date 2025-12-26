# Main Window Structure

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The main window is the primary interface for SyncoPaid. It features a traditional menu bar, a header bar with quick controls, a sidebar for navigation, and a content area that changes based on the selected view.

---

## Window Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SyncoPaid - Time Tracking                                      [─] [□] [✕] │
├─────────────────────────────────────────────────────────────────────────────┤
│  File    Edit    View    Tools    Help                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  HEADER BAR                                                         │    │
│  │  ┌──────────────┐  ┌────────────────────────────┐                   │    │
│  │  │ ▶ Tracking   │  │ Today ▼ (date picker)      │                   │    │
│  │  │   [Pause]    │  │                            │                   │    │
│  │  └──────────────┘  └────────────────────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  SIDEBAR                          MAIN CONTENT AREA                 │    │
│  │  ┌───────────────┐   ┌─────────────────────────────────────────┐    │    │
│  │  │               │   │                                         │    │    │
│  │  │ 📅 Timeline   │◄──┼── DEFAULT VIEW                          │    │    │
│  │  │               │   │                                         │    │    │
│  │  │ 📋 Activities │   │  (Content changes based on              │    │    │
│  │  │               │   │   sidebar selection)                    │    │    │
│  │  │ 📁 Matters    │   │                                         │    │    │
│  │  │               │   │                                         │    │    │
│  │  │ 👥 Clients    │   │                                         │    │    │
│  │  │               │   │                                         │    │    │
│  │  │ ───────────── │   │                                         │    │    │
│  │  │               │   │                                         │    │    │
│  │  │ 📊 Reports    │   │                                         │    │    │
│  │  │               │   │                                         │    │    │
│  │  │ 📤 Export     │   │                                         │    │    │
│  │  │               │   │                                         │    │    │
│  │  └───────────────┘   └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STATUS BAR                                                         │    │
│  │  Tracking: Active │ Today: 4.2 hrs │ Uncategorized: 3 activities    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Window Components

### Title Bar

Standard Windows title bar with application name and window controls.

### Menu Bar

Traditional menu bar providing access to all features. See [Menu Bar](2025-12-25-Menu-Bar.md) for details.

| Menu | Purpose |
|------|---------|
| File | New items, import/export, settings, exit |
| Edit | Undo/redo, selection, activity editing |
| View | Switch views, toggle UI elements, zoom, filters |
| Tools | Tracking control, AI features, database tools |
| Help | Documentation, shortcuts, about |

### Header Bar

Quick-access controls that persist across all views.

| Component | Function |
|-----------|----------|
| Tracking Toggle | Start/Pause tracking with visual status indicator |
| Date Picker | Filter all views by date or date range |

### Sidebar

Navigation panel for switching between views. Can be toggled with View → Sidebar (Ctrl+B).

| Section | Purpose | Shortcut |
|---------|---------|----------|
| Timeline | Visual time-block view of activities (default) | F2 |
| Activities | Table/list view of all activities | F3 |
| Matters | Manage legal matters and keywords | F4 |
| Clients | Manage clients and their matters | F5 |
| Reports | Time summaries and analytics | F6 |
| Export | Export data for billing systems | F7 |

### Content Area

Main workspace that displays the selected view. Changes based on sidebar selection.

### Status Bar

Information bar at bottom of window. Can be toggled via View → Status Bar.

| Element | Description |
|---------|-------------|
| Tracking Status | Shows Active/Paused/Idle |
| Today's Hours | Total tracked time for today |
| Uncategorized Count | Number of activities needing attention |

---

## Window States

### Default State
- Opens to Timeline view
- Sidebar visible
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
