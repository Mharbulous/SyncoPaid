# Phase 3: Documentation Structure Planning

Based on the Diataxis framework, organize extracted information into four documentation types plus troubleshooting.

## Diataxis Framework Overview

| Type | Orientation | Purpose |
|------|-------------|---------|
| Tutorials | Learning | Hand-holding for new users |
| How-To Guides | Task | Problem-solving focused |
| Reference | Information | Precise, comprehensive |
| Explanation | Understanding | Why things work |

## 1. Tutorials (Learning-Oriented)

**Getting Started**: First-time user experience
- Installation/setup
- Quick start (minimal viable usage)
- First meaningful task completion
- Understanding basic concepts

**Target**: New users who need hand-holding

## 2. How-To Guides (Task-Oriented)

**Common Tasks**: Problem-solving focused
- Each guide solves one specific problem
- Step-by-step instructions
- Assumes basic knowledge
- Shows different ways to accomplish goals

**Examples by application type:**
- **Web app**: "How to reset your password", "How to export data", "How to customize your dashboard"
- **API**: "How to authenticate requests", "How to handle rate limits", "How to paginate results"
- **CLI**: "How to process batch files", "How to configure output format", "How to automate workflows"

## 3. Reference (Information-Oriented)

**Technical Specifications**: Precise, comprehensive
- Configuration reference (all settings with defaults)
- API reference (all endpoints with parameters)
- CLI reference (all commands with options)
- Error codes and meanings
- Data formats and schemas

**Target**: Users who know what they're looking for

## 4. Explanation (Understanding-Oriented)

**Concepts and Architecture**: Why things work the way they do
- Key concepts explained
- Architecture overview (from user perspective, not developer)
- Design decisions that affect usage
- Limitations and constraints
- Security model

**Target**: Users who want deeper understanding

## 5. Troubleshooting

**Common Problems**: Reactive help
- Error messages with solutions
- FAQs from issues/discussions
- Performance problems
- Compatibility issues

## Documentation Hierarchy

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

## Adapting Structure

### For APIs
- Emphasize reference section with all endpoints
- Include authentication guide prominently
- Add rate limiting and pagination guides

### For CLI Tools
- Emphasize command reference
- Include workflow examples combining commands
- Add scripting/automation guides

### For Web Apps
- Emphasize user task guides
- Include UI navigation help
- Add screenshots/video placeholders

### For Desktop Apps
- Include installation per platform
- Document keyboard shortcuts
- Cover settings/preferences in detail

## Next Phase

Once structure is planned, proceed to **Phase 4: Content Generation** by reading `phases/04-content-generation.md`.
