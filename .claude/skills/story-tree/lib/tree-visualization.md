# Tree Visualization

For any tree visualization needs, use the `tree-view.py` script rather than constructing ASCII trees manually.

## CRITICAL: Presenting Tree Diagrams to Users

**Problem:** Claude Code truncates bash command output (e.g., showing `... +42 lines`). When you run `tree-view.py`, the user often cannot see the actual tree diagram.

**Solution:** When the user asks to "show the story tree" or "show a diagram", you MUST:

1. **Capture output to a file**, then read and present it:
   ```bash
   # Save output to temp file
   python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii > /tmp/story-tree-output.txt
   ```

2. **Read the file using the Read tool** (not cat/bash)

3. **Present the tree in your response text** as a properly formatted code block:
   ```
   Here's your current story tree:

   ```
   ListBot [8/10] O
   +-- (1) File Upload & Deduplication [8/8] +
   |   +-- (1.1) Hash-Based File Deduplication [0/4] +
   |   +-- (1.2) Drag-and-Drop Upload Interface [0/3] +
   ...
   ```
   ```

4. **Add a legend and insights** after the tree:
   - Explain the status symbols (`.` = concept, `+` = implemented, etc.)
   - Highlight notable patterns (under-capacity nodes, next priorities)
   - Summarize key metrics (total stories, completion percentage)

**DO NOT:**
- Show raw bash output and expect the user to see it (it gets truncated)
- Use `cat` or `echo` to display the tree (same truncation issue)
- Skip the visualization when output is too long

**Example workflow for "show story tree":**
```bash
# Step 1: Generate tree to temp file
python .claude/skills/story-tree/tree-view.py --show-capacity --force-ascii > /tmp/tree.txt 2>&1
```
Then use Read tool to read `/tmp/tree.txt`, and present the contents in your response.

## Basic Usage

```bash
# Full tree with capacity and status indicators
python .claude/skills/story-tree/tree-view.py --show-capacity --show-status --force-ascii

# Subtree from a specific node with depth limit
python .claude/skills/story-tree/tree-view.py --root 1.1 --depth 2

# Filter by status (e.g., only implemented stories)
python .claude/skills/story-tree/tree-view.py --status implemented --compact

# Markdown format for documentation
python .claude/skills/story-tree/tree-view.py --format markdown --show-capacity

# Exclude deprecated stories
python .claude/skills/story-tree/tree-view.py --status deprecated --exclude-status
```

**When to use:**
- Generating report tree visualization (Step 7)
- Answering user questions about tree structure
- Creating documentation that shows tree state
- Debugging tree integrity issues

## Status Symbols (ASCII)

| Status | Symbol |
|--------|--------|
| concept | `.` |
| approved | `v` |
| rejected | `x` |
| planned | `o` |
| queued | `@` |
| active | `O` |
| in-progress | `D` |
| bugged | `!` |
| implemented | `+` |
| ready | `#` |
| deprecated | `-` |
| infeasible | `0` |

**Note:** Use `--force-ascii` on Windows cmd.exe to avoid encoding issues.
