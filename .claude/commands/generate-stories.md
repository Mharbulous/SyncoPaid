Generate user story concepts for the backlog.

## CI Mode (Automated)

```bash
python .claude/scripts/story_workflow.py --ci
```

- If `NO_CAPACITY`, exit successfully
- Generate ONE story based on JSON output using target node's description
- Avoid duplicates by reviewing existing children

```bash
python .claude/scripts/insert_story.py "<id>" "<parent_id>" "<title>" "<description>"
python .claude/scripts/insert_story.py --update-commit "<newest_commit>"
```

## Interactive Mode

Launch Xstory GUI then invoke the `story-writing` skill:
```bash
venv\Scripts\activate && python dev-tools\xstory\xstory.py
```

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
