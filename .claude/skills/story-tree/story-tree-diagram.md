# TimeLawg Story Tree Diagram

**Last Updated:** 2025-12-11T22:45:00Z
**Version:** 1.0.0

---

## Legend

- ✅ **implemented** - Feature complete and working
- 🚧 **in-progress** - Currently being developed
- 📋 **planned** - Approved for development
- 💡 **concept** - Idea stage
- ⭐ **active** - Product vision (root only)
- ❌ **deprecated** - No longer relevant

**Capacity notation:** `[current/target]` - number of child stories vs. target capacity

---

## Story Tree

```
⭐ root [6/10] - TimeLawg - Automated time tracking for lawyers
│   Windows desktop application that automatically captures window activity, screenshots,
│   and idle time for accurate billable time tracking while preserving attorney-client
│   privilege through local-only data storage
│
├─✅ 1.1 [4/4] - Window activity tracking
│  │   As a lawyer, I want automatic tracking of which applications and windows I'm using
│  │   so that my billable time is captured without manual effort
│  │   📝 Commits: 6efd5cb, 9d1dac5
│  │
│  ├─✅ 1.1.1 [0/2] - Active window detection
│  │     As a lawyer, I want the app to detect which window I'm actively using so that
│  │     my work context is captured
│  │
│  ├─✅ 1.1.2 [0/2] - Idle time detection
│  │     As a lawyer, I want idle time to be detected and marked so that non-billable
│  │     time isn't included in my reports
│  │
│  ├─✅ 1.1.3 [0/2] - Activity event merging
│  │     As a lawyer, I want brief window switches to be merged into continuous sessions
│  │     so that my time logs are clean and accurate
│  │
│  └─✅ 1.1.4 [0/2] - End time tracking
│        As a lawyer, I want both start time and end time recorded for each activity so
│        that I have complete temporal data for billing
│        📝 Commits: 531a5b9
│
├─✅ 1.2 [5/5] - Periodic screenshot capture
│  │   As a lawyer, I want periodic screenshots of my work so that I have visual proof
│  │   of my activities for billing disputes
│  │   📝 Commits: 55d264c, e98fd8e, df69b65, 46e50d3
│  │
│  ├─✅ 1.2.1 [0/3] - Perceptual hash deduplication
│  │     As a lawyer, I want duplicate screenshots to be automatically merged so that
│  │     storage is used efficiently
│  │     📝 Commits: 55d264c
│  │
│  ├─✅ 1.2.2 [0/3] - Multi-monitor support
│  │     As a lawyer, I want screenshots to work correctly across multiple monitors so
│  │     that my secondary display activities are captured
│  │     📝 Commits: e98fd8e, bc46d54
│  │
│  ├─✅ 1.2.3 [0/2] - Context-aware similarity thresholds
│  │     As a lawyer, I want different similarity thresholds when windows change so that
│  │     important screenshots aren't overwritten
│  │     📝 Commits: df69b65
│  │
│  ├─✅ 1.2.4 [0/2] - Window title change detection
│  │     As a lawyer, I want new screenshots when window titles change so that browser
│  │     tab switches and email changes are captured
│  │     📝 Commits: 46e50d3
│  │
│  └─✅ 1.2.5 [0/2] - Timezone-aware filename format
│        As a lawyer, I want screenshot filenames to include local timezone so that I
│        can easily locate files by when I worked on them
│        📝 Commits: cd78bf5, b082e8b
│
├─✅ 1.3 [4/4] - Action-based screenshot capture
│  │   As a lawyer, I want screenshots triggered by my actions (clicks, drags, focus
│  │   changes) so that I have visual evidence of key work moments
│  │   📝 Commits: 9e7864d, db8305c, 36bb125
│  │
│  ├─✅ 1.3.1 [0/2] - Mouse click capture
│  │     As a lawyer, I want screenshots when I click so that important UI interactions
│  │     are documented
│  │     📝 Commits: 9e7864d
│  │
│  ├─✅ 1.3.2 [0/2] - Drag-and-drop capture
│  │     As a lawyer, I want screenshots when I drag files or content so that evidence
│  │     handling is documented
│  │     📝 Commits: 36bb125
│  │
│  ├─✅ 1.3.3 [0/2] - Window focus change capture
│  │     As a lawyer, I want screenshots when I switch windows so that context switches
│  │     are visible in my timeline
│  │     📝 Commits: db8305c
│  │
│  └─✅ 1.3.4 [0/2] - Action throttling
│        As a lawyer, I want action screenshots throttled to prevent excessive captures
│        so that storage isn't wasted
│        📝 Commits: 9e7864d
│
├─✅ 1.4 [5/5] - System tray interface
│  │   As a lawyer, I want a system tray icon with controls so that I can manage time
│  │   tracking without opening a full application window
│  │   📝 Commits: 9cd4fd1, 3f72402, 5873af4
│  │
│  ├─✅ 1.4.1 [0/2] - Start/Pause tracking toggle
│  │     As a lawyer, I want to start and pause tracking from the system tray so that
│  │     I can control when time is recorded
│  │
│  ├─✅ 1.4.2 [0/3] - View Time window
│  │     As a lawyer, I want to view my recent activity in a window so that I can
│  │     review what was tracked
│  │     📝 Commits: 9cd4fd1
│  │
│  ├─✅ 1.4.3 [0/2] - Start with Windows toggle
│  │     As a lawyer, I want to enable/disable auto-start so that I can control whether
│  │     tracking starts automatically
│  │     📝 Commits: 1409acc
│  │
│  ├─✅ 1.4.4 [0/2] - Screenshot folder access commands
│  │     As a lawyer, I want command shortcuts to open screenshot folders so that I can
│  │     quickly access captured images
│  │     📝 Commits: b960361
│  │
│  └─✅ 1.4.5 [0/1] - About dialog with version info
│        As a lawyer, I want to see version information so that I can verify which
│        version I'm running
│        📝 Commits: 36bb125
│
├─✅ 1.5 [3/4] - Data storage and export
│  │   As a lawyer, I want my time data stored locally and exportable so that I maintain
│  │   client privilege and can process data with external tools
│  │
│  ├─✅ 1.5.1 [0/2] - SQLite activity event storage
│  │     As a lawyer, I want activity events stored in SQLite so that my time data
│  │     persists across sessions
│  │
│  ├─✅ 1.5.2 [0/2] - Screenshot metadata database
│  │     As a lawyer, I want screenshot metadata stored in database so that I can query
│  │     and relate screenshots to activities
│  │
│  └─✅ 1.5.3 [0/3] - JSON export for LLM processing
│        As a lawyer, I want to export time data as JSON so that I can use AI tools to
│        categorize and bill my time
│
└─✅ 1.6 [3/4] - Build and packaging automation
   │   As a developer, I want automated build and versioning so that I can create
   │   distributable executables efficiently
   │   📝 Commits: ab5856b, cc75360, 5e39595
   │
   ├─✅ 1.6.1 [0/2] - PyInstaller executable creation
   │     As a developer, I want automated PyInstaller builds so that I can create
   │     single-file Windows executables
   │
   ├─✅ 1.6.2 [0/3] - Automatic version generation with git
   │     As a developer, I want version numbers auto-generated from git commits so that
   │     each build is uniquely identifiable
   │     📝 Commits: ab5856b, cc75360, 5e39595
   │
   └─✅ 1.6.3 [0/2] - Windows version metadata
         As a developer, I want Windows file properties to show version info so that
         users can verify executable versions
```

---

## Summary Statistics

### Overall Progress
- **Total Stories:** 33
- **Implemented:** 32 ✅
- **In Progress:** 0 🚧
- **Planned:** 0 📋
- **Concept:** 0 💡
- **Root:** 1 ⭐

### Capacity Analysis
- **Root Capacity:** 6/10 (60% filled - room for 4 more major features)
- **Fully Implemented Major Features:** 6/6 (100%)
  - Window activity tracking ✅
  - Periodic screenshot capture ✅
  - Action-based screenshot capture ✅
  - System tray interface ✅
  - Data storage and export ✅
  - Build and packaging automation ✅

### Under-Capacity Nodes (Opportunities for Growth)
- **1.5 [3/4]** - Data storage and export (1 story slot available)
- **1.6 [3/4]** - Build and packaging automation (1 story slot available)
- **Root [6/10]** - Main product (4 story slots available for new major features)

### Recent Implementation Activity
Recent commits show active development in:
- End time tracking (531a5b9)
- Screenshot features (multiple commits)
- Build automation (ab5856b, cc75360, 5e39595)
- System tray enhancements (multiple commits)

---

## Next Steps & Opportunities

Based on the story tree analysis:

1. **Root level has capacity for 4 more major features** - Consider adding:
   - LLM-based time categorization/billing assistant
   - Client/matter management
   - Reporting and analytics
   - Integration with billing systems

2. **Two features are slightly under capacity:**
   - Data storage (1.5) could add backup/sync capabilities
   - Build automation (1.6) could add auto-update functionality

3. **All current features are fully implemented** - Excellent foundation for next phase

---

*This diagram is auto-generated from `.claude/data/story-tree.db`*
