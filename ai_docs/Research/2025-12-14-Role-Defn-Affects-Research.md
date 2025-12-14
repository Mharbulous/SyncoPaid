# How CLAUDE.md Role Definition Affects Claude Code Agent Behavior

**Role prompting in CLAUDE.md has limited impact on objective task performance but significantly affects delegation behavior through properly crafted subagent descriptions and explicit orchestration instructions.** Research shows persona definitions account for less than 10% of variance in task outcomes, yet community experience demonstrates that strategic CLAUDE.md configuration—particularly action-oriented subagent descriptions and explicit delegation reminders—measurably improves Claude Code's propensity to use agents and skills. The key insight: context engineering and clear task boundaries matter more than personality definitions.

## Orchestrator patterns exist but face architectural limits

The Claude Code community has developed sophisticated orchestrator patterns in CLAUDE.md, though they work within significant constraints. The most common approach involves defining the main agent as a coordinator that delegates to specialized subagents in `.claude/agents/`. Repositories like **VoltAgent/awesome-claude-code-subagents** (5.6k stars) and **lst97/claude-code-sub-agents** provide production-ready examples featuring "agent-organizer" patterns that perform intelligent project analysis and strategic team assembly.

A critical limitation undermines hierarchical orchestration: **subagents cannot spawn other subagents**. GitHub Issue #5528 documents users finding that despite configuring `tools: Read, Write, Edit, Task` in subagent definitions, the Task tool remains unavailable. This architectural constraint means true multi-level delegation hierarchies are impossible—only single-level orchestration works natively.

Community workarounds have emerged. The most effective is using Claude's built-in `Task(...)` feature to spawn clones of the general agent rather than specialized subagents. Developer Shrivu Shankar explains: "Put all key context in CLAUDE.md, then let the main agent decide when and how to delegate work to copies of itself. This gives all the context-saving benefits without the drawbacks of custom subagents gatekeeping context."

For teams that need specialized agents, the **disler/claude-code-hooks-mastery** repository (1.8k stars) provides the definitive meta-agent pattern—an agent that generates other agent configurations:

```markdown
---
name: meta-agent
description: Creates specialized sub-agents from descriptions
tools: Read, Write, Edit, Glob, Grep
---
You are a meta-agent that designs and creates sub-agent configuration files...
```

## Delegation reliability depends on description field optimization

The most impactful factor for delegation reliability is the `description` field in subagent YAML frontmatter—not role definitions in the body text. Claude Code's automatic delegation matches task context to subagent descriptions; vague descriptions cause Claude to skip delegation entirely.

**Bad description**: `"Helps with code"`  
**Good description**: `"Reviews Python code for security vulnerabilities, PEP 8 compliance, and performance issues. Use proactively for all code review requests."`

Developer Pan Xinghan reports: "When I first tried the multi-agent system, Claude wouldn't actively use subagents, so I added reminders in my CLAUDE.md." The pattern that works:

```markdown
## 👥 SUB-AGENT DELEGATION SYSTEM
**CRITICAL: YOU HAVE 12 SPECIALIZED EMPLOYEES AVAILABLE!**
**BE PROACTIVE WITH SUB-AGENTS - delegate before attempting tasks yourself**

- Use @code-reviewer for ALL code quality analysis
- Use @security-auditor for ANY authentication or security changes
- Use @test-specialist for test creation and debugging
```

Several GitHub issues document persistent delegation problems. Issue #6800 requests forcing the main agent into permanent plan mode because "it's very easy for delegation to fail and for the main agent to start taking tasks it shouldn't be taking." Issue #9417 reports the primary agent claiming it cannot use the Task tool despite configuration. The pattern: explicit invocation (`> Use the code-reviewer subagent`) works reliably, while automatic delegation remains inconsistent.

## Research shows role prompting has modest effects on accuracy

Academic research reveals nuanced findings about role prompting effectiveness. A peer-reviewed ACL 2024 study found that persona variables account for **less than 10% of variance** in task annotations. A large-scale study testing 162 personas across 4 LLM families concluded: "Adding personas in system prompts does not improve model performance across a range of questions compared to the control setting."

The "Jekyll & Hyde" paper (arXiv 2408.08631) showed personas can both improve and degrade reasoning—performance is "extremely sensitive to assigned prompts." Interestingly, LLM-generated personas outperform human-written ones. The recommended approach: ensemble results from both persona-based and neutral prompts, then select the better output.

For open-ended tasks like advice-giving, brainstorming, and creative writing, auto-generated expert personas do outperform minimal prompts. But for multiple-choice and closed-ended tasks, there is "little-to-no advantage" to persona prompting.

**Anthropic's own research** emphasizes context engineering over role definition. Their June 2025 paper on multi-agent research systems found that a Claude Opus 4 lead with Sonnet 4 subagents outperformed single-agent systems by **90.2%**—but token usage alone explained 80% of performance variance. Extended thinking mode improved instruction-following more than persona definitions. The critical guidance: prompts should be at the "right altitude"—specific enough to guide behavior, flexible enough to provide strong heuristics.

## Community examples show patterns that work

Several repositories demonstrate effective CLAUDE.md configurations:

**centminmod/my-claude-code-setup** (1.4k stars) provides a complete starter template featuring a memory bank system, 15+ slash commands, and MCP integrations. The approach separates concerns: CLAUDE.md handles high-level context and delegation rules while specialized agents handle domain knowledge.

**vanzan01/claude-code-sub-agent-collective** addresses specific failure modes through what they call a "Hub-and-Spoke Architecture":
- Agents bypassing directives → CLAUDE.md as "behavioral operating system" with prime directives
- Agents stopping mid-task → Test-driven handoff validation
- Agents making up APIs → Context7 integration forces real documentation usage
- Agents losing context → Handoff contracts preserve information

**0ldh/claude-code-agents-orchestra** organizes 47 specialized agents into 10 teams with explicit orchestration via CLAUDE.md: "All agent communication goes through the Task tool, the Tech Lead only creates blueprints (never executes), and Claude manages all execution after your approval."

The **ruvnet/claude-flow** repository offers 25 specialized skills that activate automatically via natural language, providing an alternative to manual delegation patterns.

## Best practices for maximizing instruction-following

Based on official documentation and community experience, effective CLAUDE.md configuration follows these principles:

**Keep it concise** (~150-200 instructions maximum). Research shows LLM instruction-following quality decreases uniformly as instruction count increases. Claude Code's system prompt already contains ~50 instructions, leaving limited budget for user additions.

**Use progressive disclosure** rather than exhaustive upfront detail. Tell Claude how to find information rather than providing everything—this reduces context bloat while maintaining capability.

**Don't use CLAUDE.md as a linter**. Code style guidelines add instructions and degrade performance. Use deterministic linters/formatters instead; consider Stop hooks that run formatters and present errors.

**Optimize the import hierarchy**. CLAUDE.md supports `@filename.md` imports with recursive loading (max 5 hops). Structure files by concern:
```
~/.claude/
├── CLAUDE.md           # Core instructions, delegation rules
├── agents/             # Specialized agent definitions  
└── commands/           # Slash command templates
```

**Pin tools purposefully**. Read-only agents (reviewers) should get `tools: Read, Grep, Glob`. Research agents add `WebFetch, WebSearch`. Code writers need `Read, Write, Edit, Bash, Glob, Grep`. Limiting tools improves focus and security.

**Use explicit effort scaling rules** embedded in prompts:
- Simple fact-finding: 1 agent, 3-10 tool calls
- Direct comparisons: 2-4 subagents, 10-15 calls each  
- Complex research: 10+ subagents with divided responsibilities

## Addressing your specific delegation problem

For the issue of Claude Code not remembering to use agents or skills, the evidence suggests several interventions:

**First, check skill YAML formatting**. Multi-line descriptions in YAML frontmatter break skill discovery—a documented bug. Use single-line descriptions with `# prettier-ignore` if needed. Multiple open issues (#11266, #10145, #9716) document skills not being auto-discovered despite proper structure.

**Second, add explicit delegation triggers** to your CLAUDE.md. The pattern that works includes bold emphasis, specific agent-to-task mappings, and phrases like "use PROACTIVELY" or "MUST BE USED" in subagent descriptions.

**Third, consider using Task(...) clones** instead of specialized subagents. This approach keeps all context available to delegated agents rather than gatekeeping information in specialized configs.

**Fourth, try explicit invocation** for deterministic automation. Rather than relying on automatic delegation, use syntax like `> Use the test-runner subagent to fix failing tests` to force specific agent usage.

The fundamental insight from both research and community experience: role definitions set stylistic tone but **context engineering, clear task boundaries, and strategic description fields** drive reliable delegation behavior. The most successful CLAUDE.md configurations combine minimal high-level guidance with explicit triggers for when and how to delegate.