# Docusaurus Setup

**When to recommend**: React/JavaScript projects, users wanting rich interactivity, versioning support.

## Installation

```bash
npx create-docusaurus@latest docs classic
cd docs
npm install
```

## Configuration

Create/update `docusaurus.config.js`:

```javascript
// @ts-check
const {themes} = require('prism-react-renderer');
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: '[Project Name] Documentation',
  tagline: 'User guide and reference',
  favicon: 'img/favicon.ico',

  url: 'https://[username].github.io',
  baseUrl: '/[repo-name]/',

  organizationName: '[username]',
  projectName: '[repo-name]',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/[username]/[repo]/tree/main/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: '[Project Name]',
        logo: {
          alt: '[Project Name] Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'doc',
            docId: 'getting-started/installation',
            position: 'left',
            label: 'Getting Started',
          },
          {
            type: 'doc',
            docId: 'guides/common-tasks',
            position: 'left',
            label: 'Guides',
          },
          {
            type: 'doc',
            docId: 'reference/configuration',
            position: 'left',
            label: 'Reference',
          },
          {
            href: 'https://github.com/[username]/[repo]',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'Getting Started',
                to: '/getting-started/installation',
              },
              {
                label: 'Guides',
                to: '/guides/common-tasks',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub Discussions',
                href: 'https://github.com/[username]/[repo]/discussions',
              },
              {
                label: 'Issues',
                href: 'https://github.com/[username]/[repo]/issues',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} [Author/Organization]. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'json', 'yaml', 'python', 'javascript', 'typescript'],
      },
    }),
};

module.exports = config;
```

## Sidebar Configuration

Create `sidebars.js`:

```javascript
/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'index',
      label: 'Home',
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/first-steps',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/common-tasks',
        'guides/advanced-usage',
        'guides/integrations',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/configuration',
        'reference/api-reference',
        'reference/cli-reference',
      ],
    },
    {
      type: 'category',
      label: 'Explanation',
      items: [
        'explanation/architecture',
        'explanation/concepts',
      ],
    },
    {
      type: 'category',
      label: 'Troubleshooting',
      items: [
        'troubleshooting/common-errors',
        'troubleshooting/faq',
      ],
    },
  ],
};

module.exports = sidebars;
```

## Local Preview

```bash
cd docs
npm start
```

Visit http://localhost:3000

## Build

```bash
npm run build
```

Output: `build/` directory

## Deploy to GitHub Pages

### Manual Deploy

```bash
GIT_USER=[username] npm run deploy
```

### Auto-Deploy with GitHub Actions

Create `.github/workflows/docs-deploy.yml`:

```yaml
name: Deploy Docs

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
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: npm
          cache-dependency-path: docs/package-lock.json
      - name: Install dependencies
        working-directory: docs
        run: npm ci
      - name: Build
        working-directory: docs
        run: npm run build
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/build
```

## Deploy to Netlify

1. Connect repository to Netlify
2. Base directory: `docs`
3. Build command: `npm run build`
4. Publish directory: `docs/build`

## Versioning

Docusaurus supports documentation versioning:

```bash
# Create a new version
npm run docusaurus docs:version 1.0

# Versioned docs stored in versioned_docs/
```

## Custom CSS

Edit `src/css/custom.css`:

```css
:root {
  --ifm-color-primary: #2e8555;
  --ifm-color-primary-dark: #29784c;
  --ifm-color-primary-darker: #277148;
  --ifm-color-primary-darkest: #205d3b;
  --ifm-color-primary-light: #33925d;
  --ifm-color-primary-lighter: #359962;
  --ifm-color-primary-lightest: #3cad6e;
}
```

## Admonition Syntax

Docusaurus uses `:::` syntax:

```markdown
:::note
This is a note.
:::

:::warning
This is a warning.
:::

:::tip
This is a tip.
:::

:::danger
This is dangerous.
:::
```
