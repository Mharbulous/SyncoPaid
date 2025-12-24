# User Manual Generator Skill

Automatically generate comprehensive, deployment-ready user documentation from your application codebase using Claude Code.

## What This Skill Does

The User Manual Generator analyzes your codebase and creates production-ready user documentation following industry best practices:

- **Intelligent Analysis**: Extracts user-facing features from code, routes, config files, and CLI definitions
- **Diataxis Framework**: Organizes content into tutorials, how-to guides, reference, and explanations
- **Multiple Formats**: Supports MkDocs Material, Docusaurus, VitePress, or plain Markdown
- **Deployment-Ready**: Generates complete static sites with GitHub Pages/Netlify/Vercel configuration
- **User-Focused**: Creates documentation for end users, not just developers

## Installation

### Prerequisites

- Windows 11 with VS Code
- Claude Code CLI or Claude Code web interface
- Node.js 18+ (for Docusaurus/VitePress) or Python 3.8+ (for MkDocs)
- Git for deployment

### Install the Skill

1. **Clone or copy this skill to your skills directory**:

   ```bash
   # On Windows (Claude Code default location)
   mkdir -p /mnt/skills/user
   cp -r user-manual-generator /mnt/skills/user/
   ```

2. **Verify installation**:

   ```bash
   # List available skills
   ls /mnt/skills/user/
   ```

   You should see `user-manual-generator` in the list.

3. **The skill is now ready to use** - no additional dependencies required.

## Usage

### Quick Start

1. **Open your project in VS Code**

2. **Invoke the skill in Claude Code**:

   Type in Claude Code:
   ```
   Use the user-manual-generator skill to create documentation for this project
   ```

3. **Answer the configuration questions**:
   - Application type (web app, API, CLI, desktop)
   - Target audience (end users, developers, admins)
   - Static site generator preference
   - Deployment target
   - Documentation depth

4. **Wait for generation** (typically 2-5 minutes):
   - Code analysis
   - Documentation generation
   - Static site setup
   - Quality checks

5. **Review the output**:
   - `docs/` - All generated documentation
   - `docs/GENERATION-REPORT.md` - What was created
   - `docs/TODO.md` - Items needing manual review

6. **Preview locally**:

   ```bash
   # MkDocs Material
   pip install -r requirements.txt
   mkdocs serve

   # Docusaurus
   cd docs && npm install && npm start

   # VitePress
   npm run docs:dev
   ```

7. **Deploy**:

   Follow deployment instructions in `docs/DEPLOYMENT.md`

### Advanced Usage

#### Regenerate Documentation

As your code evolves, regenerate docs to capture changes:

```
Regenerate the user documentation with comprehensive depth
```

The skill will update existing docs while preserving manual edits (marked sections).

#### Customize for Specific Audiences

```
Generate API documentation focused on developer integration, using Docusaurus
```

#### Generate Specific Sections

```
Add a troubleshooting guide based on GitHub issues
```

#### Multi-Language Documentation

```
Set up documentation structure for English, Spanish, and French
```

## What Gets Generated

### Documentation Structure

```
docs/
├── index.md                          # Landing page
├── getting-started/
│   ├── installation.md               # Platform-specific setup
│   ├── quick-start.md                # 5-minute first run
│   └── first-steps.md                # Complete first task
├── guides/
│   ├── common-tasks.md               # Frequent operations
│   ├── advanced-usage.md             # Power user features
│   ├── integrations.md               # Connect with other tools
│   └── workflows.md                  # End-to-end scenarios
├── reference/
│   ├── configuration.md              # All config options
│   ├── api-reference.md              # (APIs) All endpoints
│   ├── cli-reference.md              # (CLIs) All commands
│   └── error-codes.md                # Error reference
├── explanation/
│   ├── architecture.md               # How it works
│   ├── concepts.md                   # Key ideas
│   └── limitations.md                # Constraints
└── troubleshooting/
    ├── common-errors.md              # Error solutions
    └── faq.md                        # Frequently asked questions
```

### Static Site Configuration

Complete setup for your chosen generator:

- **MkDocs Material**: `mkdocs.yml` + Material theme configuration
- **Docusaurus**: Full Docusaurus site with navigation, search, versioning
- **VitePress**: Minimal, fast Vue-based docs site
- **Plain Markdown**: GitHub-friendly markdown with navigation

### Deployment Files

- GitHub Actions workflows for auto-deployment
- Netlify/Vercel configuration files
- Deployment instructions and troubleshooting

## Configuration Options

The skill asks these questions on invocation:

### 1. Application Type
- Web application (React, Vue, Angular, etc.)
- REST/GraphQL API
- CLI tool
- Desktop application (Electron, etc.)
- Full-stack application

**Why it matters**: Determines which code patterns to look for and how to structure docs.

### 2. Target Audience
- End users (non-technical)
- API consumers (developers)
- System administrators
- Mixed audience

**Why it matters**: Affects language complexity and focus areas.

### 3. Static Site Generator
- **MkDocs Material**: Beautiful Material Design, Python-based, excellent search
- **Docusaurus**: React-based, rich features, versioning support, used by Meta
- **VitePress**: Vue-based, fast, minimal setup
- **Plain Markdown**: No generator, GitHub Pages compatible

**Why it matters**: Determines deployment complexity and available features.

### 4. Deployment Target
- GitHub Pages (free, easy)
- Netlify (free tier, advanced features)
- Vercel (free tier, Next.js optimized)
- Self-hosted

**Why it matters**: Configures deployment scripts and workflows.

### 5. Documentation Depth
- **Quick start only**: Minimal docs, fast generation (5-10 pages)
- **Standard**: Getting started + common tasks + reference (15-25 pages)
- **Comprehensive**: Full coverage with examples and explanations (30+ pages)

**Why it matters**: Balances completeness vs time investment.

## Output Quality

### What You Can Expect

✅ **70-80% time savings** vs manual documentation
✅ **Deployment-ready** static site (zero build errors)
✅ **Comprehensive coverage** of user-facing features
✅ **Best practices** following Diataxis framework
✅ **Accessible** following WCAG guidelines
✅ **Maintainable** with clear TODO markers

### What Needs Manual Work (~20%)

📸 **Screenshots**: Placeholders marked with 📸
🎥 **Video tutorials**: Scripts provided, recording needed
⚠️ **Verification**: Code examples tested but should be validated
🎨 **Branding**: Logo, colors, footer customization
🌍 **Translation**: English content generated, other languages need translation

### Confidence Levels

Generated content is marked with confidence:

- ✅ **High**: Extracted directly from code (config defaults, API routes, CLI commands)
- ⚠️ **Medium**: Inferred from patterns (workflows, use cases)
- ❓ **Low**: Needs verification (error solutions, advanced features)

Check `docs/TODO.md` for items flagged for review.

## Examples

### Example 1: React Web Application

```
User: "Generate user documentation for this React app"

Skill detects:
- React with React Router
- 15 routes across 3 main sections
- Authentication with JWT
- REST API integration

Generates:
- Installation guide (npm install + env setup)
- Quick start (first login + navigation tour)
- 8 how-to guides (user management, data export, etc.)
- Full UI navigation reference
- Troubleshooting guide with auth errors

Output: 23 pages, MkDocs Material site, GitHub Actions workflow
```

### Example 2: Express.js API

```
User: "Create API documentation for developers integrating our service"

Skill detects:
- Express with 42 endpoints
- JWT authentication
- Rate limiting (100 req/hr free tier)
- OpenAPI spec available

Generates:
- Getting started (API key creation + first request)
- Authentication guide (OAuth flow explained)
- Complete API reference (all endpoints with examples)
- Rate limiting and pagination guides
- Webhook integration guide
- Error code reference

Output: 18 pages, Docusaurus site with API playground, Netlify deploy
```

### Example 3: Python CLI Tool

```
User: "Generate docs for this CLI app using MkDocs"

Skill detects:
- Click-based CLI with 12 commands
- Config file support (YAML)
- Batch processing capabilities

Generates:
- Installation (pip install + verify)
- Quick start (first command walkthrough)
- Complete command reference (all 12 commands)
- Configuration guide (all YAML options)
- Workflow guides (batch processing, automation)
- Troubleshooting (file permissions, encoding)

Output: 15 pages, MkDocs Material, GitHub Pages ready
```

## Troubleshooting

### Skill won't activate

**Problem**: Skill command not recognized

**Solution**:
1. Verify skill location: `/mnt/skills/user/user-manual-generator/SKILL.md`
2. Try explicit invocation: "Load the user-manual-generator skill from /mnt/skills/user/"
3. Restart Claude Code session

### Can't detect project type

**Problem**: Skill can't determine application type

**Solution**:
1. Provide explicit information: "This is a React web application"
2. Point to main entry file: "The main file is src/index.tsx"
3. Describe the project briefly

### Generated docs have errors

**Problem**: Code examples don't work or information is incorrect

**Solution**:
1. Check `docs/TODO.md` for flagged items
2. Review sections marked ⚠️ (medium confidence)
3. Verify examples against actual code
4. Edit individual .md files to correct

### Build errors with static site generator

**Problem**: `mkdocs build` or `npm run build` fails

**Solution**:
1. Check generator-specific errors in terminal
2. Verify all required files present
3. Validate YAML/JSON configuration syntax
4. See `docs/DEPLOYMENT.md` troubleshooting section
5. Fallback: Use plain Markdown if SSG issues persist

### Missing features in documentation

**Problem**: Important features not documented

**Solution**:
1. Check if features are user-facing (skill focuses on user docs)
2. Regenerate with "comprehensive" depth
3. Manually add missing sections
4. Provide example: "Add documentation for [feature] based on [file path]"

### Documentation too technical

**Problem**: Content written for developers, not end users

**Solution**:
1. Specify audience clearly: "Target audience is non-technical users"
2. Request rewrite: "Simplify the [section] for non-technical readers"
3. Manually edit to reduce jargon

## Best Practices

### Before Running the Skill

1. **Clean up obvious issues**: Fix broken imports, remove dead code
2. **Update README**: Ensure basic project info is current
3. **Have example usage**: Test files or examples directory helps
4. **Define target audience**: Know who will use the docs

### After Generation

1. **Review immediately**: Check `GENERATION-REPORT.md` first
2. **Test examples**: Verify code samples actually work
3. **Add screenshots**: Use placeholders as guide
4. **Preview locally**: See docs as users will
5. **Get feedback**: Share with a user from target audience

### Maintaining Documentation

1. **Regenerate periodically**: After major feature additions
2. **Preserve manual edits**: Skill marks sections to avoid overwriting
3. **Version documentation**: For major releases, snapshot docs
4. **Monitor issues**: GitHub issues often reveal doc gaps

## Integration with Development Workflow

### Git Hooks

Auto-check docs when code changes:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Warn if code changed but docs didn't
if git diff --cached --name-only | grep -q "^src/"; then
  if ! git diff --cached --name-only | grep -q "^docs/"; then
    echo "⚠️  Code changed but docs didn't. Consider updating documentation."
  fi
fi
```

### CI/CD Integration

Auto-deploy docs on merge:

```yaml
# .github/workflows/docs-deploy.yml
name: Deploy Docs
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy docs
        run: |
          # [Deployment commands based on chosen SSG]
```

### Documentation as Code

- **Store in repo**: `docs/` committed alongside code
- **Review in PRs**: Require doc updates for feature PRs
- **Version together**: Docs version matches code version
- **Test in CI**: Build docs in CI to catch errors early

## Comparison with Other Approaches

| Approach | Time | Quality | Maintenance | User-Focused |
|----------|------|---------|-------------|--------------|
| **Manual writing** | High | Excellent | Hard | Yes |
| **Code comments → docs** | Low | Poor | Easy | No |
| **API schema generators** | Low | Medium | Easy | No (API only) |
| **This skill** | **Low** | **Good** | **Medium** | **Yes** |

**When to use this skill**:
- Need user documentation quickly
- Want deployment-ready site
- Prefer 80/20 approach (80% generated, 20% refinement)

**When NOT to use this skill**:
- Need perfect, publication-quality docs (write manually)
- Only need API reference (use OpenAPI generators)
- Tiny project (just write a README)

## Roadmap

Planned improvements for future versions:

- **Screenshot automation**: Integrate Playwright for auto-screenshots
- **Video script generation**: Create detailed video tutorial scripts
- **Diff-based updates**: Only regenerate changed sections
- **Custom templates**: User-provided templates for specific industries
- **AI-assisted review**: Suggest improvements to generated content
- **Metrics dashboard**: Track doc completeness and quality
- **Multi-repo support**: Generate unified docs for microservices

## Contributing

This skill is part of the Claude Code skills ecosystem. To improve it:

1. **Report issues**: Note what worked poorly or was confusing
2. **Share examples**: Provide example projects where it excelled/failed
3. **Suggest templates**: Better templates for specific app types
4. **Improve patterns**: Code patterns that should be recognized

## License

This skill is provided as-is for use with Claude Code.

## Credits

Created for the Claude Code skills repository.

**Frameworks and tools**:
- [Diataxis](https://diataxis.fr/) - Documentation framework
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [Docusaurus](https://docusaurus.io/)
- [VitePress](https://vitepress.dev/)

## Support

For issues with:
- **The skill itself**: Check troubleshooting section above
- **Generated content**: Review and edit .md files directly
- **Static site generators**: See SSG-specific documentation
- **Claude Code**: Visit https://code.claude.com/docs

---

**Ready to generate documentation?**

Open your project in Claude Code and type:
```
Use the user-manual-generator skill to create documentation
```
