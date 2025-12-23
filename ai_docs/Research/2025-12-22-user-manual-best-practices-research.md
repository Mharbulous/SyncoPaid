# SaaS documentation best practices: what the evidence actually says

A systematic verification of documentation recommendations reveals **strong support for most claims**, with a few important corrections. The writing guidelines and task-oriented approach are universally endorsed by authoritative sources. However, the oft-cited "25% statistic" requires careful attribution, screenshot annotation guidance needs nuance, and two of the five example companies aren't actually recognized as documentation exemplars.

## The "Life Is Too Short to RTFM" study is real, but the 25% figure needs context

The frequently cited study is legitimate peer-reviewed research by Blackler, Gomez, Popovic, and Thompson, published in *Interacting with Computers* (Oxford University Press, 2016). The researchers surveyed **170 participants over 7 years** and conducted longitudinal diary studies. Their key finding: "manuals are not read by the majority of people."

However, the specific "25%" statistic appears to be conflated from secondary sources. The original abstract states that the majority don't read documentation—without specifying 25%. A separate van Loggem (2014) study found that **26% of tokens** were allocated to documentation by student users, which may be the actual source of this figure.

Critically, other research shows higher consultation rates depending on context. Studies by Wright et al. found **82.9%** consulted complex equipment manuals, while Smart et al. recorded **99%** consulting word processor documentation at some point. The distinction is between *any* consultation versus *thorough reading*—most users consult documentation briefly but don't read comprehensively.

**Minimalism is strongly validated.** John Carroll's foundational research (*The Nurnberg Funnel*, 1990) established that minimal manuals with **3-page chapters** outperformed comprehensive documentation. Nielsen Norman Group research confirms users scan rather than read online content, with only about **28% of words** on a typical page actually read. The DITA (Darwin Information Typing Architecture) standard, now used industry-wide, was built directly on Carroll's minimalism principles.

## All five writing guidelines verified with strong consensus

Extensive research confirms each recommendation from authoritative sources including Microsoft, Google, the U.S. Plain Language Act, and Nielsen Norman Group.

**Active voice** receives universal endorsement. Microsoft's style guide instructs writers to "use active voice and indicative mood most of the time." Google's developer documentation guide states: "Use active voice: make clear who's performing the action." The federal Plain Language Guidelines explain the reasoning: "Active voice makes it clear who is supposed to do what. It eliminates ambiguity about responsibilities."

**Starting steps with action verbs** is industry standard. Google's procedures documentation specifies: "Steps should begin with an imperative verb, be complete sentences, and follow parallel structure." Microsoft explicitly advises: "Most of the time, start each statement with a verb. Edit out 'you can' and 'there is, there are, there were.'"

**The 15-20 word sentence length** is validated by multiple sources. The U.S. Office of Personnel Management states: "Sentence length should average 15-20 words." Oxford Guide to Plain English concurs: "Over the whole document, make the average sentence length 15-20 words." American Press Institute research demonstrates the impact: at **8 words**, comprehension is 100%; at **14 words**, 90%; at **43+ words**, comprehension drops below 10%. The key nuance: this is an *average*, not a maximum—varied sentence length improves readability.

**Short paragraphs (2-3 sentences)** aligns with guidance, though sources emphasize "one topic per paragraph" rather than strict counts. Google's style guide states: "A paragraph longer than 5 or 6 sentences is often an indication that the paragraph is trying to convey too much information." Single-sentence paragraphs are acceptable; Nielsen Norman Group notes that "users will skip over any extra ideas if they are not caught by the first few words."

**Plain language** is not merely recommended—it's legally mandated for U.S. federal agencies under the Plain Language Act of 2010. Microsoft advises: "Write like you speak. Avoid jargon and overly complex or technical language. It should sound like a friendly conversation."

## Visual and structural guidelines mostly verified, with important nuances

**Screenshots should NOT always be annotated**—this claim requires correction. While annotations are valuable for directing attention to specific elements, sources recommend judicious use rather than mandatory annotation. Ritza's style guide warns: "Do not use too many annotations on a single screenshot (often around 3-4 is the maximum before the shot starts looking very cluttered)." Annotations are best used for non-obvious interactions, complex interfaces, or when text alone would be lengthy. Simple, self-explanatory interfaces may not require annotation, and over-annotating creates maintenance burden when UI changes.

**Videos supplementing rather than replacing text is strongly verified.** ClickHelp states definitively: "Though video adds value to documentation, it cannot substitute it." The reasoning is practical: text excels at searchability (search engines index full text but only video metadata), skimmability (users can scan text in seconds), accessibility (text requires no captions or audio descriptions), and maintainability (updating text is far simpler than re-recording video).

**Getting Started guides are essential**—verified as "cornerstone of onboarding" by multiple sources. HeroThemes notes: "The goal is to get users to their 'aha!' moment as quickly as possible." ProProfs cites "around a 30% reduction in support costs" from self-service tools including quick-start guides.

**Single-task article focus is standard practice** in topic-based authoring. The DITA framework distinguishes three topic types: concepts (explain), tasks (how-to steps), and references (lookup information). GitHub's documentation best practices specify: "Keep each document focused on a particular topic or task."

**Searchability is critical**—validated as Nielsen Norman Group's Heuristic #10 for help systems. Docsie claims proper search "can improve documentation discoverability by 70%." Best practice: display search prominently in the header with autocomplete suggestions.

**Progressive disclosure is a foundational UX pattern** introduced by Jakob Nielsen in 1995. Nielsen Norman Group states it "improves 3 of usability's 5 components: learnability, efficiency of use, and error rate." In documentation, this manifests as accordions, expandable sections, and hyperlinked deeper content. The caveat: limit to two levels maximum—users get lost with more.

## Task-oriented documentation is the established standard

The preference for task-based over feature-based documentation is strongly validated by technical communication standards. The OASIS DITA 1.3 specification defines tasks as "the main building blocks for task-oriented user assistance" that "answer the question of 'how to?' by telling the user precisely what to do."

McMurrey's *Online Technical Writing* states the case definitively: "When you write for users, you have a choice of two approaches, function orientation and task orientation, **the latter of which is by far the better choice**." Linux Magazine memorably describes poor feature-oriented documentation as "death marches through the menus"—starting with the first menu item and proceeding sequentially through every feature.

The widely-adopted **Diátaxis framework** (developed by Daniele Procida and used by Python, Django, Gatsby, Cloudflare, and Ubuntu) separates documentation into four types based on user needs: tutorials (learning), how-to guides (accomplishing tasks), reference (technical facts), and explanation (background). This framework explicitly centers user goals over product features.

One important nuance: **reference documentation is appropriately feature-oriented.** API documentation, configuration options, and technical specifications are information-oriented by nature. The principle applies primarily to user-facing help content.

## Anti-patterns confirmed with strong evidence

All listed anti-patterns are validated by authoritative sources.

**Lengthy introductions** contradict fundamental web reading behavior. Nielsen Norman Group's research (1997-present) established that reading from screens is 25% slower than paper, leading to the recommendation to "write no more than 50% of the text you would have used in a hardcopy publication." DITA Best Practices specifies that context sections should be "brief and does not replace or recreate a concept topic."

**Marketing language in documentation** is explicitly cautioned against in Google's Developer Documentation Style Guide, which warns against "excessive claims." The fundamental problem: technical documentation serves users seeking task completion, not prospects being persuaded. Mixing purposes confuses both audiences. ProProfs summarizes the principle: "Educate, do not sell."

**Walls of text** trigger scanning rather than reading behavior. Nielsen Norman Group found that "people don't want to read a lot of text from computer screens." Solutions include using headings, subheadings, bullet points, and white space to create visual hierarchy.

Additional verified anti-patterns include:
- **Mixing content types** within single documents (explanations in API references)
- **Vague language** ("some," "many," "often") without specifics
- **Inconsistent terminology** for the same concepts
- **Missing prerequisites** or warnings essential for task completion
- **Ignoring audience** by not adjusting complexity to reader expertise

## Only three of five example companies are genuinely cited as exemplary

The research reveals significant corrections needed for the recommended examples to study.

**Stripe is the undisputed gold standard for API documentation.** It appears in virtually every "best documentation" list from Mintlify, Apidog, Nordic APIs, Archbee, DreamFactory, and ReadMe. Praised qualities include: three-column layout (navigation, content, code examples), personalized code samples with user's API keys auto-populated, interactive language switching, and clear error documentation. However, Stripe's Help Center (distinct from API docs) is noted as "a bit cluttered." For simple SaaS apps, Stripe's principles apply but the implementation is API-focused.

**Slack demonstrates excellent user documentation.** Featured in Archbee's "9 Examples of Great SaaS End User Documentation," Slack earns praise for strong visual identity matching their brand, plain language delivery, interactive navigation elements, and tips that elevate beyond basic instructions. Their prominent search and progressive approach makes documentation "engaging and even fun to use." **Highly relevant** for consumer-facing apps like time trackers.

**Ahrefs is cited for good help center practices.** Also in Archbee's list, praised for prominent search bar design, well-organized topic collections, positioning their Getting Started guide first, and comprehensive educational content through Ahrefs Academy. Moderately relevant for simpler tools.

**Notion is NOT typically cited as a documentation exemplar.** No articles were found praising Notion's own Help Center as an example. Instead, most references discuss using Notion *as a tool* to create documentation (via HelpKit, Notiondesk, etc.). Notion's editor is praised; their documentation is not.

**Toggl Track is NOT cited as exemplary.** Despite being a time tracking app itself, no technical writing publications or "best documentation" lists feature Toggl. User reviews describe their Help Center as "easy to use" and "helpful"—functional but unremarkable. It represents an adequate baseline rather than best-in-class. For time tracker documentation specifically, Toggl provides a reference for "adequate" but other examples would be more instructive.

## Corrections and additions to the original guide

Based on this research, the best practices guide should be updated:

| Original Claim | Verification Status | Recommended Correction |
|---------------|---------------------|----------------------|
| Users read manuals 25% of the time | Partially verified | Cite as "majority don't read thoroughly" from Blackler et al. (2016); 25% figure is from separate research |
| Screenshots should ALWAYS be annotated | Needs correction | Change to "annotate screenshots when they clarify non-obvious elements; avoid over-annotation" |
| Notion as exemplary documentation | Not verified | Remove or replace with Intercom, Asana, or Zendesk—frequently cited alternatives |
| Toggl Track as exemplary documentation | Not verified | Remove; use as baseline reference only, not as aspirational example |
| 15-20 word sentences | Verified | Add that this is an *average*; sentence variety is important |
| 2-3 sentence paragraphs | Verified with nuance | Emphasize "one topic per paragraph" as the primary principle |

**Additional authoritative sources to cite:**
- Google Developer Documentation Style Guide (free, comprehensive, regularly updated)
- Microsoft Writing Style Guide (industry standard)
- Diátaxis Framework (diataxis.fr—adopted by major open-source projects)
- Nielsen Norman Group research on UX writing
- U.S. Plain Language Guidelines (plainlanguage.gov—legally mandated standards)
- DITA OASIS Standard (technical communication industry standard)

Note: The Society for Technical Communication (STC) ceased operations in January 2025, so their guidelines should be replaced with current sources.

## Conclusion

The best practices guide is largely sound, with core recommendations validated by decades of research from Carroll's minimalism work through current industry standards. The writing guidelines and structural recommendations have strong consensus across all authoritative sources. The task-oriented approach is now embedded in formal standards like DITA and frameworks like Diátaxis.

The primary corrections needed are: qualifying the 25% statistic with proper attribution, softening the "always annotate" guideline, and replacing Notion and Toggl Track with genuinely cited exemplars like Intercom or Asana for user documentation. For a simple time tracking app, Slack's approach to engaging, on-brand help content may be more instructive than Stripe's developer-focused API documentation.