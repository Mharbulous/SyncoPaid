# SyncoPaid Story Tree Visualization

> Auto-generated visualization of story tree database

## Run Details

| Field | Value |
|-------|-------|
| Generated | 2025-12-19 13:18:07 UTC |
| Total Stories | 95 |

## Active Stories by Stage

| Stage | Count |
|-------|-------|
| concept | 13 |
| approved | 8 |
| active | 18 |
| implemented | 1 |
| ready | 30 |

## Held Stories

| Hold Reason | Count |
|-------------|-------|
| blocked | 6 |
| pending | 1 |
| polish | 1 |
| wishlist | 8 |

## Disposed Stories

| Disposition | Count |
|-------------|-------|
| duplicative | 1 |
| rejected | 8 |

## Tree Structure

```
SyncoPaid [14/10] ●
├── (1) Window Activity Tracking System [8/8] ●
│   ├── (1.1) Active Window Polling [3/3] ●
│   │   ├── (1.1.2) Process Command Line and Arguments Tracking [0/None] ●
│   │   ├── (1.1.3) Window Interaction Level Detection [0/None] ●
│   │   └── (1.1.4) Window Focus Duration Tracking [0/None] ❓
│   ├── (1.2) Idle Detection [3/3] ●
│   │   ├── (1.2.1) Idle Resumption Detection and Smart Prompt Trigger [0/None] ★
│   │   ├── (1.2.2) Lock Screen and Screensaver Detection [0/None] ⊗
│   │   └── (1.2.3) Configurable Idle Threshold [0/None] ·
│   ├── (1.3) Event Merging [0/2] ✔
│   ├── (1.4) Activity State Management [0/3] ✔
│   ├── (1.5) Start/End Time Recording [0/2] ✔
│   ├── (1.6) Enhanced Context Extraction from Window Titles [0/None] ●
│   ├── (1.7) Application-Specific Context Extraction for Legal Tools [0/None] ✓
│   └── (1.8) Multi-Monitor Window Position Tracking [0/None] ?
├── (10) Reporting & Analytics Dashboard [0/3] ✗
├── (11) Website & Marketing Platform [0/3] ·
├── (12) Practice Management Integration [0/3] ?
├── (13) Documentation & Help System [0/3] ·
├── (15) AI Screenshot Intelligence & Time Categorization [10/None] ✓
│   ├── (15.1) Automatic Screenshot Analysis [0/None] ·
│   ├── (15.10) Model Upgrade Transparency [0/None] ·
│   ├── (15.2) Night Processing Mode [0/None] ·
│   ├── (15.3) Client/Matter Recognition [0/None] ·
│   ├── (15.4) Intelligent Narrative Generation [0/None] ·
│   ├── (15.5) Review and Correction Interface [0/None] ·
│   ├── (15.6) Batch Processing On-Demand [0/None] ·
│   ├── (15.7) Privacy-Preserving Analysis [0/None] ·
│   ├── (15.8) Handling Analysis Failures [0/None] ·
│   └── (15.9) Performance Feedback [0/None] ✗
├── (2) Screenshot Capture & Deduplication [10/10] ●
│   ├── (2.1) Periodic Screenshot Capture [0/4] ✔
│   ├── (2.10) Screenshot-Assisted Time Categorization UI [0/None] ●
│   ├── (2.2) Perceptual Hash Deduplication [0/3] ✔
│   ├── (2.3) Action-Triggered Screenshots [0/3] ✔
│   ├── (2.4) Multi-Monitor Support [0/3] ✔
│   ├── (2.5) Context-Aware Thresholds [0/2] ✔
│   ├── (2.6) Screenshot Retention & Cleanup Policy [0/3] ●
│   ├── (2.7) Screenshot Gallery & Viewer [0/3] ✗
│   ├── (2.8) Screenshot Quality Optimization [0/3] ✗
│   └── (2.9) Monthly Screenshot Archiving [0/None] ?
├── (3) Data Management & Export [7/7] ●
│   ├── (3.1) SQLite Event Storage [0/3] ✔
│   ├── (3.2) Event Deletion [0/3] ✔
│   ├── (3.3) JSON Export for LLM Processing [0/4] ✔
│   ├── (3.4) Database Statistics [0/2] ✔
│   ├── (3.6) AI Learning Database for Categorization Patterns [0/None] ✓
│   ├── (3.7) Database Integrity Validation and Repair [0/None] ?
│   └── (3.8) Database Backup and Recovery [0/None] ?
├── (4) User Interface & Controls [9/9] ●
│   ├── (4.1) System Tray Integration [0/4] ✔
│   ├── (4.10) Batch Operations Toolbar [0/None] ?
│   ├── (4.2) View Time Window [0/4] ✔
│   ├── (4.3) Command Text Field [0/3] ✔
│   ├── (4.4) About Dialog [0/2] ✔
│   ├── (4.5) Start/Pause Tracking Controls [0/3] ✔
│   ├── (4.6) Activity Timeline View [0/3] ✓
│   ├── (4.7) Quick Actions Popup [0/3] ✗
│   └── (4.9) Matter Selection and Assignment UI [0/None] ✗
├── (5) Configuration & Settings Management [6/6] ●
│   ├── (5.1) JSON Config File [0/2] ✔
│   ├── (5.2) Polling & Threshold Settings [0/3] ✔
│   ├── (5.3) Screenshot Configuration [0/4] ✔
│   ├── (5.4) Startup Behavior Settings [0/3] ✔
│   ├── (5.5) User-Configurable Privacy and Application Blocking [0/None] ◇
│   └── (5.6) Configuration Validation & Error Handling [0/None] ?
├── (6) Build, Packaging & Distribution [5/5] ●
│   ├── (6.1) Automatic Version Generation [0/3] ✔
│   ├── (6.2) PyInstaller Executable [0/4] ✔
│   ├── (6.3) Build Script Automation [0/3] ✔
│   ├── (6.4) Windows Code Signing Integration [0/None] ✓
│   └── (6.5) Automated Update Check and Notification [0/None] ?
├── (7) Privacy & Data Security [6/6] ●
│   ├── (7.1) Local-Only Data Storage [0/2] ✔
│   ├── (7.2) Single Instance Enforcement [0/2] ✔
│   ├── (7.3) Sensitive Content Blocking [0/3] ✔
│   ├── (7.4) Local Database Encryption at Rest [0/None] ✗
│   ├── (7.5) Audit Logging for Data Access and Compliance [0/None] ✗
│   └── (7.6) Secure Data Deletion [0/None] ·
├── (8) LLM & AI Integration [5/8] ⊗
│   ├── (8.1) Matter/Client Database [1/3] ⊗
│   │   └── (8.1.1) Matter Keywords/Tags for AI Matching [0/3] ✓
│   ├── (8.2) Browser URL Extraction [0/3] ●
│   ├── (8.3) UI Automation Integration [0/3] ⊗
│   ├── (8.4) AI Disambiguation with Screenshot Context [2/3] ⊗
│   │   ├── (8.4.1) Activity-to-Matter Matching [0/3] ⊗
│   │   └── (8.4.2) Transition Detection & Smart Prompts [0/3] ●
│   └── (8.5) LLM API Integration & Batch Categorization [0/None] ✓
└── (9) Performance & Reliability [5/5] ●
    ├── (9.1) Background Thread Architecture [0/3] ✔
    ├── (9.2) Graceful Shutdown [0/3] ✔
    ├── (9.3) Error Recovery [0/3] ✔
    ├── (9.4) Application Health Monitoring and Auto-Recovery [0/None] ?
    └── (9.5) Resource Usage Optimization and Adaptive Throttling [0/None] ✓
```

---
*Generated by daily visualization workflow*
