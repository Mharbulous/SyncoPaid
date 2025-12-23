# Phase 1: Discovery & Requirements Gathering

## Initial Questions

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

## Codebase Discovery

Use the following tools to understand the project structure:

### 1. Identify Project Type

```bash
# Check for package managers and frameworks
ls -la | grep -E "(package.json|requirements.txt|Gemfile|go.mod|pom.xml|Cargo.toml|composer.json)"

# Check for common config files
ls -la | grep -E "(vite.config|webpack.config|tsconfig.json|next.config|nuxt.config|angular.json)"
```

### 2. Map Project Structure

Use `Glob` to find key files:
- Entry points: `**/*main*.{js,ts,py,go,java}`, `**/index.{js,ts,html}`, `**/__main__.py`
- Routes/navigation: `**/routes/**/*.{js,ts}`, `**/pages/**/*.{js,ts,tsx,jsx}`, `**/urls.py`
- CLI definitions: `**/cli.{js,ts,py}`, `**/commands/**/*.{js,ts,py}`
- Configuration: `**/config/*.{js,ts,py,json,yaml,toml}`, `.env.example`
- Components: `**/components/**/*.{jsx,tsx,vue}`, `**/views/**/*.py`

### 3. Detect Technology Stack

Based on files found, determine:
- **Frontend framework**: React, Vue, Angular, Svelte, vanilla JS
- **Backend framework**: Express, FastAPI, Django, Flask, Spring Boot, Rails
- **Language**: JavaScript/TypeScript, Python, Java, Go, Ruby, PHP
- **Build tools**: Vite, Webpack, Rollup, Parcel
- **Package manager**: npm, yarn, pnpm, pip, poetry, maven, gradle

## Next Phase

Once discovery is complete, proceed to **Phase 2: Feature Extraction** by reading `phases/02-feature-extraction.md`.
