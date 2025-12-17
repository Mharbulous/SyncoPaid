#!/usr/bin/env python3
"""
Conflict Detection for Story Tree
Detects duplicate, overlapping, and competing stories using lightweight text similarity.

No external dependencies - uses only Python stdlib.
"""

import sqlite3
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
from collections import Counter

DB_PATH = Path('.claude/data/story-tree.db')

# Domain-specific synonym groups - words in same group are treated as equivalent
SYNONYM_GROUPS = [
    {'screenshot', 'screenshots', 'capture', 'captures', 'image', 'images', 'visual'},
    {'archive', 'archives', 'archiving', 'archived', 'retention', 'cleanup', 'compress', 'compressed', 'zip', 'old'},
    {'block', 'blocks', 'blocking', 'blocked', 'blocklist', 'blacklist', 'filter', 'exclude', 'privacy', 'sensitive'},
    {'config', 'configuration', 'configure', 'configurable', 'settings', 'preferences', 'options', 'customize'},
    {'matter', 'matters', 'client', 'clients', 'case', 'cases', 'billing', 'legal'},
    {'database', 'db', 'sqlite', 'storage', 'store', 'stored', 'persist', 'save'},
    {'track', 'tracking', 'tracker', 'monitor', 'monitoring', 'log', 'logging', 'record', 'recording'},
    {'window', 'windows', 'application', 'applications', 'app', 'apps', 'program', 'programs', 'process'},
    {'browser', 'browsers', 'chrome', 'edge', 'firefox', 'url', 'urls', 'web', 'website', 'address'},
    {'extract', 'extraction', 'extracting', 'parse', 'parsing', 'context', 'get', 'retrieve', 'obtain', 'title'},
    {'ai', 'llm', 'categorization', 'categorize', 'classify', 'classification', 'match', 'matching', 'smart', 'intelligent'},
    {'prompt', 'prompts', 'dialog', 'notification', 'alert', 'popup', 'ask', 'question'},
    {'idle', 'inactive', 'away', 'pause', 'paused', 'resume', 'resumption', 'break'},
    {'review', 'reviewing', 'interface', 'ui', 'display', 'view', 'viewer', 'show', 'screen', 'interactive'},
    {'learn', 'learning', 'correction', 'corrections', 'feedback', 'improve', 'train', 'adapt'},
    {'transition', 'switch', 'switching', 'change', 'detect', 'detection', 'trigger'},
    {'monthly', 'month', 'daily', 'weekly', 'periodic', 'scheduled', 'automatic', 'automatically', 'regular'},
    {'entry', 'entries', 'event', 'events', 'activity', 'activities', 'time', 'session'},
    {'outlook', 'email', 'emails', 'mail', 'inbox', 'message', 'messages'},
    {'automation', 'automate', 'automated', 'uiautomation', 'accessible', 'accessibility'},
    {'enhanced', 'advanced', 'improved', 'better', 'extended'},
]

# Build synonym lookup: word -> canonical form (first word in group)
SYNONYM_MAP = {}
for group in SYNONYM_GROUPS:
    canonical = sorted(group)[0]  # Use alphabetically first as canonical
    for word in group:
        SYNONYM_MAP[word] = canonical


@dataclass
class StoryComponents:
    """Parsed user story components."""
    story_id: str
    title: str
    description: str
    status: str
    role: Optional[str] = None
    want: Optional[str] = None
    benefit: Optional[str] = None
    criteria: Optional[str] = None
    keywords: set = field(default_factory=set)
    normalized_keywords: set = field(default_factory=set)


@dataclass
class Conflict:
    """A detected conflict between two stories."""
    story_a_id: str
    story_b_id: str
    conflict_type: str  # 'duplicate', 'scope_overlap', 'competing'
    confidence: float   # 0.0 to 1.0
    reason: str
    want_similarity: float
    benefit_similarity: float
    title_similarity: float
    criteria_similarity: float = 0.0


STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
    'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'just', 'don', 'now', 'i', 'want', 'that', 'this',
    'it', 'its', 'and', 'or', 'but', 'if', 'because', 'until', 'while',
    'user', 'users', 'they', 'them', 'their', 'my', 'me', 'we', 'our',
    'using', 'used', 'use', 'also', 'like', 'new', 'first', 'last',
    'any', 'every', 'both', 'either', 'neither', 'whether', 'while',
    'specific', 'appropriate', 'relevant', 'current', 'existing'
}


def tokenize(text: str, normalize: bool = False) -> set:
    """Convert text to lowercase word tokens, optionally normalizing synonyms."""
    if not text:
        return set()

    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    tokens = {w for w in words if w not in STOPWORDS}

    if normalize:
        tokens = {SYNONYM_MAP.get(w, w) for w in tokens}

    return tokens


def extract_criteria(description: str) -> str:
    """Extract acceptance criteria from description."""
    # Find acceptance criteria section
    match = re.search(r'Acceptance Criteria[:\s]*\n(.*?)(?:\n\n[A-Z]|\Z)', description, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)

    # Try to find bullet points
    bullets = re.findall(r'[-*]\s*\[?\s*[xX ]?\]?\s*(.+)', description)
    if bullets:
        return ' '.join(bullets)

    return ''


def extract_components(story_id: str, title: str, description: str, status: str) -> StoryComponents:
    """Extract user story components using regex patterns."""
    components = StoryComponents(
        story_id=story_id,
        title=title,
        description=description,
        status=status
    )

    # Strip markdown bold markers for easier parsing
    clean_desc = re.sub(r'\*\*', '', description)

    # Pattern: "As a [role]"
    role_match = re.search(r'[Aa]s (?:a|an) ([^,\n]+?)(?:,|\n|who|I want)', clean_desc)
    if role_match:
        components.role = role_match.group(1).strip()

    # Pattern: "I want [to] [want]"
    want_match = re.search(r'[Ii] want (?:to )?(.+?)(?:\s+[Ss]o that|\s*\n\n|\s*Acceptance|$)', clean_desc, re.DOTALL)
    if want_match:
        components.want = want_match.group(1).strip()
        components.want = re.sub(r'\s+', ' ', components.want)

    # Pattern: "So that [benefit]"
    benefit_match = re.search(r'[Ss]o that (.+?)(?:\s*\n\n|\s*Acceptance|\s*$)', clean_desc, re.DOTALL)
    if benefit_match:
        components.benefit = benefit_match.group(1).strip()
        components.benefit = re.sub(r'\s+', ' ', components.benefit)

    # Extract acceptance criteria
    components.criteria = extract_criteria(description)

    # Build keyword sets
    all_text = f"{title} {components.want or ''} {components.benefit or ''} {components.criteria}"
    components.keywords = tokenize(all_text, normalize=False)
    components.normalized_keywords = tokenize(all_text, normalize=True)

    return components


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def containment_similarity(set_a: set, set_b: set) -> float:
    """Compute containment: what fraction of the smaller set is in the larger."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    min_size = min(len(set_a), len(set_b))
    return intersection / min_size if min_size > 0 else 0.0


def text_similarity(text_a: Optional[str], text_b: Optional[str], normalize: bool = True) -> float:
    """Compute text similarity using normalized tokens."""
    if not text_a or not text_b:
        return 0.0

    tokens_a = tokenize(text_a, normalize=normalize)
    tokens_b = tokenize(text_b, normalize=normalize)

    if not tokens_a or not tokens_b:
        return 0.0

    jaccard = jaccard_similarity(tokens_a, tokens_b)
    containment = containment_similarity(tokens_a, tokens_b)

    # Weighted combination
    return 0.5 * jaccard + 0.5 * containment


def classify_conflict(
    title_sim: float,
    want_sim: float,
    benefit_sim: float,
    criteria_sim: float,
    comp_a: StoryComponents,
    comp_b: StoryComponents
) -> Optional[Conflict]:
    """Classify the relationship between two stories based on similarities."""

    # Skip if stories are in same hierarchy (parent-child)
    if comp_a.story_id.startswith(comp_b.story_id + '.') or \
       comp_b.story_id.startswith(comp_a.story_id + '.'):
        return None

    # Normalized keyword overlap (with synonyms)
    norm_overlap = len(comp_a.normalized_keywords & comp_b.normalized_keywords)
    norm_smaller = min(len(comp_a.normalized_keywords), len(comp_b.normalized_keywords))
    norm_containment = norm_overlap / norm_smaller if norm_smaller > 0 else 0.0

    # Raw keyword overlap (without synonyms)
    raw_overlap = len(comp_a.keywords & comp_b.keywords)

    # Combined score with multiple signals
    combined = (
        0.25 * title_sim +
        0.20 * want_sim +
        0.15 * benefit_sim +
        0.25 * criteria_sim +
        0.15 * norm_containment
    )

    # DUPLICATE: High title similarity
    if title_sim >= 0.55:
        return Conflict(
            story_a_id=comp_a.story_id,
            story_b_id=comp_b.story_id,
            conflict_type='duplicate',
            confidence=min(title_sim + 0.15, 0.95),
            reason=f"Similar titles: title={title_sim:.0%}, criteria={criteria_sim:.0%}",
            want_similarity=want_sim,
            benefit_similarity=benefit_sim,
            title_similarity=title_sim,
            criteria_similarity=criteria_sim
        )

    # DUPLICATE: High criteria overlap (acceptance criteria are specific)
    if criteria_sim >= 0.35 and norm_containment >= 0.40:
        return Conflict(
            story_a_id=comp_a.story_id,
            story_b_id=comp_b.story_id,
            conflict_type='duplicate',
            confidence=min(criteria_sim + 0.25, 0.90),
            reason=f"Similar acceptance criteria: criteria={criteria_sim:.0%}, keywords={norm_containment:.0%}",
            want_similarity=want_sim,
            benefit_similarity=benefit_sim,
            title_similarity=title_sim,
            criteria_similarity=criteria_sim
        )

    # DUPLICATE: High combined score
    if combined >= 0.35:
        return Conflict(
            story_a_id=comp_a.story_id,
            story_b_id=comp_b.story_id,
            conflict_type='duplicate',
            confidence=min(combined + 0.20, 0.85),
            reason=f"High overall similarity: combined={combined:.0%}",
            want_similarity=want_sim,
            benefit_similarity=benefit_sim,
            title_similarity=title_sim,
            criteria_similarity=criteria_sim
        )

    # SCOPE_OVERLAP: High normalized keyword containment
    if norm_containment >= 0.40 and (title_sim >= 0.10 or criteria_sim >= 0.15):
        return Conflict(
            story_a_id=comp_a.story_id,
            story_b_id=comp_b.story_id,
            conflict_type='scope_overlap',
            confidence=min(norm_containment + 0.15, 0.75),
            reason=f"Overlapping scope: keywords={norm_containment:.0%} ({norm_overlap}/{norm_smaller}), criteria={criteria_sim:.0%}",
            want_similarity=want_sim,
            benefit_similarity=benefit_sim,
            title_similarity=title_sim,
            criteria_similarity=criteria_sim
        )

    # COMPETING: Similar want/criteria but different benefit
    if (want_sim >= 0.30 or criteria_sim >= 0.25) and benefit_sim < 0.20:
        conf = max(want_sim, criteria_sim)
        return Conflict(
            story_a_id=comp_a.story_id,
            story_b_id=comp_b.story_id,
            conflict_type='competing',
            confidence=min(conf + 0.15, 0.75),
            reason=f"Same problem, different approach: want={want_sim:.0%}, criteria={criteria_sim:.0%}, benefit={benefit_sim:.0%}",
            want_similarity=want_sim,
            benefit_similarity=benefit_sim,
            title_similarity=title_sim,
            criteria_similarity=criteria_sim
        )

    return None


def load_stories(db_path: Path) -> list[StoryComponents]:
    """Load all active stories from database.

    Computes effective status from three-field system: disposition > hold_reason > stage
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT id, title, description,
               COALESCE(disposition, hold_reason, stage) AS status
        FROM story_nodes
        WHERE disposition IS NULL OR disposition NOT IN ('rejected', 'archived', 'deprecated', 'infeasible')
        ORDER BY id
    """)

    stories = []
    for row in cursor:
        comp = extract_components(
            story_id=row['id'],
            title=row['title'],
            description=row['description'],
            status=row['status']
        )
        stories.append(comp)

    conn.close()
    return stories


def detect_conflicts(stories: list[StoryComponents], min_confidence: float = 0.50) -> list[Conflict]:
    """Detect conflicts between all story pairs."""
    conflicts = []
    n = len(stories)

    for i in range(n):
        for j in range(i + 1, n):
            comp_a = stories[i]
            comp_b = stories[j]

            # Quick filter: skip if no normalized keyword overlap
            if not (comp_a.normalized_keywords & comp_b.normalized_keywords):
                continue

            title_sim = text_similarity(comp_a.title, comp_b.title)
            want_sim = text_similarity(comp_a.want, comp_b.want)
            benefit_sim = text_similarity(comp_a.benefit, comp_b.benefit)
            criteria_sim = text_similarity(comp_a.criteria, comp_b.criteria)

            conflict = classify_conflict(title_sim, want_sim, benefit_sim, criteria_sim, comp_a, comp_b)

            if conflict and conflict.confidence >= min_confidence:
                conflicts.append(conflict)

    conflicts.sort(key=lambda c: c.confidence, reverse=True)
    return conflicts


def format_report(conflicts: list[Conflict], stories: list[StoryComponents]) -> str:
    """Format conflicts as a readable report."""
    if not conflicts:
        return "No conflicts detected."

    story_lookup = {s.story_id: s for s in stories}
    lines = [f"Found {len(conflicts)} potential conflict(s):\n"]

    for i, c in enumerate(conflicts, 1):
        story_a = story_lookup.get(c.story_a_id)
        story_b = story_lookup.get(c.story_b_id)

        lines.append(f"## Conflict {i}: {c.conflict_type.upper()} (confidence: {c.confidence:.0%})")
        lines.append(f"")
        lines.append(f"**Story A**: `{c.story_a_id}` - {story_a.title if story_a else 'Unknown'}")
        lines.append(f"**Story B**: `{c.story_b_id}` - {story_b.title if story_b else 'Unknown'}")
        lines.append(f"")
        lines.append(f"**Reason**: {c.reason}")
        lines.append(f"")

        if story_a and story_a.want:
            lines.append(f"**A wants**: {story_a.want[:200]}...")
        if story_b and story_b.want:
            lines.append(f"**B wants**: {story_b.want[:200]}...")

        lines.append(f"")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    """Run conflict detection and output results."""
    import argparse

    parser = argparse.ArgumentParser(description='Detect story conflicts')
    parser.add_argument('--db', type=Path, default=DB_PATH, help='Database path')
    parser.add_argument('--min-confidence', type=float, default=0.50, help='Minimum confidence threshold')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Error: Database not found at {args.db}")
        return 1

    stories = load_stories(args.db)
    print(f"Loaded {len(stories)} stories")

    conflicts = detect_conflicts(stories, args.min_confidence)

    if args.format == 'json':
        output = [asdict(c) for c in conflicts]
        print(json.dumps(output, indent=2))
    else:
        print(format_report(conflicts, stories))

    return 0 if not conflicts else len(conflicts)


if __name__ == '__main__':
    exit(main())
