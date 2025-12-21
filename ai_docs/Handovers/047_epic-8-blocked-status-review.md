# Handover: Epic 8 Blocked Status Review

## Context

Epic 8 (LLM & AI Integration) and several child stories are marked `blocked` by CI automation. We just added stories 8.6-8.10 for local LLM integration (Moondream 2/3). The question: should Epic 8 remain blocked, or does the new local LLM path unblock it?

## Current State

```
Epic 8: LLM & AI Integration (stage=planned, hold_reason=blocked)
├── 8.1: Matter/Client Database (blocked)
├── 8.2: Browser URL Extraction (active) ← not blocked
├── 8.3: UI Automation Integration (blocked)
├── 8.4: AI Disambiguation with Screenshot Context (blocked)
│   ├── 8.4.1: Activity-to-Matter Matching (blocked)
│   └── 8.4.2: Transition Detection & Smart Prompts (reviewing)
├── 8.5: LLM API Integration & Batch Categorization (approved)
├── 8.6: Local LLM Engine Architecture (concept) ← NEW
├── 8.7: Hardware Detection & Model Selection (concept) ← NEW
├── 8.8: Moondream 2 Integration (CPU-Friendly) (concept) ← NEW
├── 8.9: Moondream 3 Integration (GPU-Accelerated) (concept) ← NEW
└── 8.10: First-Run Model Download & Cache Management (concept) ← NEW
```

## Key Files

| Purpose | Path |
|---------|------|
| Story database | `.claude/data/story-tree.db` |
| Blocked plan for 8.4 | `.claude/data/plans/blocked/007_ai-disambiguation-foundation.md` |
| Blocked plan for 8.1 | `.claude/data/plans/blocked/006A_matter-client-db-schema.md` |
| Moondream 2 checklist | `ai_docs/MoonDream/moondream2-integration-checklist.md` |
| Deprecated cloud LLM plan | `deprecated/019_llm-ai-integration.md` (used OpenAI/Anthropic - obsolete) |

## Why Stories Are Blocked

Notes in database show `BLOCKED by CI: 2025-12-18 05:21:06` - an automated workflow marked these blocked. Original dependency chain assumed cloud LLM APIs (OpenAI/Anthropic), which conflicts with privacy requirements for attorney-client privilege.

## Decision Points

1. **Unblock 8.1 (Matter/Client Database)?** - This is infrastructure, not dependent on LLM choice. The plan in `007_ai-disambiguation-foundation.md` includes matter DB schema. Could proceed independently.

2. **Unblock 8.4 (AI Disambiguation)?** - Depends on having an LLM engine. With 8.6-8.10 providing local LLM path, the blocker may be resolved.

3. **Keep 8.3 blocked?** - UI Automation (Outlook/Explorer context extraction) is independent of LLM choice but complex. May stay blocked for other reasons.

4. **Update Epic 8 hold_reason?** - Change from `blocked` to something else (or clear it) now that local LLM stories exist.

## Questions to Resolve

- Should Matter/Client Database (8.1) be unblocked since it's pure infrastructure?
- Does adding 8.6-8.10 change the blocking dependency for 8.4?
- What was the original reason for CI blocking these? (Check workflow logs if needed)

## Relevant Workflow

The CI blocking may come from: `.github/workflows/story-tree-orchestrator.yml`

## Task

Determine whether to change the `hold_reason` status for Epic 8 and its blocked children now that local LLM integration stories exist.
