# SyncoPaid Story Tree Visualization

> Auto-generated visualization of story tree database

## Run Details

| Field | Value |
|-------|-------|
| Generated | 2025-12-18 13:20:59 UTC |
| Total Stories | 81 |

## Active Stories by Stage

| Stage | Count |
|-------|-------|
| approved | 18 |
| active | 16 |
| verifying | 1 |
| implemented | 30 |

## Held Stories

| Hold Reason | Count |
|-------------|-------|
| blocked | 6 |
| pending | 5 |

## Disposed Stories

| Disposition | Count |
|-------------|-------|
| rejected | 4 |
| wishlist | 1 |

## Tree Structure

```
SyncoPaid [13/10] ●
├── (1.1) Window Activity Tracking System [8/8] ●
│   ├── (1.1.1) Active Window Polling [2/3] ●
│   │   ├── (1.1.1.2) Process Command Line and Arguments Tracking [0/None] ✓
│   │   └── (1.1.1.3) Window Interaction Level Detection [0/None] ❓
│   ├── (1.1.2) Idle Detection [2/3] ●
│   │   ├── (1.1.2.1) Idle Resumption Detection and Smart Prompt Trigger [0/None] ?
│   │   └── (1.1.2.2) Lock Screen and Screensaver Detection [0/None] ⊗
│   ├── (1.1.3) Event Merging [0/2] ★
│   ├── (1.1.4) Activity State Management [0/3] ★
│   ├── (1.1.5) Start/End Time Recording [0/2] ★
│   ├── (1.1.6) Enhanced Context Extraction from Window Titles [0/None] ●
│   ├── (1.1.7) Application-Specific Context Extraction for Legal Tools [0/None] ❓
│   └── (1.1.8) Multi-Monitor Window Position Tracking [0/None] ✓
├── (1.10) Reporting & Analytics Dashboard [0/3] ✗
├── (1.11) Website & Marketing Platform [0/3] ✓
├── (1.12) Practice Management Integration [0/3] ?
├── (1.13) Documentation & Help System [0/3] ✓
├── (1.2) Screenshot Capture & Deduplication [10/10] ●
│   ├── (1.2.1) Periodic Screenshot Capture [0/4] ★
│   ├── (1.2.10) Screenshot-Assisted Time Categorization UI [0/None] ●
│   ├── (1.2.2) Perceptual Hash Deduplication [0/3] ★
│   ├── (1.2.3) Action-Triggered Screenshots [0/3] ★
│   ├── (1.2.4) Multi-Monitor Support [0/3] ★
│   ├── (1.2.5) Context-Aware Thresholds [0/2] ★
│   ├── (1.2.6) Screenshot Retention & Cleanup Policy [0/3] ●
│   ├── (1.2.7) Screenshot Gallery & Viewer [0/3] ✗
│   ├── (1.2.8) Screenshot Quality Optimization [0/3] ✗
│   └── (1.2.9) Monthly Screenshot Archiving [0/None] ⊗
├── (1.3) Data Management & Export [7/7] ●
│   ├── (1.3.1) SQLite Event Storage [0/3] ★
│   ├── (1.3.2) Event Deletion [0/3] ★
│   ├── (1.3.3) JSON Export for LLM Processing [0/4] ★
│   ├── (1.3.4) Database Statistics [0/2] ★
│   ├── (1.3.6) AI Learning Database for Categorization Patterns [0/None] ❓
│   ├── (1.3.7) Database Integrity Validation and Repair [0/None] ✓
│   └── (1.3.8) Database Backup and Recovery [0/None] ✓
├── (1.4) User Interface & Controls [9/9] ●
│   ├── (1.4.1) System Tray Integration [0/4] ★
│   ├── (1.4.10) Batch Operations Toolbar [0/None] ✓
│   ├── (1.4.2) View Time Window [0/4] ★
│   ├── (1.4.3) Command Text Field [0/3] ★
│   ├── (1.4.4) About Dialog [0/2] ★
│   ├── (1.4.5) Start/Pause Tracking Controls [0/3] ★
│   ├── (1.4.6) Activity Timeline View [0/3] ❓
│   ├── (1.4.7) Quick Actions Popup [0/3] ✗
│   └── (1.4.9) Matter Selection and Assignment UI [0/None] ✓
├── (1.5) Configuration & Settings Management [6/6] ●
│   ├── (1.5.1) JSON Config File [0/2] ★
│   ├── (1.5.2) Polling & Threshold Settings [0/3] ★
│   ├── (1.5.3) Screenshot Configuration [0/4] ★
│   ├── (1.5.4) Startup Behavior Settings [0/3] ★
│   ├── (1.5.5) User-Configurable Privacy and Application Blocking [0/None] ✓
│   └── (1.5.6) Configuration Validation & Error Handling [0/None] ❓
├── (1.6) Build, Packaging & Distribution [5/5] ●
│   ├── (1.6.1) Automatic Version Generation [0/3] ★
│   ├── (1.6.2) PyInstaller Executable [0/4] ★
│   ├── (1.6.3) Build Script Automation [0/3] ★
│   ├── (1.6.4) Windows Code Signing Integration [0/None] ✓
│   └── (1.6.5) Automated Update Check and Notification [0/None] ✓
├── (1.7) Privacy & Data Security [5/6] ●
│   ├── (1.7.1) Local-Only Data Storage [0/2] ★
│   ├── (1.7.2) Single Instance Enforcement [0/2] ★
│   ├── (1.7.3) Sensitive Content Blocking [0/3] ★
│   ├── (1.7.4) Local Database Encryption at Rest [0/None] ✓
│   └── (1.7.5) Audit Logging for Data Access and Compliance [0/None] ✓
├── (1.8) LLM & AI Integration [5/8] ⊗
│   ├── (1.8.1) Matter/Client Database [1/3] ⊗
│   │   └── (1.8.1.1) Matter Keywords/Tags for AI Matching [0/3] ✓
│   ├── (1.8.2) Browser URL Extraction [0/3] ●
│   ├── (1.8.3) UI Automation Integration [0/3] ⊗
│   ├── (1.8.4) AI Disambiguation with Screenshot Context [2/3] ⊗
│   │   ├── (1.8.4.1) Activity-to-Matter Matching [0/3] ✓
│   │   └── (1.8.4.2) Transition Detection & Smart Prompts [0/3] ●
│   └── (1.8.5) LLM API Integration & Batch Categorization [0/None] ✓
└── (1.9) Performance & Reliability [5/5] ●
    ├── (1.9.1) Background Thread Architecture [0/3] ★
    ├── (1.9.2) Graceful Shutdown [0/3] ★
    ├── (1.9.3) Error Recovery [0/3] ★
    ├── (1.9.4) Application Health Monitoring and Auto-Recovery [0/None] ✓
    └── (1.9.5) Resource Usage Optimization and Adaptive Throttling [0/None] ✓
```

---
*Generated by daily visualization workflow*
