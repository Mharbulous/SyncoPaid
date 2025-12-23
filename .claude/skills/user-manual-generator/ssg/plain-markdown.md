# Plain Markdown Setup

**When to recommend**: Simple projects, users wanting minimal setup, GitHub-only hosting.

## Overview

Plain Markdown requires no build step. GitHub renders `.md` files natively, making this the simplest option for documentation.

## Directory Structure

```
docs/
├── README.md                         # Landing page (GitHub shows this)
├── getting-started/
│   ├── README.md                     # Section index
│   ├── installation.md
│   ├── quick-start.md
│   └── first-steps.md
├── guides/
│   ├── README.md
│   ├── common-tasks.md
│   ├── advanced-usage.md
│   └── integrations.md
├── reference/
│   ├── README.md
│   ├── configuration.md
│   ├── api-reference.md
│   └── cli-reference.md
├── explanation/
│   ├── README.md
│   ├── architecture.md
│   └── concepts.md
└── troubleshooting/
    ├── README.md
    ├── common-errors.md
    └── faq.md
```

## Main Navigation

Create `docs/README.md`:

```markdown
# [Project Name] Documentation

Welcome to the [Project Name] user guide.

## Getting Started

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [First Steps](getting-started/first-steps.md)

## Guides

- [Common Tasks](guides/common-tasks.md)
- [Advanced Usage](guides/advanced-usage.md)
- [Integrations](guides/integrations.md)

## Reference

- [Configuration](reference/configuration.md)
- [API Reference](reference/api-reference.md)
- [CLI Reference](reference/cli-reference.md)

## Explanation

- [Architecture](explanation/architecture.md)
- [Concepts](explanation/concepts.md)

## Troubleshooting

- [Common Errors](troubleshooting/common-errors.md)
- [FAQ](troubleshooting/faq.md)

## Getting Help

[How to get support]
```

## Section Index Pages

Create `README.md` in each section folder:

```markdown
# Getting Started

New to [Project Name]? Start here!

- [Installation](installation.md) - Install [Project Name] on your system
- [Quick Start](quick-start.md) - Get up and running in 5 minutes
- [First Steps](first-steps.md) - Complete your first meaningful task

---

[Back to Documentation Home](../README.md)
```

## Enable GitHub Pages

1. Go to repository **Settings**
2. Click **Pages** in the sidebar
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/docs**
4. Click **Save**

Your documentation will be available at:
`https://[username].github.io/[repo-name]/`

## Linking Best Practices

### Relative Links

Always use relative links for internal navigation:

```markdown
<!-- Good -->
[Installation](getting-started/installation.md)
[Back to Home](../README.md)

<!-- Bad - won't work on GitHub -->
[Installation](/docs/getting-started/installation.md)
```

### Section Anchors

Link to specific sections:

```markdown
[See Configuration Options](reference/configuration.md#environment-variables)
```

### External Links

Open external links in same tab (GitHub behavior):

```markdown
[GitHub Repository](https://github.com/username/repo)
```

## Images

Store images in an `assets` or `images` folder:

```
docs/
├── assets/
│   ├── screenshot-1.png
│   └── diagram.svg
```

Reference images with relative paths:

```markdown
![Screenshot](assets/screenshot-1.png)
```

## Tables

GitHub renders tables nicely:

```markdown
| Option | Default | Description |
|--------|---------|-------------|
| `port` | `8080` | Server port |
| `host` | `localhost` | Server host |
```

## Code Blocks

Specify language for syntax highlighting:

```markdown
```python
def hello():
    print("Hello, World!")
```
```

## Callouts (Limited)

GitHub doesn't support native callouts, but you can use:

```markdown
> **Note**: This is a note.

> **Warning**: This is a warning.

> **Tip**: This is a tip.
```

Or use HTML:

```markdown
<details>
<summary>Click to expand</summary>

Hidden content here.

</details>
```

## Advantages

- Zero build step
- No dependencies
- GitHub renders natively
- Version controlled with code
- Works offline

## Disadvantages

- No search functionality
- Limited theming
- No admonition boxes
- Basic navigation only
- No automatic table of contents
