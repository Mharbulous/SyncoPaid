Generate new user story concepts for the backlog using pre-built workflow scripts.

## CI Mode (Automated)

When running in automated/YOLO mode (no user interaction):

1. **Run workflow script** to get target node context:
```bash
python .claude/scripts/story_workflow.py --ci
```

2. **If NO_CAPACITY**, exit successfully - nothing to generate.

3. **Generate story** based on the JSON output:
   - Use target node's description to identify gaps
   - Review existing children to avoid duplicates
   - Create ONE story in user story format (As a/I want/So that)

4. **Insert story** using:
```bash
python .claude/scripts/insert_story.py "<id>" "<parent_id>" "<title>" "<description>"
```

5. **Update commit checkpoint**:
```bash
python .claude/scripts/insert_story.py --update-commit "<newest_commit>"
```

## Interactive Mode

For interactive use with full context gathering and rich output, launch the Xstory GUI:

```bash
venv\Scripts\activate && python dev-tools\xstory\xstory.py
```

Then invoke the `story-writing` skill which provides:
- Detailed git commit analysis
- Goals/non-goals context
- Rich story format with acceptance criteria

## Story Format

```
Title: [Concise description]

As a [role],
I want [capability],
So that [benefit].

Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

## Output Format (CI)

```
Generated 1 story for node [PARENT_ID]:
  - [STORY_ID]: [Title]
```
