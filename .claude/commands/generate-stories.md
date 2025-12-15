Generate new user story concepts for the backlog using the story-tree skill.

## Steps

1. Launch the Xstory GUI in the background:

```bash
venv\Scripts\activate && python dev-tools\xstory\xstory.py
```

2. Delegate story generation to a subagent using the Task tool:

```
Task(
  subagent_type="general-purpose",
  description="Execute story-tree skill workflow",
  prompt="""
Read the skill file at `.claude/skills/story-tree/SKILL.md` and execute the complete 7-step workflow:

1. Initialize/Load Database (if needed)
2. Analyze Git Commits (incremental from checkpoint)
3. Identify Priority Target (using the SQL query in the skill)
4. Generate Stories (max 3 per target node, in exact format specified)
5. Insert Stories (using closure table pattern)
6. Update Metadata (lastUpdated, lastAnalyzedCommit)
7. Output Report (following the template in the skill)

IMPORTANT:
- Follow the skill instructions EXACTLY - do not improvise
- Use Python sqlite3 module, NOT sqlite3 CLI
- Scripts are in `.claude/skills/story-tree/scripts/`, not project root
- Return ONLY the final "Story Tree Update Report" with tree visualization
- Do NOT return intermediate debug output
"""
)
```

3. Present the returned report to the user. The Xstory GUI will already be open for them to review and approve/reject the new concept stories.
