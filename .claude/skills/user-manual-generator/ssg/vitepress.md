# VitePress Setup

**When to recommend**: Vue projects, users wanting simplicity and speed, minimal configuration.

## Installation

```bash
npm init
npm add -D vitepress
npx vitepress init
```

Answer the prompts to set up your project.

## Configuration

Create `.vitepress/config.js`:

```javascript
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '[Project Name] Documentation',
  description: 'User guide and reference for [Project Name]',

  base: '/[repo-name]/',

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started/installation' },
      { text: 'Guides', link: '/guides/common-tasks' },
      { text: 'Reference', link: '/reference/configuration' },
    ],

    sidebar: {
      '/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Installation', link: '/getting-started/installation' },
            { text: 'Quick Start', link: '/getting-started/quick-start' },
            { text: 'First Steps', link: '/getting-started/first-steps' },
          ]
        },
        {
          text: 'Guides',
          items: [
            { text: 'Common Tasks', link: '/guides/common-tasks' },
            { text: 'Advanced Usage', link: '/guides/advanced-usage' },
            { text: 'Integrations', link: '/guides/integrations' },
          ]
        },
        {
          text: 'Reference',
          items: [
            { text: 'Configuration', link: '/reference/configuration' },
            { text: 'API Reference', link: '/reference/api-reference' },
            { text: 'CLI Reference', link: '/reference/cli-reference' },
          ]
        },
        {
          text: 'Explanation',
          items: [
            { text: 'Architecture', link: '/explanation/architecture' },
            { text: 'Concepts', link: '/explanation/concepts' },
          ]
        },
        {
          text: 'Troubleshooting',
          items: [
            { text: 'Common Errors', link: '/troubleshooting/common-errors' },
            { text: 'FAQ', link: '/troubleshooting/faq' },
          ]
        },
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/[username]/[repo]' }
    ],

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/[username]/[repo]/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025 [Author/Organization]'
    }
  }
})
```

## Package.json Scripts

Update `package.json`:

```json
{
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  },
  "devDependencies": {
    "vitepress": "^1.0.0"
  }
}
```

## Local Preview

```bash
npm run docs:dev
```

Visit http://localhost:5173

## Build

```bash
npm run docs:build
```

Output: `docs/.vitepress/dist`

## Deploy to GitHub Pages

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: npm
      - run: npm ci
      - run: npm run docs:build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: docs/.vitepress/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

Enable GitHub Pages in repository settings:
- Settings > Pages > Source: GitHub Actions

## Deploy to Netlify

1. Connect repository to Netlify
2. Build command: `npm run docs:build`
3. Publish directory: `docs/.vitepress/dist`

## Deploy to Vercel

1. Connect repository to Vercel
2. Build command: `npm run docs:build`
3. Output directory: `docs/.vitepress/dist`

## Custom Theme Colors

Create `.vitepress/theme/custom.css`:

```css
:root {
  --vp-c-brand-1: #5b8af9;
  --vp-c-brand-2: #3468e4;
  --vp-c-brand-3: #2856c8;
}
```

Reference in `.vitepress/theme/index.js`:

```javascript
import DefaultTheme from 'vitepress/theme'
import './custom.css'

export default DefaultTheme
```

## Admonition Syntax

VitePress uses custom containers:

```markdown
::: info
This is an info box.
:::

::: tip
This is a tip.
:::

::: warning
This is a warning.
:::

::: danger
This is a danger box.
:::
```
