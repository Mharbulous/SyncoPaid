# Best Practices

Quick reference for documentation best practices.

## Do's

### Content

- **Start with user research**: Ask questions before generating
- **Follow existing patterns**: Match the project's style/tone
- **Provide examples**: Every concept needs a code sample
- **Link generously**: Connect related topics
- **Mark uncertainty**: Better to flag than to mislead
- **Test locally**: Verify SSG builds before declaring success
- **Plan for maintenance**: Make it easy to regenerate/update

### Writing Style

- **Use "you" and "your"**: Not "the user" or "users"
- **Write in active voice**: "Click the button" not "The button should be clicked"
- **Use present tense**: "The system saves" not "will save"
- **Keep it simple**: Avoid jargon or explain it immediately
- **Be concise**: Get to the point quickly
- **Be consistent**: Use same terminology throughout

### Structure

- **Clear purpose first**: State what the reader will learn
- **Prerequisites upfront**: List what's needed before starting
- **Logical progression**: Build from simple to complex
- **Descriptive headings**: Not clever ones
- **Numbered steps**: For sequential actions
- **Tables for reference**: For option lists, error codes

### Examples

- **Real-world scenarios**: Not toy examples
- **Show expected output**: After every command
- **Include error handling**: Show what happens when things go wrong
- **Before/after comparisons**: For transformations

### Verification

- **Success criteria**: How to know it worked
- **Verification commands**: Test commands after procedures
- **Expected output**: Show what success looks like

## Don'ts

### Content

- **Don't guess**: If you can't find it in code, mark it for review
- **Don't over-generate**: Better 10 great pages than 50 mediocre ones
- **Don't ignore existing docs**: If README has good content, incorporate it
- **Don't forget visuals**: Text-only docs are harder to follow
- **Don't skip testing**: Broken examples destroy credibility
- **Don't make it perfect**: 80% generated, 20% manual refinement is the goal

### Writing Style

- **Don't be condescending**: Avoid "simply" or "just"
- **Don't assume knowledge**: Explain acronyms first use
- **Don't use passive voice**: "Click" not "should be clicked"
- **Don't be verbose**: Get to the point
- **Don't use future tense**: "saves" not "will save"

### Structure

- **Don't bury important info**: Lead with the key point
- **Don't skip heading levels**: h1 → h2 → h3, not h1 → h3
- **Don't use "click here"**: Use descriptive link text
- **Don't create walls of text**: Break up with headings, lists, code

### Examples

- **Don't show incomplete examples**: Always show full, working code
- **Don't use placeholder values**: Use realistic example data
- **Don't hide complexity**: Show the real steps, not simplified versions

## Quality Targets

### Completeness

| Section | Minimum |
|---------|---------|
| Installation guide | Present |
| Quick start | Present |
| How-to guides | 5+ guides |
| Reference | All options documented |
| Troubleshooting | Present |
| FAQ | 10+ questions |

### Code Samples

- Every concept has an example
- All examples show expected output
- All examples have been tested

### Accessibility

- All images have alt text
- Headings follow hierarchy
- Code blocks specify language
- Tables have headers
- Links have descriptive text

### Confidence Levels

Mark each section:

| Level | Meaning | Action |
|-------|---------|--------|
| High | Verified against code | Ship it |
| Medium | Inferred from patterns | Quick review |
| Low | Needs verification | Full review |

## Time Allocation

Recommended effort distribution:

| Activity | Time |
|----------|------|
| Discovery & planning | 10% |
| Code analysis | 15% |
| Content generation | 50% |
| SSG setup | 10% |
| Quality assurance | 10% |
| Handoff | 5% |

## Success Metrics

Documentation is successful when:

1. Non-technical users can complete tasks
2. All major features are covered
3. Zero build errors
4. Passes accessibility checks
5. Deployable to chosen hosting platform

Expected outcome:
- 70-80% time saved vs manual documentation
- ~20% manual refinement needed
- Deployment-ready site in minutes
