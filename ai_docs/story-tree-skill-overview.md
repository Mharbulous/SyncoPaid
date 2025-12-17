# Story Tree Skill Overview

This document provides an independent explanation of the story-tree custom skill based solely on its internal documentation.

## What is the Story Tree Skill?

The story-tree skill is an autonomous backlog management system that organizes software development ideas into a hierarchical tree structure. Each node in the tree represents a user story at a particular level of detail, from high-level product vision down to specific implementation tasks.

The skill operates with minimal human intervention. When invoked, it examines the current state of the tree, identifies where new ideas are needed based on capacity rules, and generates contextually appropriate user stories to fill those gaps.

## Core Concepts

### Hierarchical Organization

Stories are arranged in a parent-child tree structure:
- The root node represents the overall project or application
- First-level children represent major feature areas
- Second-level nodes describe specific capabilities within those features
- Deeper levels capture implementation details as granular as needed

### Capacity-Based Growth

Each node has a target capacity defining how many children it should have. The skill calculates effective capacity dynamically:
- New nodes start with a base capacity of three
- Capacity increases as children are completed (specifically, capacity equals three plus the count of implemented children)
- This mechanism encourages finishing existing work before expanding the tree further

### Priority Through Depth

When deciding where to add new stories, the skill always prioritizes shallower nodes over deeper ones. A half-empty root node takes precedence over a completely empty node buried four levels deep. This breadth-first approach ensures strategic balance across the product portfolio before diving deep into any single area.

### Git-Driven Implementation Tracking

The skill connects to the repository's git history to detect when stories have been implemented. It extracts keywords from commit messages and matches them against story descriptions using similarity scoring. Strong matches automatically update story status from planned or in-progress to implemented.

## Data Storage Architecture

All data resides in a SQLite database using a closure table pattern. This design choice enables efficient queries across the tree hierarchy without recursive traversal. The database contains:

- A nodes table storing story details, capacity, and status
- A paths table recording all ancestor-descendant relationships with their depth
- A commits table linking git commits to the stories they implement
- A metadata table tracking housekeeping information like last update timestamps

The database file lives separately from the skill definition files, allowing the skill itself to be copied between projects while keeping project-specific data isolated.

## Three-Field Workflow System

Stories are tracked using three orthogonal fields rather than a single status:

### Stage (Progress through workflow)

| Stage | Meaning |
|-------|---------|
| concept | Initial idea awaiting human review |
| approved | Human has validated the idea |
| planned | Implementation plan exists |
| queued | Ready to work on, dependencies satisfied |
| active | Currently being developed |
| reviewing | Code complete, awaiting review |
| verifying | Under verification testing |
| implemented | Development complete |
| ready | Fully tested and production-ready |
| polish | Minor refinements needed |
| released | Shipped to production |

### Hold Reason (Temporary blocks)

| Hold | Meaning |
|------|---------|
| pending | Awaiting human decision |
| paused | Work intentionally paused |
| blocked | Waiting on external dependency |
| broken | Encountering issues requiring fixes |
| refine | Needs rework based on feedback |

When a hold is set, the stage is preserved. Clearing the hold resumes work at the same stage.

### Disposition (Terminal states)

| Disposition | Meaning |
|-------------|---------|
| rejected | Human decided against pursuing it |
| infeasible | Cannot be built as conceived |
| wishlist | Nice to have but not prioritized |
| legacy | Historical, superseded by newer approach |
| deprecated | No longer relevant |
| archived | Preserved for reference only |

The skill will not automatically expand nodes that are in concept stage, have a hold reason set, or have a disposition. These require human attention before receiving new children.

## When to Use This Skill

Trigger phrases that invoke this skill:
- "Update story tree" - runs the full analysis and generation workflow
- "Generate stories" - creates new stories for under-capacity nodes
- "Show story tree" - displays the current tree structure
- "Tree status" - reports metrics without generating new content
- "Initialize story tree" - creates a fresh database
- Various commands for adjusting capacity or status

## When NOT to Use This Skill

The skill is inappropriate for:
- Adding just one or two specific stories manually
- Backlogs that don't have hierarchical structure
- Projects without git history (the pattern detection needs commits)
- Daily task management (this is strategic planning, not sprint tracking)
- Creating detailed implementation plans (use dedicated planning tools instead)
- Non-software projects

## Autonomous Behavior

The skill operates autonomously by default. When invoked, it:
1. Loads the current tree from the database
2. Analyzes recent git commits for implementation evidence
3. Calculates metrics across all nodes
4. Identifies the highest-priority target for expansion
5. Generates one to three new story concepts
6. Saves them to the database
7. Produces a summary report

Human intervention is requested only when:
- Nodes exceed their capacity limits
- Multiple equally valid priority targets exist
- Git history is ambiguous or unavailable

## Staleness Protection

The skill automatically checks when it was last updated. If more than three days have passed, it runs a full update before processing any other command. This ensures the tree stays synchronized with ongoing development work.

## Quality Standards

Generated stories must meet specific criteria:
- Clear basis in commit history or gap analysis
- Specific and actionable descriptions
- Testable acceptance criteria
- No duplicates of existing stories
- Alignment with established architecture patterns
- Complete user story format (role, capability, benefit)

Stories failing these checks should be revised before being added to the tree.
