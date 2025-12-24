# MkDocs Material Setup

**When to recommend**: Python projects, users wanting beautiful Material Design, excellent search.

## Installation

```bash
pip install mkdocs mkdocs-material mkdocs-minify-plugin
```

Or create `requirements-docs.txt`:

```txt
mkdocs>=1.5.0
mkdocs-material>=9.4.0
mkdocs-minify-plugin>=0.7.0
```

## Configuration

Create `mkdocs.yml` in project root:

```yaml
site_name: [Project Name] Documentation
site_description: User guide and reference for [Project Name]
site_author: [Author/Organization]
site_url: https://[username].github.io/[repo-name]

theme:
  name: material
  palette:
    # Light mode
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate

plugins:
  - search
  - minify:
      minify_html: true

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - attr_list
  - md_in_html

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
      - First Steps: getting-started/first-steps.md
  - Guides:
      - Common Tasks: guides/common-tasks.md
      - Advanced Usage: guides/advanced-usage.md
      - Integrations: guides/integrations.md
  - Reference:
      - Configuration: reference/configuration.md
      - API Reference: reference/api-reference.md
      - CLI Reference: reference/cli-reference.md
  - Explanation:
      - Architecture: explanation/architecture.md
      - Concepts: explanation/concepts.md
  - Troubleshooting:
      - Common Errors: troubleshooting/common-errors.md
      - FAQ: troubleshooting/faq.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/[username]/[repo]
```

## Local Preview

```bash
mkdocs serve
```

Visit http://127.0.0.1:8000

## Build

```bash
mkdocs build
```

Output: `site/` directory

## Deploy to GitHub Pages

### Manual Deploy

```bash
mkdocs gh-deploy
```

This builds and pushes to the `gh-pages` branch.

### Auto-Deploy with GitHub Actions

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: pip install mkdocs-material mkdocs-minify-plugin
      - run: mkdocs gh-deploy --force
```

## Deploy to Netlify

1. Connect repository to Netlify
2. Build command: `mkdocs build`
3. Publish directory: `site`

## Deploy to Vercel

1. Connect repository to Vercel
2. Build command: `pip install mkdocs-material && mkdocs build`
3. Output directory: `site`

## Customization

### Colors

In `mkdocs.yml`:

```yaml
theme:
  palette:
    primary: blue  # Options: red, pink, purple, deep purple, indigo, blue, light blue, cyan, teal, green, light green, lime, yellow, amber, orange, deep orange
    accent: blue
```

### Logo and Favicon

```yaml
theme:
  logo: assets/logo.png
  favicon: assets/favicon.png
```

### Custom CSS

Create `docs/stylesheets/extra.css`:

```css
:root {
  --md-primary-fg-color: #your-color;
}
```

Reference in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
```

## Admonition Syntax

MkDocs Material supports callout boxes:

```markdown
!!! note
    This is a note.

!!! warning
    This is a warning.

!!! tip
    This is a tip.

!!! danger
    This is dangerous.
```
