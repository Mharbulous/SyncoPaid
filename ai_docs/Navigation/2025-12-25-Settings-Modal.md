# Settings Modal

> **Last Updated:** 2025-12-26
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Settings Modal provides access to essential application configuration. Settings are minimal — if a sensible default exists, we use it instead of adding a setting.

---

## Menu Access

- **File → Settings** (Ctrl+,)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SETTINGS                                                          [✕]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ SIDEBAR ───────┐  ┌─ CONTENT ─────────────────────────────────────┐     │
│  │                 │  │                                               │     │
│  │  Startup   ◄────┼──┤  STARTUP                                      │     │
│  │  Screenshots    │  │  ─────────────────────────────────────────    │     │
│  │  AI             │  │                                               │     │
│  │  Privacy        │  │  ☑ Start tracking on app launch               │     │
│  │                 │  │  ☑ Start app on Windows login                 │     │
│  │                 │  │  ☐ Start minimized to tray                    │     │
│  │                 │  │                                               │     │
│  │                 │  │                                               │     │
│  │                 │  │                                               │     │
│  └─────────────────┘  └───────────────────────────────────────────────┘     │
│                                                                             │
│                                                     [Cancel]  [Save]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Settings Categories

### Startup

| Setting | Description | Default |
|---------|-------------|---------|
| Start tracking on app launch | Begin tracking automatically | ☑ |
| Start app on Windows login | Launch at system startup | ☑ |
| Start minimized to tray | Hide window on launch | ☐ |

### Screenshots

| Setting | Description | Default |
|---------|-------------|---------|
| Enable screenshots | Capture screenshots for AI context | ☑ |
| Retention | Days to keep screenshots | 30 days |
| Quality | JPEG compression quality | 80% |
| Similarity threshold | dHash threshold for deduplication | 95% |

### AI

| Setting | Description | Default |
|---------|-------------|---------|
| Enable AI categorization | Allow AI to categorize activities | ☑ |
| AI Model | Local or cloud-based AI model | Moondream 2 |
| Confidence threshold | Minimum confidence for auto-accept | 90% |

**AI Model options:**
- **Moondream 2** — Local processing
- **Moondream 3** — Local processing
- **Gemini 2.0 Flash** — Cloud (OAuth) ⚠️

### Privacy

| Setting | Description | Default |
|---------|-------------|---------|
| Data retention | Days to keep activity data | 365 days |
| Excluded applications | Apps to never track | (list) |
| Excluded window titles | Title patterns to ignore | (list) |
| Clear all data | Delete all tracked data | (button) |
| Export all data | GDPR data export | (button) |

---

## Category Details

### Startup Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STARTUP                                                                │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  ☑ Start tracking on app launch                                         │
│  ☑ Start app on Windows login                                           │
│  ☐ Start minimized to tray                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Screenshots Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SCREENSHOTS                                                            │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  ☑ Enable screenshot capture                                            │
│                                                                         │
│  Retention period:      [30 days ▼]                                     │
│  Quality:               [80% ▼]                                         │
│  Similarity threshold:  [95% ▼]                                         │
│                                                                         │
│  Current usage:         1.2 GB (847 screenshots)                        │
│                         [Clean Up Now...]                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

*Quality and similarity threshold enable data gathering for future optimization decisions.*

### AI Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AI                                                                     │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  ☑ Enable AI categorization                                             │
│                                                                         │
│  AI Model:              [Moondream 2 ▼]                                  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐      │
│  │  ○ Moondream 2      Local processing                          │      │
│  │  ○ Moondream 3      Local processing                          │      │
│  │  ○ Gemini 2.0 Flash Cloud (OAuth)                             │      │
│  └───────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  Confidence threshold:  [90% ▼]                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

*When Gemini 2.0 Flash is selected, a warning appears:*

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ┌─ ⚠ Warning ───────────────────────────────────────────────────┐      │
│  │  Gemini 2.0 Flash is not a local LLM. Only select this        │      │
│  │  option if you intend to transmit your data to be processed   │      │
│  │  online by the Gemini LLM.                                    │      │
│  └───────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

*Confidence threshold enables data gathering for future optimization decisions.*

### Privacy Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PRIVACY                                                                │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  Data Retention:                                                        │
│  Keep activity data for:    [365 days ▼]                                │
│                                                                         │
│  Excluded Applications (never track):                                   │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • KeePass                                              [✕]  │        │
│  │ • 1Password                                            [✕]  │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  [+ Add Application]                                                    │
│                                                                         │
│  Excluded Window Titles (pattern matching):                             │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ • *password*                                           [✕]  │        │
│  │ • *private*                                            [✕]  │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  [+ Add Pattern]                                                        │
│                                                                         │
│  ⚠ Danger Zone                                                          │
│  ───────────────────────────────────────────────────────────────        │
│  [Clear All Data]     [Export All Data]                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Actions

| Button | Action |
|--------|--------|
| [✕] | Close without saving (prompts if changes) |
| Cancel | Discard changes and close |
| Save | Apply changes and close |

---

## What Was Removed

The following settings were intentionally excluded — sensible defaults are used instead:

| Removed | Rationale |
|---------|-----------|
| Language, Date/Time format | Use system settings |
| Theme (Light/Dark) | Use system theme |
| Poll interval, Idle threshold, Merge threshold | Technical internals; use good defaults |
| Screenshot capture interval | Use good default (10s) |
| Screenshot excluded apps | Consolidated into Privacy exclusions |
| Performance settings (CPU, Memory, etc.) | Premature optimization; app should just work |
| API keys | Local models don't need keys; Gemini uses OAuth |

## What Was Kept (Data Gathering Hooks)

These settings enable future optimization decisions based on real usage data:

| Setting | Purpose |
|---------|---------|
| Screenshot quality (80%) | Gather data on storage vs quality trade-offs |
| Similarity threshold (95%) | Gather data on deduplication effectiveness |
| AI confidence threshold (90%) | Gather data on auto-accept accuracy |

*Rationale: Simple settings for data collection are OK; complex optimization features are not. These settings let users adjust values while we gather information about what works best.*

---

## Related

- [Menu Bar](2025-12-25-Menu-Bar.md) - Settings access via File menu
