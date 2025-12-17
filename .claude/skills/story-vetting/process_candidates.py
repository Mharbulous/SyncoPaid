#!/usr/bin/env python3
"""
Process vetting candidates systematically with caching support.
"""
import sqlite3
import json
import sys

def get_cached_decision(conn, id_a, id_b):
    """Check if decision is cached for this pair."""
    # Normalize pair key (smaller ID first)
    if id_a > id_b:
        id_a, id_b = id_b, id_a
    pair_key = f"{id_a}|{id_b}"

    cursor = conn.execute("""
        SELECT classification, action_taken, decided_at, story_a_version, story_b_version
        FROM vetting_decisions
        WHERE pair_key = ?
    """, (pair_key,))
    return cursor.fetchone()

def get_story_version(conn, story_id):
    """Get current version of a story."""
    cursor = conn.execute("SELECT version FROM story_nodes WHERE id = ?", (story_id,))
    result = cursor.fetchone()
    return result[0] if result else 1

def cache_decision(conn, id_a, id_b, classification, action):
    """Cache a vetting decision."""
    # Normalize pair key (smaller ID first)
    if id_a > id_b:
        id_a, id_b = id_b, id_a
    pair_key = f"{id_a}|{id_b}"

    version_a = get_story_version(conn, id_a)
    version_b = get_story_version(conn, id_b)

    conn.execute("""
        INSERT OR REPLACE INTO vetting_decisions
        (pair_key, story_a_id, story_b_id, story_a_version, story_b_version, classification, action_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pair_key, id_a, id_b, version_a, version_b, classification, action))
    conn.commit()

def filter_uncached_candidates(candidates_json):
    """Filter candidates to only those not in cache or with stale versions."""
    conn = sqlite3.connect('.claude/data/story-tree.db')

    needs_processing = []
    cache_hits = 0

    for candidate in candidates_json['candidates']:
        id_a = candidate['story_a']['id']
        id_b = candidate['story_b']['id']

        cached = get_cached_decision(conn, id_a, id_b)
        if cached:
            # Check if versions match
            version_a = get_story_version(conn, id_a)
            version_b = get_story_version(conn, id_b)

            if cached[3] == version_a and cached[4] == version_b:
                # Cache hit - valid decision
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
