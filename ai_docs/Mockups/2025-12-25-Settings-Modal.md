# Settings Modal

> **Last Updated:** 2025-12-25
> **Parent:** [Navigation Index](2025-12-25-Navigation-Index.md)

---

## Overview

The Settings Modal provides access to all application configuration options, organized by category.

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
│  │  General        │  │  TRACKING                                     │     │
│  │  Tracking  ◄────┼──┤  ─────────────────────────────────────────    │     │
│  │  Screenshots    │  │                                               │     │
│  │  AI / LLM       │  │  Poll interval:     [1 second ▼]              │     │
│  │  Privacy        │  │  Idle threshold:    [3 minutes ▼]             │     │
│  │  Performance    │  │  Merge threshold:   [2 seconds ▼]             │     │
│  │                 │  │                                               │     │
│  │                 │  │  ☑ Start tracking on app launch               │     │
│  │                 │  │  ☑ Start app on Windows login                 │     │
│  │                 │  │  ☐ Show notification on pause                 │     │
│  │                 │  │                                               │     │
│  └─────────────────┘  └───────────────────────────────────────────────┘     │
│                                                                             │
│                                                     [Cancel]  [Save]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Settings Categories

### General

| Setting | Description | Default |
|---------|-------------|---------|
| Language | Application language | English |
| Theme | Light / Dark / System | System |
| Window behavior | Remember position, Start minimized | Remember |
| Date format | Date display format | System default |
| Time format | 12-hour / 24-hour | System default |

### Tracking

| Setting | Description | Default |
|---------|-------------|---------|
| Poll interval | How often to check active window | 1 second |
| Idle threshold | Time before marking as idle | 3 minutes |
| Merge threshold | Combine activities shorter than | 2 seconds |
| Start tracking on app launch | Auto-start tracking | ☑ |
| Start app on Windows login | Launch at startup | ☑ |
| Show notification on pause | System notification | ☐ |

### Screenshots

| Setting | Description | Default |
|---------|-------------|---------|
| Enable screenshots | Capture screenshots | ☑ |
| Capture interval | Time between captures | 10 seconds |
| Quality | JPEG quality (1-100) | 80 |
| Retention | Days to keep screenshots | 30 days |
| Skip duplicates | Use dHash deduplication | ☑ |
| Excluded apps | Apps to never screenshot | (list) |

### AI / LLM

| Setting | Description | Default |
|---------|-------------|---------|
| Enable AI categorization | Allow AI features | ☑ |
| API provider | OpenAI / Claude / Local | OpenAI |
| API key | API key for provider | (encrypted) |
| Auto-categorize threshold | Confidence level for auto-apply | 90% |
| Review low-confidence | Prompt review for uncertain | ☑ |

### Privacy

| Setting | Description | Default |
|---------|-------------|---------|
| Data retention | Days to keep activity data | 365 days |
| Excluded applications | Apps to never track | (list) |
| Excluded window titles | Title patterns to ignore | (list) |
| Clear all data | Delete all tracked data | (button) |
| Export all data | GDPR data export | (button) |

### Performance

| Setting | Description | Default |
|---------|-------------|---------|
| Max CPU usage | Throttle when above | 10% |
| Memory limit | Maximum RAM usage | 200 MB |
| Background priority | Process priority when hidden | Low |
| Database vacuum | Auto-optimize database | Weekly |

---

## Category Details

### General Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  GENERAL                                                                │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  Language:              [English ▼]                                     │
│                                                                         │
│  Theme:                 ● Light   ○ Dark   ○ System                     │
│                                                                         │
│  Window:                                                                │
│  ☑ Remember window position and size                                    │
│  ☐ Start minimized to tray                                              │
│                                                                         │
│  Date & Time:                                                           │
│  Date format:           [MM/DD/YYYY ▼]                                  │
│  Time format:           ● 12-hour (AM/PM)   ○ 24-hour                   │
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
│  Capture interval:      [10 seconds ▼]                                  │
│  Image quality:         [80 ▼] %                                        │
│                                                                         │
│  Storage:                                                               │
│  Retention period:      [30 days ▼]                                     │
│  Current usage:         1.2 GB (847 screenshots)                        │
│                         [Clean Up Now...]                               │
│                                                                         │
│  Optimization:                                                          │
│  ☑ Skip duplicate screenshots (dHash)                                   │
│  Similarity threshold:  [95 ▼] %                                        │
│                                                                         │
│  Excluded Applications:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ password manager, banking app, ...                          │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  [+ Add Application]                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Privacy Settings Page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PRIVACY                                                                │
│  ─────────────────────────────────────────────────────────────────      │
│                                                                         │
│  Data Retention:                                                        │
│  Keep activity data for:    [365 days ▼]                                │
│  Keep screenshots for:      [30 days ▼]                                 │
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

## Related

- [Menu Bar](2025-12-25-Menu-Bar.md) - Settings access via File menu
