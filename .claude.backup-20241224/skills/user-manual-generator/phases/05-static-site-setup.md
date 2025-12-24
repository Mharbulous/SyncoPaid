# Phase 5: Static Site Setup

Set up the static site generator based on user's choice from Phase 1.

## SSG Selection Guide

| SSG | Best For | Key Features |
|-----|----------|--------------|
| MkDocs Material | Python projects, Material Design lovers | Beautiful design, excellent search |
| Docusaurus | React/JS projects, versioning needs | Rich interactivity, built-in versioning |
| VitePress | Vue projects, simplicity | Fast, lightweight, minimal config |
| Plain Markdown | Simple projects, GitHub-only hosting | Zero build, GitHub renders natively |

## Configuration Files

Load the appropriate configuration from `ssg/` directory:

| User's Choice | Configuration File |
|--------------|-------------------|
| MkDocs Material | `ssg/mkdocs.md` |
| Docusaurus | `ssg/docusaurus.md` |
| VitePress | `ssg/vitepress.md` |
| Plain Markdown | `ssg/plain-markdown.md` |

## Common Setup Steps

Regardless of SSG choice:

### 1. Create Documentation Directory

```bash
mkdir -p docs/{getting-started,guides,reference,explanation,troubleshooting}
```

### 2. Add Documentation Files

Move generated content into the structure:

```
docs/
├── index.md
├── getting-started/
│   ├── installation.md
│   ├── quick-start.md
│   └── first-steps.md
├── guides/
│   └── [how-to guides]
├── reference/
│   └── [reference docs]
├── explanation/
│   └── [conceptual docs]
└── troubleshooting/
    ├── common-errors.md
    └── faq.md
```

### 3. Configure Navigation

Each SSG has its own navigation configuration format. Follow the specific SSG's configuration file.

### 4. Test Locally

Before deploying, always test locally:

| SSG | Local Preview Command |
|-----|----------------------|
| MkDocs | `mkdocs serve` |
| Docusaurus | `npm start` |
| VitePress | `npm run docs:dev` |
| Plain Markdown | Open in browser/VS Code preview |

## Deployment Targets

### GitHub Pages

All SSGs support GitHub Pages deployment:
- Enable in repository Settings > Pages
- Use GitHub Actions for automatic deployment
- Specific workflow files in each SSG config

### Netlify

1. Connect repository to Netlify
2. Set build command:
   - MkDocs: `mkdocs build`
   - Docusaurus: `npm run build`
   - VitePress: `npm run docs:build`
3. Set publish directory:
   - MkDocs: `site`
   - Docusaurus: `build`
   - VitePress: `docs/.vitepress/dist`

### Vercel

Similar to Netlify - connect repo and configure build settings.

## Next Phase

Once static site is set up, proceed to **Phase 6: Quality Assurance** by reading `phases/06-quality-assurance.md`.
