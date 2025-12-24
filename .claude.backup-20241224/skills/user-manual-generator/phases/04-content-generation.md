# Phase 4: Content Generation

Generate documentation content following these guidelines and using templates from the `templates/` directory.

## Writing Guidelines

### 1. User-Focused Language
- Use "you" and "your" (not "the user")
- Active voice ("Click the button" not "The button should be clicked")
- Present tense ("The system saves your data" not "will save")
- Simple words (avoid jargon or explain it immediately)

### 2. Clear Structure
- Start with what the user will accomplish
- Use descriptive headings (not clever ones)
- Break long content into sections
- Use lists for sequential steps
- Use tables for reference material

### 3. Examples Everywhere
- Code samples for every concept
- Real-world scenarios, not toy examples
- Expected output shown after commands
- Before/after comparisons

### 4. Contextual Help
- Prerequisites stated upfront
- Links to related topics
- Warnings before destructive operations
- Success criteria (how to know it worked)

## Templates

Load templates as needed from the `templates/` directory:

| Template File | Use For |
|--------------|---------|
| `templates/installation.md` | Installation guide |
| `templates/quick-start.md` | Quick start guide |
| `templates/how-to-guide.md` | Task-oriented guides |
| `templates/configuration-reference.md` | Config options reference |
| `templates/api-reference.md` | API endpoint documentation |
| `templates/cli-reference.md` | CLI command reference |
| `templates/troubleshooting.md` | Error messages and FAQ |

## Content Generation Process

For each documentation file:

1. **Determine the purpose**: Tutorial, how-to, reference, or explanation?
2. **Extract relevant code**: Find the features/config/commands to document
3. **Use appropriate template**: Follow the structure from templates
4. **Write user-focused content**: Follow the writing guidelines
5. **Add examples**: Real code samples with expected output
6. **Cross-reference**: Link to related documentation
7. **Add placeholders**: Mark where screenshots/videos would help

## Placeholder Format

Use these formats to mark where visual content is needed:

```markdown
> **Screenshot needed**: [Description of what screenshot should show]
>
> **Location**: [Where in the UI or workflow this screenshot belongs]

> **Video tutorial**: [Description of what video should demonstrate]
>
> **Duration**: [Suggested length, e.g., "2-3 minutes"]
```

## Quality Checklist Per File

Before moving to the next file, verify:

- [ ] Clear purpose stated at the top
- [ ] Prerequisites listed if any
- [ ] All code examples have expected output
- [ ] Links to related topics included
- [ ] Warnings for destructive operations
- [ ] Success criteria provided

## Next Phase

Once content is generated, proceed to **Phase 5: Static Site Setup** by reading `phases/05-static-site-setup.md`.
