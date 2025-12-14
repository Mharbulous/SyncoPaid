# Optimizing CLAUDE.md files for Claude Code

**CLAUDE.md is the highest-leverage configuration point for Claude Code**, a special Markdown file automatically loaded into every conversation to provide persistent project context, coding standards, and workflow instructions. A well-optimized CLAUDE.md eliminates repetitive explanations, enforces consistency, and dramatically improves Claude's code quality. On Windows 11 with VS Code, you can achieve **50-70% token reduction** and significantly better output by following the optimization principles below.

## What CLAUDE.md does and where it lives

CLAUDE.md functions as Claude Code's persistent memory system—content you'd otherwise explain every session gets loaded automatically. According to Anthropic's official documentation, ideal content includes common bash commands, code style guidelines, testing instructions, repository etiquette, developer environment setup, and project-specific quirks or warnings.

Claude Code implements a **four-tier memory hierarchy**, loaded in order of precedence:

| Priority | Location | Scope |
|----------|----------|-------|
| 1 (Highest) | Enterprise-managed path | Organization-wide |
| 2 | `~/.claude/CLAUDE.md` | All your sessions |
| 3 | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Current project |
| 4 | Child directory CLAUDE.md files | On-demand for subdirectories |

For Windows 11 users, user-level settings live at `%USERPROFILE%\.claude\CLAUDE.md`. Claude Code reads memories recursively—starting from your current working directory upward—making monorepo setups with nested CLAUDE.md files particularly effective.

## Structure your file for maximum clarity

The most effective CLAUDE.md files share a common architecture: **essential rules first, detailed context second, validation steps last**. Here's a proven template structure:

```markdown
# Project: [Name]

## 🚨 CRITICAL RULES
- YOU MUST run `pnpm run typecheck` before committing
- Never modify files in `/generated/` directly

## Tech Stack
- TypeScript 5.3, React 18, Next.js 14 (App Router)
- pnpm for package management
- Tailwind CSS 4 with shadcn/ui

## Commands
- `pnpm dev` — Start development server
- `pnpm test` — Run Jest tests (prefer single test files)
- `pnpm lint` — ESLint + Prettier check

## Project Structure
- `app/` — Next.js App Router pages
- `components/` — React components (PascalCase files)
- `lib/` — Utility functions and shared logic

## Code Conventions
- Use ES modules (import/export), not CommonJS
- Destructure imports: `import { foo } from 'bar'`
- Type hints required on all exported functions

## Final Steps
**IMPORTANT**: After completing changes:
1. Run `pnpm lint` and fix any errors
2. Run `pnpm typecheck` and resolve issues
3. Run relevant tests before marking complete
```

**Be specific over vague**—"Use 2-space indentation" beats "Format code properly" every time. Anthropic recommends treating CLAUDE.md like a frequently-used prompt: iterate, test, and refine based on what produces the best instruction-following.

## Token efficiency determines performance

Every line of CLAUDE.md consumes context window tokens on every interaction. With Claude's **200K token context** (or 1M on some API configurations), optimization directly impacts both cost and response quality. Teams report **62% token reduction** by trimming bloated files—from 2,800 lines down to 180 lines.

**Keep files under 300 lines**, ideally closer to 60-180 lines for the root file. Each line consumes roughly 20 tokens, meaning a 500-line file burns ~10,000 tokens before you even ask a question. Implement progressive disclosure through this three-tier system:

- **Tier 1 (Always loaded)**: Core CLAUDE.md with essential context only
- **Tier 2 (Referenced)**: Detailed docs in `agent_docs/` or `docs/` folders
- **Tier 3 (On-demand)**: Full documentation loaded only when explicitly needed

Instead of embedding large documentation files with `@mention` syntax (which loads the entire file every session), provide paths with context: "For authentication details, see `docs/AUTH.md`." Claude can then read files on-demand when actually needed.

The import syntax `@path/to/file` does work for including content—useful for team members to provide individual instructions via `@~/personal-prefs.md`—but imports have a **max depth of 5 hops** and content inside code blocks isn't evaluated.

## Write instructions Claude actually follows

Claude's system prompt already contains ~50 instructions, and LLMs reliably follow **150-200 total instructions** before degradation. Don't bloat your CLAUDE.md with redundant guidance—focus on what's genuinely project-specific.

**Use emphasis strategically** for non-negotiable rules. Anthropic's own teams add "IMPORTANT" or "YOU MUST" prefixes to critical instructions:

```markdown
## Critical Rules
- **YOU MUST** run tests before creating any PR
- **IMPORTANT**: Never commit directly to main branch
- **ALWAYS** use TypeScript strict mode
```

**Provide alternatives, not just prohibitions**. Instead of "Never use the --foo flag," write "Use --bar instead of --foo (--foo causes memory leaks)." Claude responds better to positive instructions with reasoning.

**Define workflows for complex tasks**:

```markdown
## Before Modifying Database Schema
1. Review existing migrations in `db/migrations/`
2. Draft migration plan and confirm approach
3. Create new migration file (never edit existing ones)
4. Test rollback procedure before committing
```

During sessions, press the **`#` key** to add instructions Claude will automatically incorporate into the appropriate CLAUDE.md file—a fast way to document repeated corrections.

## Avoid these common mistakes

**Over-stuffing the file** ranks as the top anti-pattern. Adding every possible guideline degrades instruction-following. Keep only universally applicable rules in the root file.

**Using CLAUDE.md as a linter** wastes tokens on rules better enforced by actual tools. Instead of documenting "Use 2-space indentation" in CLAUDE.md, configure ESLint/Prettier and create a hook that runs them automatically:

```bash
# .claude/hooks/post-edit.sh
#!/bin/bash
pnpm lint --fix
pnpm prettier --write "$1"
```

**Mixing unrelated tasks** in one session causes context pollution. Use `/clear` between distinct tasks. For complex multi-step work, use the "Document & Clear" pattern: have Claude dump its plan to a markdown file, run `/clear`, then start fresh with "Read `plan.md` and continue."

**Ignoring `/init` output** happens frequently. While `/init` auto-generates a starter CLAUDE.md by analyzing your codebase, blindly accepting it often produces bloated, generic content. Treat it as a starting point and ruthlessly edit.

**Over-engineering for simple projects** is surprisingly common. Claude defaults to enterprise patterns. For MVPs or proofs-of-concept, add explicit guidance:

```markdown
## Development Philosophy
- This is a POC, NOT an enterprise project
- Start with the simplest solution that works
- Don't add abstractions until genuinely needed
```

One developer reported this saved **59 unnecessary test cases** for a simple button component.

## CLI and VS Code integration differences

Both Claude Code CLI and the VS Code extension (now at **2M+ installs**) share the same CLAUDE.md configuration system—files work identically across both. Key differences lie in the interface:

**CLI advantages**: Full `/memory` command access to view and edit loaded memory files, raw terminal control, headless mode for automation (`claude -p "prompt" --output-format stream-json`).

**VS Code extension advantages**: Real-time inline diffs with accept/reject buttons, visual diff viewing, automatic diagnostic sharing (lint errors flow to Claude automatically), and extended thinking toggle in the prompt input area.

For Windows 11 users, install the VS Code extension directly from the marketplace (search "Claude Code"). Launch with **Ctrl+Esc**, insert file references with **Alt+Ctrl+K**. The extension integrates with VS Code's diff viewer and Restricted Mode for untrusted workspaces.

MCP server configuration requires CLI setup first—run `claude` in terminal, use `/mcp` to configure, then the VS Code extension automatically uses those settings.

## Windows 11 and VS Code setup recommendations

**WSL2 provides the best experience** on Windows 11. Native Windows installation works but WSL offers better performance and compatibility:

```powershell
# PowerShell as Admin
wsl --install
# After restart, in Ubuntu terminal:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 18
npm install -g @anthropic-ai/claude-code
```

**Keep projects in the Linux filesystem** (`~/projects/`) rather than `/mnt/c/Users/...`—cross-filesystem access is significantly slower. Configure Git for proper line endings: `git config --global core.autocrlf input`.

**Use Windows Terminal** (from Microsoft Store) instead of CMD—it handles Unicode, ANSI colors, and multiple tabs properly. For VS Code, the integrated terminal works well when set to use WSL as the default profile.

Common Windows issues include "Permission denied" errors (never use `sudo` for Claude Code installation) and npm PATH problems (configure a user-local npm directory with `npm config set prefix '~/.npm-global'`).

## Validate your optimization is working

**Check context consumption** with `/context` mid-session to see what's using space. Use `/cost` for token usage statistics. Both commands help identify when your CLAUDE.md is consuming excessive resources.

**Test Claude's adherence** by asking it to explain your project structure or summarize its understanding of your conventions. If Claude repeatedly makes mistakes you've documented, your instructions aren't being followed—add emphasis or reword.

**Monitor for degradation signals**: Claude asking questions answered in CLAUDE.md, ignoring emphasized instructions, or quality dropping in long sessions all indicate problems. Response quality degrades significantly in the last 20% of context window capacity.

**Implement verification hooks** in your CLAUDE.md for on-demand checking:

```markdown
## Verification
When I type "qcheck", perform:
1. Review changes against project conventions above
2. Run `pnpm lint` and `pnpm typecheck`
3. Confirm all tests pass for modified code
4. Report any violations found
```

For continuous improvement, run your CLAUDE.md through Anthropic's prompt improver periodically, and commit working versions to git so you can track what produces the best results.

## Conclusion

The most impactful optimizations are **keeping files lean** (under 300 lines), **using progressive disclosure** instead of embedding everything, and **emphasizing critical rules** with explicit markers. For Windows 11 users, WSL2 with projects in the Linux filesystem provides the smoothest experience.

Run `/init` as a starting point, then ruthlessly edit. Press `#` during sessions to capture repeated instructions. Use `/clear` between tasks to prevent context pollution. Treat your CLAUDE.md like production code—iterate based on what actually improves Claude's output quality, and commit working versions to version control.