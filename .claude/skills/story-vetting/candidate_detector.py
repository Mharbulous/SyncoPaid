#!/usr/bin/env python
"""Story vetting Phase 1: Candidate Detection with Cache Support.

Detects potential conflict pairs using heuristics (blocking phase),
then filters out cached false_positives to reduce LLM classification load.
"""

import sqlite3
import json
import re
import sys
import os
from typing import Dict, List, Set, Any, Optional

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import DB_PATH

# Import cache functions
from vetting_cache import (
    migrate_schema, get_cached_decision, make_pair_key, get_cache_stats
)


def tokenize(text: Optional[str]) -> Set[str]:
    """Extract lowercase word tokens, removing stopwords."""
    if not text:
        return set()
    words = re.findall(r'[a-z]+', text.lower())
    stopwords = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after',
        'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'that', 'this', 'these', 'those',
        'user', 'want', 'need', 'able', 'feature', 'system', 'data'
    }
    return set(w for w in words if w not in stopwords and len(w) > 2)


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity coefficient."""
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


def overlap_coefficient(set1: Set[str], set2: Set[str]) -> float:
    """Calculate overlap coefficient (Szymkiewicz-Simpson)."""
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / min(len(set1), len(set2))


def find_specific_keywords(text: Optional[str]) -> Set[str]:
    """Extract specific implementation keywords from description."""
    if not text:
        return set()

    patterns = {
        'sqlite': 'sqlite',
        r'zip.*compress|compress.*zip': 'archive_compress',
        'monthly': 'monthly_schedule',
        r'archiv(?:e|ing)': 'archiving',
        r'retention|cleanup': 'retention_policy',
        r'block.*(?:list|app)|(?:list|app).*block': 'app_blocking',
        r'privacy.*block|block.*privacy': 'privacy_blocking',
        r'skip.*app|app.*skip': 'app_filtering',
        'crud': 'crud',
        'tkinter': 'tkinter_ui',
        r'idle.*resump|resump.*idle': 'idle_resumption',
        r'transition.*detect|detect.*transition': 'transition_detection',
        'ui automation': 'ui_automation',
        r'learn.*correction|correction.*learn|pattern.*learn': 'ai_learning',
        r'matter.*table|table.*matter': 'matter_table',
        r'client.*table|table.*client': 'client_table',
        r'process.*name|exe.*name': 'process_matching',
    }

    found = set()
    text_lower = text.lower()
    for p, label in patterns.items():
        if re.search(p, text_lower):
            found.add(label)
    return found


def detect_candidates(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect candidate conflict pairs for LLM review (blocking phase).

    Args:
        stories: List of story dicts with id, title, description, status

    Returns:
        List of candidate pairs with signals
    """
    candidates = []
    story_data = {}

    # Precompute tokens for all stories
    for s in stories:
        story_id = s['id']
        story_data[story_id] = {
            'story': s,
            'title_tokens': tokenize(s['title']),
            'desc_tokens': tokenize(s['description']),
            'spec_keywords': find_specific_keywords(s['description'])
        }

    # Compare all pairs
    story_ids = list(story_data.keys())
    for i in range(len(story_ids)):
        for j in range(i + 1, len(story_ids)):
            id_a, id_b = story_ids[i], story_ids[j]
            data_a, data_b = story_data[id_a], story_data[id_b]
            story_a, story_b = data_a['story'], data_b['story']

            # Skip if neither is a concept (non-concept vs non-concept)
            if story_a['status'] != 'concept' and story_b['status'] != 'concept':
                continue

            # Skip parent-child relationships
            if id_a.startswith(id_b + '.') or id_b.startswith(id_a + '.'):
                continue

            # Calculate similarity signals
            spec_shared = data_a['spec_keywords'] & data_b['spec_keywords']
            title_sim = jaccard_similarity(data_a['title_tokens'], data_b['title_tokens'])
            title_overlap = overlap_coefficient(data_a['title_tokens'], data_b['title_tokens'])
            desc_sim = jaccard_similarity(data_a['desc_tokens'], data_b['desc_tokens'])

            # Flag as candidate if any signal is strong enough
            is_candidate = (
                len(spec_shared) >= 1 or
                title_sim > 0.15 or
                title_overlap > 0.4 or
                desc_sim > 0.10
            )

            if is_candidate:
                candidates.append({
                    'story_a': {
                        'id': id_a,
                        'title': story_a['title'],
                        'status': story_a['status'],
                        'description': story_a['description']
                    },
                    'story_b': {
                        'id': id_b,
                        'title': story_b['title'],
                        'status': story_b['status'],
                        'description': story_b['description']
                    },
                    'signals': {
                        'shared_keywords': list(spec_shared),
                        'title_similarity': round(title_sim, 2),
                        'title_overlap': round(title_overlap, 2),
                        'desc_similarity': round(desc_sim, 2)
                    }
                })

    return candidates


def filter_cached_candidates(
    conn: sqlite3.Connection,
    candidates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Filter candidates using cache, skipping known false_positives.

    Args:
        conn: SQLite connection
        candidates: List of candidate pairs from detect_candidates

    Returns:
        Dict with filtered candidates and cache statistics
    """
    filtered = []
    cache_hits = {
        'false_positive': 0,
        'other_cached': 0,
        'stale': 0,
        'uncached': 0
    }

    for pair in candidates:
        id_a = pair['story_a']['id']
        id_b = pair['story_b']['id']

        # Check cache
        cached = get_cached_decision(conn, id_a, id_b)

        if cached:
            if cached['classification'] == 'false_positive':
                cache_hits['false_positive'] += 1
                continue  # Skip - already decided as false positive
            else:
                # Non-false-positive cached - include but mark as cached
                cache_hits['other_cached'] += 1
                pair['cached_classification'] = cached['classification']
                pair['cached_action'] = cached['action_taken']
        else:
            cache_hits['uncached'] += 1

        filtered.append(pair)

    return {
        'candidates': filtered,
        'cache_stats': cache_hits,
        'total_before_filter': len(candidates),
        'total_after_filter': len(filtered)
    }


def load_stories(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Load all active stories from database.

    Computes status from three-field system: disposition > hold_reason > stage
    """
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute('''
        SELECT s.id, s.title, s.description,
               COALESCE(s.disposition, s.hold_reason, s.stage) AS status
        FROM story_nodes s
        WHERE s.disposition IS NULL OR s.disposition NOT IN ('archived', 'deprecated')
        ORDER BY s.id
    ''').fetchall()]


def main():
    """Run candidate detection with cache filtering."""
    import argparse

    parser = argparse.ArgumentParser(description='Detect candidate conflict pairs')
    parser.add_argument('--story-id', type=str,
                        help='Only find conflicts involving this specific story ID')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Ensure schema is migrated
    migration_result = migrate_schema(conn)
    if migration_result['version_added'] or migration_result['table_created']:
        print(f"Schema migration: {migration_result}", file=sys.stderr)

    # Load stories
    stories = load_stories(conn)

    # Phase 1: Detect candidates (blocking)
    all_candidates = detect_candidates(stories)

    # Filter to specific story if requested
    if args.story_id:
        all_candidates = [
            c for c in all_candidates
            if c['story_a']['id'] == args.story_id or c['story_b']['id'] == args.story_id
        ]
        print(f"Filtering to story {args.story_id}: {len(all_candidates)} candidates", file=sys.stderr)

    # Filter using cache
    result = filter_cached_candidates(conn, all_candidates)

    # Get cache stats
    cache_info = get_cache_stats(conn)

    conn.close()

    # Output results
    output = {
        'total_stories': len(stories),
        'candidates_before_cache': result['total_before_filter'],
        'candidates_after_cache': result['total_after_filter'],
        'cache_hits': result['cache_stats'],
        'cache_info': cache_info,
        'candidates': result['candidates']
    }

    if args.story_id:
        output['filtered_story_id'] = args.story_id

    # Print summary to stderr
    print(f"\nCandidate Detection Complete", file=sys.stderr)
    print(f"=" * 40, file=sys.stderr)
    print(f"Total stories: {len(stories)}", file=sys.stderr)
    if args.story_id:
        print(f"Filtered to story: {args.story_id}", file=sys.stderr)
    print(f"Candidates found: {result['total_before_filter']}", file=sys.stderr)
    print(f"After cache filter: {result['total_after_filter']}", file=sys.stderr)
    print(f"\nCache stats:", file=sys.stderr)
    print(f"  False positives skipped: {result['cache_stats']['false_positive']}", file=sys.stderr)
    print(f"  Other cached: {result['cache_stats']['other_cached']}", file=sys.stderr)
    print(f"  Uncached (need classification): {result['cache_stats']['uncached']}", file=sys.stderr)

    # Output JSON to stdout
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
