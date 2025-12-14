# Best open source Claude Code skills for landing pages

**The top choice is the Copywriter Skill by @daffy0208**, available at claude-plugins.dev, which provides comprehensive landing page formulas, headline templates, and conversion copywriting frameworks. For maximum effectiveness, pair it with alirezarezvani's claude-skills library (143 GitHub stars), which offers production-ready marketing and content creation capabilities including SEO optimization and brand voice analysis tools.

Claude Code's skill ecosystem emerged in late 2024-2025, meaning purpose-built landing page copywriting skills remain limited but growing rapidly. Anthropic has not released official copywriting skills—their **frontend-design skill** focuses on visual design rather than conversion copy. Community developers have filled this gap with several high-quality options.

## The Copywriter Skill leads for conversion-focused writing

The **Copywriter Skill** (github.com/daffy0208/ai-dev-standards/tree/main/SKILLS/copywriter) stands out as the most comprehensive landing page copywriting tool. It provides:

- **Landing page formula**: Headline (main benefit, not feature), subheadline (how it works), CTA (primary action), and social proof structure
- **Headline templates**: "How to [achieve goal] without [pain point]," "[Number] ways to [achieve benefit]," "Get [desired outcome] in [timeframe]"
- **UX writing patterns**: Button labels, error messages, onboarding flows, empty states
- **Voice and tone guidelines**: Adaptive guidance for brand consistency

The skill covers the complete landing page stack—hero sections, feature descriptions, CTAs, and email campaigns—with practical code examples. Installation is straightforward through claude-plugins.dev or direct GitHub download.

## alirezarezvani/claude-skills offers the deepest marketing toolkit

With **143 stars and 28 forks**, this MIT-licensed repository (github.com/alirezarezvani/claude-skills) delivers three production-ready marketing skills:

The **Content Creator Skill** includes a Python CLI for brand voice analysis measuring tone, formality, and readability, plus an SEO optimizer checking keyword density, meta tags, and content structure. It provides **15+ content frameworks** for blogs, emails, social posts, and video scripts, along with platform-specific guides for LinkedIn, Twitter, Instagram, Facebook, and TikTok.

The **Marketing Demand & Acquisition Skill** covers full-funnel strategy from top-of-funnel to bottom-of-funnel, with channel playbooks for LinkedIn Ads, Google Ads, Meta, and SEO. A CAC calculator tool helps measure acquisition efficiency.

The **Product Marketing Skill** incorporates April Dunford's positioning methodology, go-to-market strategy playbooks (PLG, sales-led, hybrid), **90-day product launch frameworks**, and competitive battlecard templates.

Documentation quality is exceptional—these skills are described as "production ready" with clear installation instructions.

## vibe-marketing MCP excels at social-optimized copy

The **vibe-marketing MCP server** (github.com/synthetic-ci/vibe-marketing, 5 stars, MIT license) provides platform-specific copywriting frameworks optimized for Twitter, Instagram, LinkedIn, TikTok, YouTube, and Facebook.

Key capabilities include a **social media hooks database** with proven engagement patterns, **12+ brand archetypes** (Hero, Sage, etc.) for consistent voice, and **problematic phrase detection** that flags AI-sounding language. The `validate-content-before-fold` tool checks if above-the-fold content will convert effectively.

Installation via Smithery.ai (smithery.ai/server/@synthetic-ci/vibe-marketing) simplifies setup. This skill works best for landing pages driving social traffic where platform-native copy matters.

## The Sales Copywriting Skill targets high-conversion scenarios

Available at github.com/Useforclaude/skills-claude, this skill focuses specifically on conversion mechanics:

- **AIDA framework**: Attention → Interest → Desire → Action sequences
- **PAS framework**: Problem → Agitate → Solution structures  
- **BAB framework**: Before → After → Bridge storytelling
- **Objection handling** patterns and urgency/scarcity tactics

This skill suits aggressive conversion pages—sales letters, product launches, and promotional landing pages—where direct response techniques drive results.

## Official Anthropic skills support design, not copy

Anthropic's **frontend-design skill** (github.com/anthropics/skills) creates "distinctive, production-grade frontend interfaces" for landing pages and web applications. It explicitly avoids "generic AI slop aesthetics" through bold typography, cohesive color themes, and unexpected layouts.

However, this skill focuses entirely on visual design—not copywriting. Pair it with the Copywriter Skill for complete landing page creation: frontend-design handles the look while Copywriter handles the words.

The **brand-guidelines** and **theme-factory** skills provide additional design consistency but offer no copywriting capabilities.

## Skills require proper activation to work reliably

Community testing revealed Claude Code skills often fail to activate automatically—success rates as low as **20-50%** without proper configuration. The solution is the "Holy Trinity" approach documented in diet103's infrastructure showcase (github.com/diet103/claude-code-infrastructure-showcase, **7.6k stars**):

- **Forced Evaluation Hook**: Three-step process (EVALUATE → ACTIVATE → IMPLEMENT) that achieves **84% activation success**
- **skill-rules.json configuration**: UserPromptSubmit hook that analyzes prompts and suggests relevant skills automatically

For production use, implement these activation patterns alongside whichever copywriting skill you choose.

## Practical recommendations for landing page workflows

Based on practitioner guidance from Animalz, Strategic Nerds, and other marketing teams using Claude Code:

Start with **inspiration collection** from saaslandingpage.com, saasframe.io, or 21st.dev rather than attempting one-shot generation. Create **detailed design system documentation** (200-300+ lines) specifying fonts, colors, spacing, and component styles—this prevents Claude from producing inconsistent output.

Use **iterative prompting** with 3-5 messages per section rather than requesting complete pages. Separate copywriting from design implementation—many practitioners use Claude's web interface for copy drafting, then Claude Code for technical implementation.

Always apply **human review** for brand voice alignment and legal compliance. Claude can hallucinate metrics or fabricate claims, making QA essential for published landing pages.

## Conclusion

For landing page copywriting specifically, the **Copywriter Skill** (@daffy0208) provides the most direct value with ready-to-use formulas and templates. Supplement it with **alirezarezvani/claude-skills** for deeper marketing strategy including SEO optimization, brand voice analysis, and go-to-market frameworks. Add the **vibe-marketing MCP** when social media traffic is your primary source.

The ecosystem remains young—most skills appeared between October and December 2025. No single tool yet combines A/B copy variation testing, headline scoring, and full conversion rate optimization. However, combining these community skills with proper activation hooks delivers meaningful productivity gains: practitioners report reducing content creation time from hours to minutes and cutting marketing costs by **80%** or more.