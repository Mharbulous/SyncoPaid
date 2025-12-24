#!/usr/bin/env python3
"""
Process vetting candidates systematically with caching support.

Uses consolidated database operations from story-tree utility.
"""
import sqlite3
import json
import sys
import os

# Import common utilities from story-tree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'story-tree', 'utility'))
from story_db_common import DB_PATH, get_story_version

# Import cache functions from vetting_cache
from vetting_cache import get_cached_decision, store_decision


def filter_uncached_candidates(candidates_json):
    """Filter candidates to only those not in cache or with stale versions."""
    conn = sqlite3.connect(DB_PATH)

    needs_processing = []
    cache_hits = 0

    for candidate in candidates_json['candidates']:
        id_a = candidate['story_a']['id']
        id_b = candidate['story_b']['id']

        cached = get_cached_decision(conn, id_a, id_b)
        if cached:
            # get_cached_decision already handles version validation
            # If it returns a result, the cache is valid
            cache_hits += 1
            continue

        # Need to process this candidate
        needs_processing.append(candidate)

    conn.close()

    print(f"Cache hits: {cache_hits}/{len(candidates_json['candidates'])}", file=sys.stderr)
    print(f"Need processing: {len(needs_processing)}/{len(candidates_json['candidates'])}", file=sys.stderr)

    return needs_processing


def score_candidate(candidate):
    """Score candidate by signal strength for prioritization."""
    signals = candidate['signals']
    score = 0

    # Shared keywords are strongest signal
    score += len(signals['shared_keywords']) * 10

    # Title similarity
    score += signals['title_similarity'] * 5

    # Title overlap
    score += signals['title_overlap'] * 3

    # Description similarity
    score += signals['desc_similarity'] * 2

    return score


if __name__ == '__main__':
    # Read candidates from stdin
    candidates_data = json.load(sys.stdin)

    # Filter to uncached
    uncached = filter_uncached_candidates(candidates_data)

    # Sort by signal strength
    uncached.sort(key=score_candidate, reverse=True)

    # Output
    print(json.dumps({
        'total': len(candidates_data['candidates']),
        'cached': len(candidates_data['candidates']) - len(uncached),
        'needs_processing': len(uncached),
        'candidates': uncached
    }, indent=2))
