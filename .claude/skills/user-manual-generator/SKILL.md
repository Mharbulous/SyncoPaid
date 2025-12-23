---
name: user-manual-generator
description: Generate comprehensive end-user documentation from application codebases
version: 1.0.0
allowed-tools: [Read, Write, Glob, Grep, Bash, Edit]
tags: [documentation, user-manual, static-site, markdown]
---

# User Manual Generator

Generate comprehensive, deployment-ready user documentation from application codebases using intelligent code analysis and documentation best practices.

## Overview

This skill analyzes your codebase to automatically generate user-focused documentation (not developer/API docs). It creates deployment-ready static sites compatible with GitHub Pages, Netlify, and Vercel, following the Diataxis framework (tutorials, how-to guides, reference, explanation).

**Use this skill when you need to:**
- Create end-user documentation for web apps, APIs, CLI tools, or desktop applications
- Generate documentation that helps users accomplish tasks, not just understand code
- Deploy professional documentation sites quickly
- Establish a documentation foundation that evolves with your code

**Don't use this skill for:**
- API-only documentation (use OpenAPI/Swagger generators instead)
- Internal developer documentation (use JSDoc/Sphinx/Godoc)
- Simple README files (write those manually)

## Quick Start

When invoked, this skill will:

1. **Ask clarifying questions** about your project and preferences
2. **Analyze your codebase** to extract user-facing features
3. **Generate documentation** following best practices
4. **Set up a static site** with your chosen generator
5. **Provide deployment instructions** for immediate publishing

## Phase 1: Discovery & Requirements Gathering

### Initial Questions

Start by asking the user these questions to configure the documentation generation:

```
I'll help you generate comprehensive user documentation for your project. Let me ask a few questions to customize the output:

1. **Application Type**: What type of application is this?
   - Web application (React, Vue, Angular, etc.)
   - REST/GraphQL API
   - CLI tool
   - Desktop application (Electron, etc.)
   - Full-stack application
   - Other (please specify)

2. **Target Audience**: Who will use this documentation?
   - End users (non-technical)
   - API consumers (developers integrating your service)
   - System administrators
   - Mixed audience

3. **Static Site Generator**: Which documentation framework do you prefer?
   - MkDocs Material (Python-based, beautiful Material Design)
   - Docusaurus (React-based, used by Meta/Facebook)
   - VitePress (Vue-based, fast and lightweight)
   - Plain Markdown (no static site generator, just .md files)
   - Recommend one for me

4. **Deployment Target**: Where will you host the documentation?
   - GitHub Pages
   - Netlify
   - Vercel
   - Self-hosted
   - Not sure yet

5. **Documentation Depth**: How comprehensive should the documentation be?
   - Quick start only (minimal, get users running fast)
   - Standard (getting started + common tasks + reference)
   - Comprehensive (full coverage with examples and explanations)

6. **Additional Sections**: Should I include? (select all that apply)
   - Troubleshooting guide
   - FAQ
   - Architecture explanation (for advanced users)
   - Contributing guide
   - Changelog/release notes template
   - Video tutorial placeholders
```

Store these preferences for later use in generation.

### Codebase Discovery

Use the following tools to understand the project structure:

**1. Identify Project Type:**

```bash
# Check for package managers and frameworks
ls -la | grep -E "(package.json|requirements.txt|Gemfile|go.mod|pom.xml|Cargo.toml|composer.json)"

# Check for common config files
ls -la | grep -E "(vite.config|webpack.config|tsconfig.json|next.config|nuxt.config|angular.json)"
```

**2. Map Project Structure:**

Use `Glob` to find key files:
- Entry points: `**/*main*.{js,ts,py,go,java}`, `**/index.{js,ts,html}`, `**/__main__.py`
- Routes/navigation: `**/routes/**/*.{js,ts}`, `**/pages/**/*.{js,ts,tsx,jsx}`, `**/urls.py`
- CLI definitions: `**/cli.{js,ts,py}`, `**/commands/**/*.{js,ts,py}`
- Configuration: `**/config/*.{js,ts,py,json,yaml,toml}`, `.env.example`
- Components: `**/components/**/*.{jsx,tsx,vue}`, `**/views/**/*.py`

**3. Detect Technology Stack:**

Based on files found, determine:
- **Frontend framework**: React, Vue, Angular, Svelte, vanilla JS
- **Backend framework**: Express, FastAPI, Django, Flask, Spring Boot, Rails
- **Language**: JavaScript/TypeScript, Python, Java, Go, Ruby, PHP
- **Build tools**: Vite, Webpack, Rollup, Parcel
- **Package manager**: npm, yarn, pnpm, pip, poetry, maven, gradle

## Phase 2: Feature Extraction

### For Web Applications

**Extract Routes and Navigation:**

```bash
# React Router / Next.js
grep -r "Route path=" --include="*.jsx" --include="*.tsx"
grep -r "export default function.*Page" app/ pages/

# Vue Router
grep -r "path:" --include="router.js" --include="*.route.js"

# Angular
grep -r "path:" --include="*.routing.ts"
```

**Identify User-Facing Components:**

Use `Grep` to find:
- Form components: Search for `<form`, `onSubmit`, `FormProvider`, `useForm`
- Interactive elements: `onClick`, `onChange`, `@click`, `@change`
- Modal/dialog components: `Dialog`, `Modal`, `Popup`
- Navigation: `Navbar`, `Sidebar`, `Menu`, `Header`

**Extract UI Features:**

Read key component files to understand:
- Input validation rules (for documenting constraints)
- Error messages (for troubleshooting section)
- Success messages (for expected outcomes)
- Button labels and actions (for task documentation)

### For Backend APIs

**Extract Endpoints:**

```bash
# Express/Fastify
grep -r "router\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"
grep -r "app\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"

# Django/Flask
grep -r "@app\.route\|path(" --include="*.py"
grep -r "class.*ViewSet\|class.*APIView" --include="*.py"

# FastAPI
grep -r "@app\.\(get\|post\|put\|delete\|patch\)" --include="*.py"
```

**Find Authentication Patterns:**

```bash
# Look for auth middleware/decorators
grep -r "authenticate\|authorize\|@login_required\|requireAuth" --include="*.{js,ts,py}"

# Look for API key handling
grep -r "API_KEY\|apiKey\|x-api-key\|Authorization" --include="*.{js,ts,py}"
```

**Extract Request/Response Schemas:**

- Look for TypeScript interfaces/types near API routes
- Find Pydantic models, Joi schemas, Yup validators
- Check for OpenAPI/Swagger annotations

### For CLI Applications

**Extract Commands and Options:**

```bash
# Node.js (Commander, Yargs)
grep -r "\.command\|\.option\|\.argument" --include="*.js" --include="*.ts"

# Python (argparse, click, typer)
grep -r "add_argument\|@click\.command\|@app\.command" --include="*.py"

# Go (cobra, flag)
grep -r "cobra\.Command\|flag\." --include="*.go"
```

**Find Help Text:**

Read command definition files to extract:
- Command descriptions
- Argument descriptions
- Option flags and their purposes
- Usage examples (often in help text)

### For Desktop Applications

**Extract Menu Structures:**

```bash
# Electron
grep -r "Menu\.buildFromTemplate\|new MenuItem" --include="*.js" --include="*.ts"
```

**Find Settings/Preferences:**

```bash
grep -r "settings\|preferences\|config" --include="*.{js,ts,json}"
```

### Cross-Application Analysis

**Configuration Options:**

Read these files to document user-configurable settings:
- `.env.example` or `env.sample`
- `config/default.json`, `config.example.js`
- Settings files in user data directories
- Command-line argument parsers

**Error Messages for Troubleshooting:**

```bash
# Find error messages
grep -r "throw new Error\|raise Exception\|console\.error" --include="*.{js,ts,py}" | head -50

# Find validation messages
grep -r "validation\|validator\|schema" --include="*.{js,ts,py}"
```

**Example Code:**

Check for:
- `examples/` directory
- `demo/` directory
- Test files that show usage patterns
- README code samples

## Phase 3: Documentation Structure Planning

Based on the Diataxis framework, organize extracted information into:

### 1. Tutorials (Learning-Oriented)

**Getting Started**: First-time user experience
- Installation/setup
- Quick start (minimal viable usage)
- First meaningful task completion
- Understanding basic concepts

**Target**: New users who need hand-holding

### 2. How-To Guides (Task-Oriented)

**Common Tasks**: Problem-solving focused
- Each guide solves one specific problem
- Step-by-step instructions
- Assumes basic knowledge
- Shows different ways to accomplish goals

**Examples by application type:**
- **Web app**: "How to reset your password", "How to export data", "How to customize your dashboard"
- **API**: "How to authenticate requests", "How to handle rate limits", "How to paginate results"
- **CLI**: "How to process batch files", "How to configure output format", "How to automate workflows"

### 3. Reference (Information-Oriented)

**Technical Specifications**: Precise, comprehensive
- Configuration reference (all settings with defaults)
- API reference (all endpoints with parameters)
- CLI reference (all commands with options)
- Error codes and meanings
- Data formats and schemas

**Target**: Users who know what they're looking for

### 4. Explanation (Understanding-Oriented)

**Concepts and Architecture**: Why things work the way they do
- Key concepts explained
- Architecture overview (from user perspective, not developer)
- Design decisions that affect usage
- Limitations and constraints
- Security model

**Target**: Users who want deeper understanding

### 5. Troubleshooting

**Common Problems**: Reactive help
- Error messages with solutions
- FAQs from issues/discussions
- Performance problems
- Compatibility issues

### Documentation Hierarchy

Create this structure (adapt based on application type):

```
docs/
├── index.md                          # Landing page with overview
├── getting-started/
│   ├── installation.md               # Platform-specific install steps
│   ├── quick-start.md                # 5-minute "hello world"
│   └── first-steps.md                # Complete first meaningful task
├── guides/                           # How-to guides
│   ├── common-tasks.md               # Frequent user operations
│   ├── advanced-usage.md             # Power user features
│   ├── integrations.md               # Connect with other tools
│   └── workflows.md                  # End-to-end scenarios
├── reference/
│   ├── configuration.md              # All config options
│   ├── api-reference.md              # (for APIs) All endpoints
│   ├── cli-reference.md              # (for CLIs) All commands
│   └── error-codes.md                # Error reference
├── explanation/
│   ├── architecture.md               # How it works (user view)
│   ├── concepts.md                   # Key ideas explained
│   └── limitations.md                # What it can't do and why
└── troubleshooting/
    ├── common-errors.md              # Error messages + fixes
    └── faq.md                        # Frequently asked questions
```

## Phase 4: Content Generation

### Writing Guidelines

Follow these principles when generating documentation content:

**1. User-Focused Language**
- Use "you" and "your" (not "the user")
- Active voice ("Click the button" not "The button should be clicked")
- Present tense ("The system saves your data" not "will save")
- Simple words (avoid jargon or explain it immediately)

**2. Clear Structure**
- Start with what the user will accomplish
- Use descriptive headings (not clever ones)
- Break long content into sections
- Use lists for sequential steps
- Use tables for reference material

**3. Examples Everywhere**
- Code samples for every concept
- Real-world scenarios, not toy examples
- Expected output shown after commands
- Before/after comparisons

**4. Contextual Help**
- Prerequisites stated upfront
- Links to related topics
- Warnings before destructive operations
- Success criteria (how to know it worked)

### Template: Installation Guide

```markdown
# Installation

## Prerequisites

Before installing [Project Name], ensure you have:

- [Requirement 1] (version X.X or higher)
- [Requirement 2]
- [Operating System requirements]

## Installation Steps

### Windows

1. Download the installer from [link]
2. Run the installer
3. Follow the setup wizard
4. Verify installation:
   ```bash
   [command] --version
   ```

   You should see: `[Project Name] vX.X.X`

### macOS

[Installation steps for macOS]

### Linux

[Installation steps for Linux]

## Docker Installation (Optional)

For containerized deployment:

```bash
docker pull [image]
docker run -d -p [port]:[port] [image]
```

## Verify Installation

Test that everything works:

```bash
[test command]
```

Expected output:
```
[sample output]
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Get up and running in 5 minutes
- [Configuration](../reference/configuration.md) - Customize your setup

## Troubleshooting

**Problem**: [Common installation issue]
**Solution**: [How to fix]
```

### Template: Quick Start

```markdown
# Quick Start

Get started with [Project Name] in under 5 minutes.

## What You'll Build

[Brief description of what the user will accomplish]

## Step 1: [First Step]

[Clear instruction]

```bash
[command or code]
```

**What this does**: [Explanation]

## Step 2: [Second Step]

[Continue with clear steps]

## Step 3: [Third Step]

[Keep it minimal - only essential steps]

## You Did It!

You've successfully [accomplished task].

**What you learned**:
- [Key concept 1]
- [Key concept 2]

## Next Steps

Now that you know the basics:

- **[Common task]**: Learn how to [link to guide]
- **[Another task]**: Discover how to [link to guide]
- **Explore all features**: Check out the [complete reference](../reference/)
```

### Template: How-To Guide

```markdown
# How to [Accomplish Specific Task]

**Time required**: [X minutes]
**Prerequisites**: [What user needs to know/have first]

## Overview

[One paragraph explaining what this guide accomplishes and when you'd use it]

## Steps

### 1. [First Action]

[Clear instruction with context]

```bash
[command or code sample]
```

**Expected result**: [What user should see]

### 2. [Second Action]

[Continue with clear, numbered steps]

**Tip**: [Helpful note]

**Warning**: [Important caution if applicable]

### 3. [Final Action]

[Complete the task]

## Verification

To confirm everything worked:

```bash
[verification command]
```

You should see: [expected output]

## Troubleshooting

**Problem**: [Common issue with this task]
**Solution**: [How to resolve]

## Related Guides

- [Related task 1]
- [Related task 2]
```

### Template: Configuration Reference

```markdown
# Configuration Reference

Complete reference for all [Project Name] configuration options.

## Configuration File

[Project Name] looks for configuration in:

- **Linux/macOS**: `~/.config/[project]/config.json`
- **Windows**: `%APPDATA%\[project]\config.json`

## Configuration Format

```json
{
  "option1": "value",
  "option2": 123,
  "nested": {
    "suboption": true
  }
}
```

## Options

### `option1`

- **Type**: `string`
- **Default**: `"default-value"`
- **Required**: No

[Description of what this option does]

**Example**:
```json
"option1": "custom-value"
```

**Valid values**:
- `"value1"`: [What this means]
- `"value2"`: [What this means]

### `option2`

[Continue for all options...]

## Environment Variables

Configuration can also be set via environment variables:

| Environment Variable | Config Option | Example |
|---------------------|---------------|---------|
| `PROJECT_OPTION1` | `option1` | `export PROJECT_OPTION1=value` |

## Examples

### Minimal Configuration

```json
{
  "option1": "value"
}
```

### Production Configuration

```json
{
  "option1": "production-value",
  "option2": 1000,
  "nested": {
    "suboption": false
  }
}
```

[Explain this configuration choice]
```

### Template: API Reference (User-Focused)

```markdown
# API Reference

## Authentication

All API requests require authentication using an API key.

**Getting your API key**: [How to obtain]

**Using your API key**:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.example.com/endpoint
```

## Rate Limits

- **Free tier**: 100 requests/hour
- **Pro tier**: 1000 requests/hour

When you exceed the limit, you'll receive a `429 Too Many Requests` response.

## Endpoints

### Create a Resource

`POST /api/resources`

Creates a new resource.

**Request Body**:

```json
{
  "name": "Resource Name",
  "type": "resource-type",
  "options": {
    "enabled": true
  }
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | The resource name (max 255 chars) |
| `type` | string | Yes | One of: `type1`, `type2` |
| `options` | object | No | Configuration options |

**Response** (201 Created):

```json
{
  "id": "res_abc123",
  "name": "Resource Name",
  "type": "resource-type",
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Example**:

```bash
curl -X POST https://api.example.com/api/resources \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Resource",
    "type": "type1"
  }'
```

**Errors**:

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 400 | Invalid request body | Check required fields |
| 401 | Missing/invalid API key | Verify your API key |
| 409 | Resource already exists | Use a different name |

[Continue for all endpoints...]
```

### Template: CLI Reference

```markdown
# CLI Reference

Complete reference for all [Project Name] commands.

## Global Options

These options work with all commands:

- `--help, -h`: Show help
- `--version, -v`: Show version
- `--config <file>`: Use custom config file
- `--verbose`: Enable detailed output

## Commands

### `project init`

Initialize a new project.

**Usage**:
```bash
project init [options] [directory]
```

**Arguments**:

- `directory`: Target directory (default: current directory)

**Options**:

- `--template <name>`: Use a template (`basic`, `advanced`, `minimal`)
- `--name <name>`: Project name
- `--force`: Overwrite existing files

**Examples**:

```bash
# Initialize in current directory
project init

# Initialize with template
project init --template advanced my-project

# Force overwrite
project init --force
```

**Output**:

```
✓ Created project structure
✓ Installed dependencies
✓ Initialized configuration

Project ready! Run 'project start' to begin.
```

[Continue for all commands...]
```

### Template: Troubleshooting

```markdown
# Troubleshooting

Common problems and their solutions.

## Error Messages

### "Error: Connection refused"

**Cause**: The application cannot connect to the required service.

**Solutions**:

1. Verify the service is running:
   ```bash
   [check command]
   ```

2. Check your configuration:
   ```bash
   [config check command]
   ```

3. Ensure the correct port is configured (default: [port])

**Still not working?** [Link to further help]

### "Error: Permission denied"

**Cause**: Insufficient permissions to access a resource.

**Solutions**:

1. **On Linux/macOS**: Run with elevated privileges:
   ```bash
   sudo [command]
   ```

2. **On Windows**: Run Command Prompt as Administrator

3. Check file permissions:
   ```bash
   ls -la [file]
   ```

[Continue for all common errors...]

## FAQ

### How do I [common question]?

[Clear answer with example]

### Why is [feature] not working?

[Troubleshooting steps]

### Can I [user question]?

[Yes/no answer with explanation and example]

[Continue for frequently asked questions...]

## Getting Help

If you're still stuck:

- **GitHub Issues**: [link] - Report bugs or request help
- **Discussions**: [link] - Ask questions and share tips
- **Email**: [support email]
```

### Content Generation Process

For each documentation file:

1. **Determine the purpose**: Tutorial, how-to, reference, or explanation?
2. **Extract relevant code**: Find the features/config/commands to document
3. **Use appropriate template**: Follow the structure above
4. **Write user-focused content**: Follow the writing guidelines
5. **Add examples**: Real code samples with expected output
6. **Cross-reference**: Link to related documentation
7. **Add placeholders**: Mark where screenshots/videos would help

**Placeholder Format**:

```markdown
> **📸 Screenshot needed**: [Description of what screenshot should show]
>
> **Location**: [Where in the UI or workflow this screenshot belongs]

> **🎥 Video tutorial**: [Description of what video should demonstrate]
>
> **Duration**: [Suggested length, e.g., "2-3 minutes"]
```

## Phase 5: Static Site Setup

### MkDocs Material Setup

**When to recommend**: Python projects, users wanting beautiful Material Design, excellent search

**Setup Process**:

1. Create `mkdocs.yml`:

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

2. Create `requirements.txt` for docs:

```txt
mkdocs>=1.5.0
mkdocs-material>=9.4.0
mkdocs-minify-plugin>=0.7.0
```

3. Create deployment instructions in `docs/DEPLOYMENT.md`:

```markdown
# Deploying Documentation

## Local Preview

```bash
# Install dependencies
pip install -r requirements.txt

# Serve locally
mkdocs serve
```

Visit http://127.0.0.1:8000

## Deploy to GitHub Pages

```bash
# Build and deploy
mkdocs gh-deploy
```

This will build the site and push to the `gh-pages` branch.

## Auto-Deploy with GitHub Actions

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: 3.x
      - run: pip install -r requirements.txt
      - run: mkdocs gh-deploy --force
```
```

### Docusaurus Setup

**When to recommend**: React/JavaScript projects, users wanting rich interactivity, versioning support

**Setup Process**:

1. Initialize Docusaurus:

```bash
npx create-docusaurus@latest docs classic
```

2. Customize `docusaurus.config.js`:

```javascript
// @ts-check
const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

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
      algolia: {
        appId: 'YOUR_APP_ID',
        apiKey: 'YOUR_API_KEY',
        indexName: 'YOUR_INDEX_NAME',
      },
    }),
};

module.exports = config;
```

3. Create `sidebars.js`:

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

4. Create deployment instructions:

```markdown
# Deploying Documentation

## Local Development

```bash
cd docs
npm install
npm start
```

Visit http://localhost:3000

## Build

```bash
npm run build
```

Static files generated in `build/`

## Deploy to GitHub Pages

```bash
GIT_USER=[username] npm run deploy
```

## Auto-Deploy with GitHub Actions

Create `.github/workflows/docs-deploy.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]

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
```

### VitePress Setup

**When to recommend**: Vue projects, users wanting simplicity and speed, minimal configuration

**Setup Process**:

1. Initialize VitePress:

```bash
npm init
npm add -D vitepress
npx vitepress init
```

2. Create `.vitepress/config.js`:

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

3. Update `package.json`:

```json
{
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  }
}
```

4. Create deployment instructions:

```markdown
# Deploying Documentation

## Local Development

```bash
npm run docs:dev
```

Visit http://localhost:5173

## Build

```bash
npm run docs:build
```

Static files in `docs/.vitepress/dist`

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

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: npm
      - run: npm ci
      - run: npm run docs:build
      - uses: actions/upload-pages-artifact@v2
        with:
          path: docs/.vitepress/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v2
        id: deployment
```
```

### Plain Markdown (No SSG)

**When to recommend**: Simple projects, users wanting minimal setup, GitHub-only hosting

**Setup Process**:

1. Create documentation structure:

```
docs/
├── README.md                         # Landing page (GitHub shows this)
├── getting-started/
│   ├── README.md
│   ├── installation.md
│   ├── quick-start.md
│   └── first-steps.md
├── guides/
│   ├── README.md
│   └── [guide files]
└── reference/
    ├── README.md
    └── [reference files]
```

2. Create navigation in main `docs/README.md`:

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

## Troubleshooting

- [Common Errors](troubleshooting/common-errors.md)
- [FAQ](troubleshooting/faq.md)

## Getting Help

[How to get support]
```

3. Enable GitHub Pages:
   - Go to repository Settings > Pages
   - Source: Deploy from branch
   - Branch: main, folder: /docs

## Phase 6: Quality Assurance

Before finalizing documentation, perform these checks:

### Completeness Check

```bash
# List all documentation files created
find docs/ -name "*.md" | sort

# Count total words (approximate content volume)
find docs/ -name "*.md" -exec wc -w {} + | tail -1
```

Verify:
- [ ] All major features documented
- [ ] Installation guide present
- [ ] Quick start guide present
- [ ] At least 5 how-to guides
- [ ] Complete reference sections
- [ ] Troubleshooting guide present
- [ ] FAQ with at least 10 questions

### Link Validation

Check for broken internal links:

```bash
# Find all markdown links
grep -r "\[.*\](.*\.md)" docs/

# Check for common link errors
grep -r "\[.*\](.*/)" docs/  # Missing .md extension
grep -r "\[.*\](\.\..*)" docs/  # Relative paths (verify they're correct)
```

### Code Sample Validation

If possible, test code samples:

```bash
# Extract bash code blocks and test
# (Manual process - extract samples and run)

# Check for placeholder text that should be replaced
grep -r "TODO\|FIXME\|XXX\|\[Your.*\]" docs/
```

### Accessibility Check

- [ ] All images have alt text
- [ ] Headings follow hierarchy (no skipping levels)
- [ ] Code blocks have language specified
- [ ] Tables have headers
- [ ] Links have descriptive text (not "click here")

### Content Quality Review

For each major documentation file:

1. **Read the introduction**: Does it clearly state what the reader will learn?
2. **Check structure**: Are sections logically ordered?
3. **Verify examples**: Do they show realistic usage?
4. **Review tone**: Is it helpful and encouraging (not condescending)?
5. **Look for gaps**: Are there unexplained jumps in knowledge?

### Mark Items for Review

Create a `docs/TODO.md` file listing:

```markdown
# Documentation TODOs

Items marked for manual review:

## Screenshots Needed

- [ ] Getting Started > Installation: Screenshot of installer window
- [ ] Quick Start: Screenshot of successful first run
- [ ] [etc.]

## Video Tutorials

- [ ] Complete walkthrough (5-10 minutes)
- [ ] [Feature] tutorial (2-3 minutes)

## Content Review

- [ ] Verify all API endpoint examples are correct
- [ ] Test all CLI command examples
- [ ] Update configuration defaults if they changed

## Enhancements

- [ ] Add diagram explaining [concept]
- [ ] Expand troubleshooting section with more errors
- [ ] Add integration guide for [popular tool]

## Generated Content Confidence

Mark each section with confidence level:

- ✅ High confidence (verified against code)
- ⚠️ Medium confidence (inferred from code patterns)
- ❓ Low confidence (needs manual verification)

### High Confidence
- Installation requirements
- Configuration options
- [etc.]

### Medium Confidence
- User workflow descriptions
- Error message solutions
- [etc.]

### Low Confidence
- [List anything that needs verification]
```

## Phase 7: Handoff

### Generate Summary Report

Create a final report for the user in `docs/GENERATION-REPORT.md`:

```markdown
# Documentation Generation Report

**Generated on**: [Date]
**Project analyzed**: [Project Name]
**Technology stack**: [Detected stack]
**Static site generator**: [Chosen SSG]

## What Was Generated

### Documentation Structure

- **Total files**: [X]
- **Total words**: ~[X]
- **Estimated reading time**: [X] minutes

### Sections Created

- ✅ Getting Started (3 guides)
- ✅ How-To Guides ([X] guides)
- ✅ Reference Documentation ([X] pages)
- ✅ Explanation ([X] pages)
- ✅ Troubleshooting (errors + FAQ)

### Features Documented

- [Feature 1]
- [Feature 2]
- [etc.]

## Confidence Level

- **High confidence**: [X]% (verified against code)
- **Medium confidence**: [X]% (inferred from patterns)
- **Needs review**: [X]% (marked with TODO)

See `TODO.md` for items requiring manual review.

## Next Steps

### 1. Preview Locally

```bash
[Preview command for chosen SSG]
```

Visit [local URL]

### 2. Review Generated Content

Priority review areas:
1. **Getting Started > Quick Start**: Ensure examples work
2. **Reference > Configuration**: Verify all defaults are correct
3. **Troubleshooting**: Add any missing common errors

### 3. Add Visual Content

The documentation includes [X] placeholders for:
- Screenshots (marked with 📸)
- Video tutorials (marked with 🎥)
- Diagrams (marked with 📊)

Use tools like:
- **Screenshots**: Snagit, ShareX, macOS Screenshot
- **Videos**: Loom, OBS Studio
- **Diagrams**: Excalidraw, Draw.io, Mermaid

### 4. Customize Branding

Update these files with your branding:
- [ ] Logo: `[path to logo]`
- [ ] Favicon: `[path to favicon]`
- [ ] Colors: `[path to theme config]`
- [ ] Footer links: `[path to config]`

### 5. Deploy

**Option 1: Manual Deploy**
```bash
[Deploy command]
```

**Option 2: Auto-Deploy**
- GitHub Actions workflow created: `.github/workflows/[workflow].yml`
- Push to main branch to trigger deployment

### 6. Maintain Documentation

As your code evolves:

- **Re-run this skill**: Regenerate docs to capture new features
- **Incremental updates**: Edit individual pages as features change
- **Version docs**: For major releases, consider versioning
  - Docusaurus: Built-in versioning support
  - MkDocs: Use mike plugin
  - VitePress: Manual version management

## Support

Generated documentation issues? Check:

1. **Missing features**: Re-run skill after adding code
2. **Incorrect info**: Edit individual .md files
3. **Broken links**: Run link checker
4. **Build errors**: Check SSG-specific troubleshooting

## Feedback

This documentation was generated by the `user-manual-generator` skill.
To improve future generations, note what worked well and what needed heavy editing.
```

### Final User Message

After completing all phases, provide this message to the user:

```
✅ Documentation generation complete!

📊 **Summary**:
- Generated [X] documentation pages (~[X] words)
- Set up [SSG name] static site
- Ready for deployment to [deployment target]

🚀 **Quick Start**:

1. Preview locally:
   ```bash
   [preview command]
   ```

2. Review the generation report:
   `docs/GENERATION-REPORT.md`

3. Check items needing manual work:
   `docs/TODO.md`

4. Deploy when ready:
   ```bash
   [deploy command]
   ```

📝 **Next Steps**:

- **Add screenshots**: [X] placeholders marked with 📸
- **Review accuracy**: Check sections marked ⚠️ in TODO.md
- **Customize branding**: Update logo, colors, footer
- **Test examples**: Verify all code samples work
- **Deploy**: Push to GitHub or run deploy command

⚠️ **Important**: This is AI-generated documentation. Please review:
- All code examples (verify they execute correctly)
- Configuration defaults (ensure they match your app)
- Troubleshooting solutions (test they resolve issues)

The documentation provides a solid foundation - expect to spend ~20% effort on refinement vs 80% generated.

📚 **Documentation is live at** (after deployment):
[Deployment URL]

Need help? Check the generation report or re-run this skill with adjusted settings.
```

## Advanced Features

### Multi-Language Documentation

If the project needs documentation in multiple languages:

1. Ask user which languages to support
2. Create language structure:

```
docs/
├── en/
│   ├── getting-started/
│   └── [all sections]
├── es/
│   ├── getting-started/
│   └── [all sections - mark for translation]
└── fr/
    └── [all sections - mark for translation]
```

3. Configure SSG for i18n:
   - **MkDocs**: Use `i18n` plugin
   - **Docusaurus**: Built-in i18n support
   - **VitePress**: Configure locales in config

4. Generate English content, create TODO for translations:

```markdown
> **🌍 Translation needed**: This content is in English.
> Translate to: [Target Language]
```

### Documentation Versioning

For projects with multiple versions:

1. Ask if versioning is needed
2. Set up version management:
   - **Docusaurus**: `npm run docusaurus docs:version X.Y`
   - **MkDocs**: Use `mike` plugin
   - **VitePress**: Manual version directories

3. Document versioning strategy:

```markdown
# Documentation Versioning

Versions maintained:
- **Latest**: Main branch documentation
- **v2.x**: Stable release (recommended)
- **v1.x**: Legacy (security updates only)

To document a new version:
[Instructions for chosen SSG]
```

### API Documentation Integration

If OpenAPI/Swagger specs exist:

1. Detect spec files:

```bash
find . -name "openapi.yaml" -o -name "swagger.json"
```

2. Integrate with SSG:
   - **Docusaurus**: Use `docusaurus-plugin-openapi-docs`
   - **MkDocs**: Use `mkdocs-swagger-ui-tag`
   - **VitePress**: Embed Swagger UI component

3. Generate user-friendly API guides alongside spec:
   - Don't rely solely on auto-generated API docs
   - Create guides showing common API workflows
   - Include authentication examples
   - Show pagination, filtering, error handling

### Interactive Examples

For web applications, include interactive demos:

1. Create `examples/` directory
2. Generate simple HTML demos:

```html
<!-- examples/feature-demo.html -->
<!DOCTYPE html>
<html>
<head>
    <title>[Feature] Demo</title>
</head>
<body>
    <h1>[Feature] Interactive Demo</h1>

    <!-- Simple interactive example -->
    <script>
        // Minimal working example
    </script>

    <p>View source to see implementation.</p>
</body>
</html>
```

3. Link from documentation:

```markdown
> **Try it live**: [Interactive demo](../examples/feature-demo.html)
```

### Video Tutorial Placeholders

When marking video needs, be specific:

```markdown
> **🎥 Video Tutorial: Getting Started (5 minutes)**
>
> **Script outline**:
> 1. Introduction (0:00-0:30): Welcome, what you'll learn
> 2. Installation (0:30-2:00): Show install process on [OS]
> 3. First run (2:00-3:30): Walk through quick start
> 4. Explore UI (3:30-4:30): Tour main features
> 5. Wrap up (4:30-5:00): Next steps, where to learn more
>
> **Required footage**:
> - Screen recording of installation
> - Screen recording of first successful run
> - Cursor highlighting key UI elements
>
> **Recommended tools**:
> - Loom (easy, web-based)
> - OBS Studio (advanced, more control)
```

## Troubleshooting Common Issues

### Skill Execution Problems

**Problem**: Can't detect project type

**Solution**:
- Ask user directly what type of application it is
- Request path to main entry point file
- Generate generic documentation structure, refine later

**Problem**: Missing configuration information

**Solution**:
- Check for `.env.example`, `config.example.js`, etc.
- Search code for default values (`defaultConfig`, `DEFAULT_*` constants)
- Ask user to provide configuration documentation if available

**Problem**: Unclear user workflows

**Solution**:
- Ask user to describe 3 main use cases
- Analyze routing/URL structure for clues
- Check test files for usage patterns

### Content Generation Issues

**Problem**: Hallucinating features that don't exist

**Solution**:
- Mark generated content with confidence levels
- Use TODO markers liberally
- Stick to observable code patterns
- When uncertain, describe what code does rather than inferring intent

**Problem**: Too technical for end users

**Solution**:
- Avoid implementation details
- Focus on "what" and "why", not "how it's coded"
- Use analogies for complex concepts
- Include glossary for necessary technical terms

**Problem**: Examples don't work

**Solution**:
- Extract examples from test files when possible
- Mark auto-generated examples with "⚠️ Verify this example"
- Provide template examples with clear placeholders

### SSG Setup Issues

**Problem**: Build errors with chosen SSG

**Solution**:
- Verify all required files are present
- Check configuration syntax carefully
- Provide fallback to plain Markdown
- Include troubleshooting section in deployment docs

## Best Practices Learned

### Do's

✅ **Start with user research**: Ask questions before generating
✅ **Follow existing patterns**: Match the project's style/tone
✅ **Provide examples**: Every concept needs a code sample
✅ **Link generously**: Connect related topics
✅ **Mark uncertainty**: Better to flag than to mislead
✅ **Test locally**: Verify SSG builds before declaring success
✅ **Plan for maintenance**: Make it easy to regenerate/update

### Don'ts

❌ **Don't guess**: If you can't find it in code, mark it for review
❌ **Don't over-generate**: Better 10 great pages than 50 mediocre ones
❌ **Don't ignore existing docs**: If README has good content, incorporate it
❌ **Don't forget visuals**: Text-only docs are harder to follow
❌ **Don't skip testing**: Broken examples destroy credibility
❌ **Don't make it perfect**: 80% generated, 20% manual refinement is the goal

## Appendix: Technology-Specific Patterns

### React Applications

**Key files to analyze**:
- `src/App.js` or `src/App.tsx`: Main app structure
- `src/pages/` or `pages/`: Page components
- `src/components/`: Reusable components
- `src/hooks/`: Custom hooks (document for advanced users)

**What to document**:
- Component props (if exposed to users via config)
- Routing structure (maps to user navigation)
- Form validations (user needs to know constraints)
- State management (if users interact with it)

**Don't document**:
- Internal component implementation
- Redux/Zustand internals (unless user-configurable)
- Build configuration (developer docs)

### Express/Node.js APIs

**Key files to analyze**:
- `routes/` or `src/routes/`: API endpoints
- `middleware/`: Auth, rate limiting (document for users)
- `models/`: Data structures (for reference)

**What to document**:
- All endpoints with request/response examples
- Authentication flow from user perspective
- Rate limits and quotas
- Error responses with solutions
- Webhook endpoints (if any)

### Python Flask/Django

**Key files to analyze**:
- `views.py` or `routes.py`: Endpoints
- `urls.py`: URL patterns
- `models.py`: Data models (for reference)
- `forms.py`: Form validations

**What to document**:
- URL routes with examples
- Form fields and validation rules
- Admin interface usage (if applicable)
- Management commands (CLI)

### CLI Tools (Python, Node.js, Go)

**Key files to analyze**:
- Argument parsers: `argparse`, `commander`, `cobra`
- Command definitions
- Configuration file loading

**What to document**:
- Every command with full examples
- All options and flags
- Configuration file format
- Common workflows (combining commands)

### Desktop Applications (Electron)

**Key files to analyze**:
- `main.js`: Main process (window management, menus)
- `preload.js`: IPC communication
- `src/`: Renderer process (UI)
- Menu definitions

**What to document**:
- Installation per platform
- UI navigation
- Keyboard shortcuts
- Settings/preferences
- File operations (open, save, export)
- Auto-update process (if applicable)

## Conclusion

This skill automates the tedious work of documentation generation while maintaining quality and user focus. The key is balancing automation (structure, templates, content extraction) with human judgment (tone, examples, verification).

**Expected outcome**:
- 70-80% time saved vs manual documentation
- Deployment-ready site in minutes
- Solid foundation requiring 20% manual refinement
- Maintainable docs that evolve with code

**Success criteria**:
- Non-technical users can complete tasks using docs
- All major features covered
- Zero build errors
- Passes basic accessibility checks
- Deployable to chosen hosting platform

Use this skill as a starting point. Every project is unique—adjust the templates, add sections, and refine the content to match your users' needs.
