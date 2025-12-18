# Current Orchestrator Workflow (As Implemented)

This diagram shows the **actual current state** of the story-tree automation as it exists today.

---

## Overview

The current system has **two parallel automation patterns**:

1. **Standalone Workflows** - Individual scheduled workflows that run at fixed times
2. **Orchestrator Loop** - A drain-pipeline loop that processes Plan→Write→Vet

---

## Standalone Workflow Sequence (Time-Based)

These workflows run independently on a daily schedule:

```mermaid
flowchart LR
    subgraph "Daily Schedule (PST)"
        direction TB
        T1["2:00 AM"]
        T2["2:30 AM"]
        T3["3:00 AM"]
        T4["3:30 AM"]
    end

    subgraph "write-stories.yml"
        W1[NEW] -->|"capacity check"| W2["concept (no hold)"]
    end

    subgraph "plan-stories.yml"
        P1["approved (no hold)"] -->|"create TDD plan"| P2["planned (no hold)"]
    end

    subgraph "activate-stories.yml"
        A1["planned (no hold)"] -->|"deps met"| A2["active (no hold)"]
        A1 -->|"deps unmet"| A3["planned (blocked)"]
    end

    subgraph "execute-stories.yml"
        E1["active (no hold)"] -->|"blocking issues"| E2["active (paused)"]
        E1 -->|"deferrable issues"| E3["reviewing (no hold)"]
        E1 -->|"no issues"| E4["verifying (no hold)"]
    end

    T1 --> W1
    T2 --> P1
    T3 --> A1
    T4 --> E1
```

---

## Orchestrator Loop (story-tree-orchestrator.yml)

The orchestrator runs a **drain-pipeline loop** that processes stories through three steps per cycle:

```mermaid
flowchart TD
    START([Workflow Triggered<br/>Daily 2:00 AM PST or Manual])

    GATE{Gate Job:<br/>STORY_AUTOMATION_ENABLED?}
    START --> GATE

    GATE -->|false| DISABLED([Exit: Automation Disabled])
    GATE -->|true| INIT

    subgraph LOOP["Drain Pipeline Loop (max 5 cycles)"]
        INIT[Initialize Cycle]

        subgraph STEP1["Step 1: Plan Stories"]
            S1_CHECK{Approved stories<br/>without holds?}
            S1_PLAN["story-planning skill"]
            S1_COMMIT[Commit & Push]
            S1_RESULT["plan_result = SUCCESS"]
            S1_NONE["plan_result = NO_APPROVED"]
        end

        subgraph STEP2["Step 2: Write Stories"]
            S2_CHECK{Capacity available<br/>for new stories?}
            S2_WRITE["story_workflow.py<br/>+ Claude generates story"]
            S2_COMMIT[Commit & Push]
            S2_RESULT["write_result = SUCCESS"]
            S2_NONE["write_result = NO_CAPACITY"]
        end

        subgraph STEP3["Step 3: Vet Stories"]
            S3_VET["story-vetting skill"]
            S3_CHECK{Conflicts found?}
            S3_DEFER["Set hold_reason='pending'<br/>for HUMAN_REVIEW cases"]
            S3_COMMIT[Commit & Push]
            S3_DONE[Vetting complete]
        end

        INIT --> S1_CHECK
        S1_CHECK -->|Yes| S1_PLAN
        S1_PLAN --> S1_COMMIT
        S1_COMMIT --> S1_RESULT
        S1_CHECK -->|No| S1_NONE
        S1_RESULT --> S2_CHECK
        S1_NONE --> S2_CHECK

        S2_CHECK -->|Yes| S2_WRITE
        S2_WRITE --> S2_COMMIT
        S2_COMMIT --> S2_RESULT
        S2_CHECK -->|No| S2_NONE
        S2_RESULT --> S3_VET
        S2_NONE --> S3_VET

        S3_VET --> S3_CHECK
        S3_CHECK -->|Yes| S3_DEFER
        S3_DEFER --> S3_COMMIT
        S3_COMMIT --> S3_DONE
        S3_CHECK -->|No| S3_DONE

        S3_DONE --> EXIT_CHECK

        EXIT_CHECK{plan_result = NO_APPROVED<br/>AND<br/>write_result = NO_CAPACITY?}
    end

    EXIT_CHECK -->|Yes| IDLE([Exit: IDLE<br/>Pipeline drained])
    EXIT_CHECK -->|No| NEXT_CYCLE{cycle < max_cycles?}
    NEXT_CYCLE -->|Yes| INIT
    NEXT_CYCLE -->|No| MAX([Exit: MAX_CYCLES<br/>Safety limit])

    IDLE --> SUMMARY
    MAX --> SUMMARY

    SUMMARY[Summary Job:<br/>Generate progress report]
```

---

## Stage Transitions Covered by Current Orchestrator

```mermaid
stateDiagram-v2
    direction LR

    state "📝 NEW" as NEW
    state "💡 concept (no hold)" as CONCEPT
    state "💡 concept (pending)" as CONCEPT_PENDING
    state "✅ approved (no hold)" as APPROVED
    state "📋 planned (no hold)" as PLANNED

    [*] --> NEW: capacity exists

    NEW --> CONCEPT: write-stories<br/>(Step 2)

    CONCEPT --> CONCEPT_PENDING: story-vetting<br/>(Step 3)<br/>conflict detected

    CONCEPT_PENDING --> APPROVED: HUMAN<br/>clears hold
    CONCEPT --> APPROVED: HUMAN<br/>approves

    APPROVED --> PLANNED: story-planning<br/>(Step 1)

    note right of PLANNED: ⚠️ Orchestrator stops here
```

---

## What's NOT in the Current Orchestrator

The orchestrator does **not** handle these transitions (they require standalone workflows or manual action):

| From Stage | To Stage | Current Handler | Gap |
|------------|----------|-----------------|-----|
| `concept` | `approved` | Human manual | No auto-approve after clean vet |
| `planned` | `active` | `activate-stories.yml` | Not integrated |
| `planned` | `blocked` | `activate-stories.yml` | Not integrated |
| `active` | `reviewing` | `execute-stories.yml` | Not integrated |
| `active` | `verifying` | `execute-stories.yml` | Not integrated |
| `active` | `paused` | `execute-stories.yml` | Not integrated |
| `reviewing` | `verifying` | None | Missing workflow |
| `verifying` | `implemented` | None | Missing workflow |
| `implemented` | `ready` | None | Missing workflow |
| `ready` | `released` | `deploy.yml` | Keep separate |

---

## Current Workflow File Summary

| Workflow | Purpose | Transitions | Integrated? |
|----------|---------|-------------|-------------|
| `story-tree-orchestrator.yml` | Drain pipeline loop | approved→planned, NEW→concept, conflict→pending | ✅ Main |
| `write-stories.yml` | Generate stories | NEW→concept | ❌ Standalone |
| `plan-stories.yml` | Plan stories | approved→planned | ❌ Standalone |
| `activate-stories.yml` | Activate stories | planned→active/blocked | ❌ Standalone |
| `execute-stories.yml` | Execute stories | active→reviewing/verifying/paused | ❌ Standalone |
| `deploy.yml` | Deploy releases | ready→released | ❌ Keep separate |

---

*Generated: 2025-12-18*
