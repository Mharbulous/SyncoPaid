Generate new user story concepts using the brainstorm-story skill.

Use the Skill tool to invoke the `brainstorm-story` skill, which will:

1. Check for vision files (`ai_docs/user-vision.md` and `ai_docs/user-anti-vision.md`)
2. Gather context for the target parent node
3. Analyze relevant git commits
4. Identify gaps in functionality
5. Generate up to 3 evidence-based user stories
6. Insert stories into the story-tree database with `concept` status
7. Output a generation report

If the user specifies a node ID (e.g., `/write-stories 1.2`), generate stories for that specific node.
If no node is specified, ask the user which node they want to brainstorm stories for.
