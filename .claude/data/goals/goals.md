# Product Vision

## What We're Building
SyncoPaid is a time-tracking application for lawyers that automatically captures work activities and uses AI to categorize time into billing categories with minimal manual effort.

## What This App Is
- A **time tracking app** — not practice management software
- A tool that **fits into the user's existing workflow** — not one that replaces it
- An app that uses the **user's own folder structure** as client/matter categories

## Target User
Lawyers who need to track billable hours across multiple matters and clients, particularly those frustrated with manual time entry and seeking to reduce administrative overhead while maintaining accurate billing records.

## Core Capabilities
- **Automatic Activity Capture**: Continuous tracking of window activities, browser URLs, email subjects, and folder paths to build a complete picture of work performed
- **Screenshot-Based History**: Automatic screenshot capture with intelligent deduplication and monthly archiving to preserve context while managing disk space
- **Import Client/Matter Folders**: Import the user's existing folder structure from their file system. Folder names are used exactly as-is — no parsing or interpretation of naming conventions
- **AI-Powered Categorization**: Intelligent activity classification that matches activities to the user's imported client/matter folders
- **Billing Status Tracking**: Time is categorized by billing status (WIP, Billed, Non-Billable) rather than temporal periods
- **Smart Prompting**: Non-intrusive AI that detects natural work transitions (inbox browsing, idle periods, context switches) and prompts "Is now a good time to categorize your time?" at appropriate moments
- **Screenshot-Assisted Review**: Interactive review UI that shows relevant screenshots when clarification is needed for ambiguous activities
- **Continuous Learning**: AI that improves categorization accuracy by learning from user corrections and building matter-specific patterns

## Guiding Principles
- **Minimize Manual Effort**: Automate everything possible so lawyers can focus on legal work, not administrative tasks
- **Non-Intrusive Intelligence**: Prompt at natural breaks, never interrupt focused work
- **Use What Already Exists**: Import the user's existing folder structure rather than making them recreate it. Use their naming conventions as-is
- **Context-Aware Categorization**: Capture rich contextual data (URLs, email subjects, folder paths) to enable accurate AI matching
- **Preserve All History**: Archive rather than delete—screenshots and activity data are valuable evidence, never throw them away
- **Learn and Improve**: Get smarter over time by learning from corrections and building matter-specific recognition patterns
- **Lawyer-Specific Workflows**: Built for legal billing conventions (6-minute increments, matter/client structures, legal research sources like Westlaw/CanLII)

---
*Auto-generated from approved story nodes. Last updated: 2025-12-16*
