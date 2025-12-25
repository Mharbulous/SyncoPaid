# SyncoPaid Navigation Documentation

> **Last Updated:** 2025-12-25
> **Status:** Proposed Design

---

## Overview

This folder contains the complete navigation documentation for SyncoPaid, a Windows 11 desktop application for automatic time tracking designed for legal professionals.

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [System Tray](2025-12-25-System-Tray.md) | System tray entry point and quick actions |
| [Menu Bar](2025-12-25-Menu-Bar.md) | Traditional menu bar (File, Edit, View, Tools, Help) |
| [Main Window](2025-12-25-Main-Window.md) | Main window structure and layout |
| [Timeline View](2025-12-25-Timeline-View.md) | Visual time-block view of activities |
| [Activities View](2025-12-25-Activities-View.md) | Table/list view of all activities |
| [Matters View](2025-12-25-Matters-View.md) | Manage legal matters and keywords |
| [Clients View](2025-12-25-Clients-View.md) | Manage clients and their matters |
| [Reports View](2025-12-25-Reports-View.md) | Time summaries and analytics |
| [Export View](2025-12-25-Export-View.md) | Export data for billing systems |
| [Settings Modal](2025-12-25-Settings-Modal.md) | Application settings and preferences |
| [Shared Components](2025-12-25-Shared-Components.md) | Reusable UI components |
| [User Journeys](2025-12-25-User-Journeys.md) | Common workflow patterns |

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Menu Bar First** | All features accessible via traditional File/Edit/View/Tools/Help menu |
| **Minimal friction** | System tray for quick actions; no main window needed for basic control |
| **Progressive disclosure** | Simple tray menu → detailed main window → specialized dialogs |
| **Context-aware** | Activities link directly to matter assignment; reports filter by selection |
| **Batch operations** | Bulk assign, bulk categorize, bulk export from any list view |
| **Background first** | App runs passively; user engages only when reviewing/exporting |

---

## Quick Reference

### Entry Points

| Entry | Action |
|-------|--------|
| Left-click tray | Opens Main Window (Timeline) |
| Right-click tray | Quick menu (Start/Pause, Open, Quit) |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Matter |
| Ctrl+Shift+N | New Client |
| Ctrl+I | Import CSV |
| Ctrl+E | Export Data |
| Ctrl+, | Settings |
| F1 | Help |
