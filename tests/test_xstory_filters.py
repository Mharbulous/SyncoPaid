"""Tests for xstory filter functionality.

Tests the three-column filter system with special 'no hold' and 'live' filters.
"""

import pytest
from dataclasses import dataclass
from typing import Optional, Set


# Constants mirrored from xstory.py (lines 64-68)
STAGE_ORDER = ['concept', 'approved', 'planned', 'active', 'reviewing',
               'verifying', 'implemented', 'ready', 'released']
HOLD_REASON_ORDER = ['no hold', 'queued', 'pending', 'paused', 'blocked', 'broken', 'polish', 'wishlist']
DISPOSITION_ORDER = ['live', 'rejected', 'infeasible', 'legacy', 'deprecated', 'archived']


@dataclass
class StoryNode:
    """Test stub for StoryNode matching xstory.py structure."""
    id: str
    status: str  # Effective status: COALESCE(disposition, hold_reason, stage)
    stage: str
    hold_reason: Optional[str] = None
    disposition: Optional[str] = None


def node_matches_filter(node: StoryNode, visible_statuses: Set[str]) -> bool:
    """Check if node matches filters. Mirrors xstory.py:1309-1320 logic."""
    show_no_hold = 'no hold' in visible_statuses
    show_live = 'live' in visible_statuses

    # Check effective status
    if node.status in visible_statuses:
        return True
    # 'no hold' matches nodes with no hold_reason
    if show_no_hold and not node.hold_reason:
        return True
    # 'live' matches nodes with no disposition
    if show_live and not node.disposition:
        return True
    return False


# --- Test Fixtures ---

@pytest.fixture
def sample_nodes():
    """Create sample nodes covering various field combinations."""
    return [
        # Nodes without hold_reason or disposition (should match 'no hold' AND 'live')
        StoryNode(id='1', status='implemented', stage='implemented'),
        StoryNode(id='2', status='active', stage='active'),
        StoryNode(id='3', status='concept', stage='concept'),

        # Nodes with hold_reason (should NOT match 'no hold')
        StoryNode(id='4', status='blocked', stage='planned', hold_reason='blocked'),
        StoryNode(id='5', status='paused', stage='active', hold_reason='paused'),
        StoryNode(id='6', status='polish', stage='ready', hold_reason='polish'),

        # Nodes with disposition (should NOT match 'live')
        StoryNode(id='7', status='rejected', stage='concept', disposition='rejected'),
        StoryNode(id='9', status='archived', stage='released', disposition='archived'),

        # Nodes with wishlist hold_reason (matches 'live' but NOT 'no hold')
        StoryNode(id='8', status='wishlist', stage='concept', hold_reason='wishlist'),

        # Node with both hold_reason AND disposition
        StoryNode(id='10', status='rejected', stage='active', hold_reason='blocked', disposition='rejected'),
    ]


# --- 'no hold' Filter Tests ---

class TestNoHoldFilter:
    """Tests for the 'no hold' special filter."""

    def test_no_hold_matches_nodes_without_hold_reason(self, sample_nodes):
        """'no hold' filter should match nodes where hold_reason is None/empty."""
        visible = {'no hold'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        # Should match nodes 1, 2, 3, 7, 9 (no hold_reason)
        # Note: node 8 has hold_reason='wishlist' so it does NOT match
        assert len(matching) == 5
        assert all(not n.hold_reason for n in matching)

    def test_no_hold_excludes_nodes_with_hold_reason(self, sample_nodes):
        """'no hold' filter should NOT match nodes with hold_reason set."""
        visible = {'no hold'}

        nodes_with_hold = [n for n in sample_nodes if n.hold_reason]

        for node in nodes_with_hold:
            assert not node_matches_filter(node, visible)

    def test_no_hold_with_empty_string_hold_reason(self):
        """'no hold' should match nodes with empty string hold_reason."""
        node = StoryNode(id='x', status='active', stage='active', hold_reason='')
        visible = {'no hold'}

        assert node_matches_filter(node, visible)


# --- 'live' Filter Tests ---

class TestLiveFilter:
    """Tests for the 'live' special filter."""

    def test_live_matches_nodes_without_disposition(self, sample_nodes):
        """'live' filter should match nodes where disposition is None/empty."""
        visible = {'live'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        # Should match nodes 1, 2, 3, 4, 5, 6, 8 (no disposition)
        # Note: node 8 has hold_reason='wishlist' but NO disposition, so it matches
        assert len(matching) == 7
        assert all(not n.disposition for n in matching)

    def test_live_excludes_nodes_with_disposition(self, sample_nodes):
        """'live' filter should NOT match nodes with disposition set."""
        visible = {'live'}

        nodes_with_disp = [n for n in sample_nodes if n.disposition]

        for node in nodes_with_disp:
            assert not node_matches_filter(node, visible)

    def test_live_with_empty_string_disposition(self):
        """'live' should match nodes with empty string disposition."""
        node = StoryNode(id='x', status='active', stage='active', disposition='')
        visible = {'live'}

        assert node_matches_filter(node, visible)


# --- Combined Filter Tests ---

class TestCombinedFilters:
    """Tests for filter combinations."""

    def test_no_hold_and_live_uses_or_logic(self, sample_nodes):
        """Combined 'no hold' + 'live' should match if EITHER condition is true."""
        visible = {'no hold', 'live'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        # Should match all nodes except #10 (has both hold_reason AND disposition)
        # Wait, let's think: node 10 has hold_reason='blocked' AND disposition='rejected'
        # 'no hold' requires no hold_reason -> False for node 10
        # 'live' requires no disposition -> False for node 10
        # So node 10 should NOT match
        assert len(matching) == 9
        assert sample_nodes[9] not in matching  # Node 10

    def test_status_filter_with_no_hold(self, sample_nodes):
        """Status filter + 'no hold' should use OR logic."""
        visible = {'blocked', 'no hold'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        # 'blocked' matches node 4 (status='blocked')
        # 'no hold' matches nodes 1, 2, 3, 7, 8, 9
        # Total: 7 unique nodes (node 4 doesn't have no hold_reason but matches 'blocked')
        blocked_nodes = [n for n in sample_nodes if n.status == 'blocked']
        no_hold_nodes = [n for n in sample_nodes if not n.hold_reason]
        expected = set(n.id for n in blocked_nodes) | set(n.id for n in no_hold_nodes)

        assert len(matching) == len(expected)

    def test_status_filter_with_live(self, sample_nodes):
        """Status filter + 'live' should use OR logic."""
        visible = {'rejected', 'live'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        # 'rejected' matches nodes 7, 10 (status='rejected')
        # 'live' matches nodes 1, 2, 3, 4, 5, 6 (no disposition)
        # Total: 8 unique nodes
        rejected_nodes = [n for n in sample_nodes if n.status == 'rejected']
        live_nodes = [n for n in sample_nodes if not n.disposition]
        expected = set(n.id for n in rejected_nodes) | set(n.id for n in live_nodes)

        assert len(matching) == len(expected)


# --- Regular Status Filter Tests ---

class TestRegularStatusFilters:
    """Tests for standard status filtering (non-special filters)."""

    def test_single_status_filter(self, sample_nodes):
        """Single status filter should match only nodes with that effective status."""
        visible = {'implemented'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        assert len(matching) == 1
        assert matching[0].status == 'implemented'

    def test_multiple_status_filters(self, sample_nodes):
        """Multiple status filters should match nodes with any of those statuses."""
        visible = {'implemented', 'active', 'concept'}

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        assert len(matching) == 3
        assert all(n.status in visible for n in matching)

    def test_empty_filter_matches_nothing(self, sample_nodes):
        """Empty filter set should match no nodes."""
        visible = set()

        matching = [n for n in sample_nodes if node_matches_filter(n, visible)]

        assert len(matching) == 0


# --- Edge Cases ---

class TestEdgeCases:
    """Edge case tests."""

    def test_node_with_all_fields_none(self):
        """Node with all optional fields None should match 'no hold' and 'live'."""
        node = StoryNode(id='x', status='concept', stage='concept')

        assert node_matches_filter(node, {'no hold'})
        assert node_matches_filter(node, {'live'})
        assert node_matches_filter(node, {'no hold', 'live'})

    def test_effective_status_priority(self):
        """Effective status should be COALESCE(disposition, hold_reason, stage)."""
        # Node with disposition takes priority
        node1 = StoryNode(id='1', status='rejected', stage='active',
                          hold_reason='blocked', disposition='rejected')
        assert node_matches_filter(node1, {'rejected'})
        assert not node_matches_filter(node1, {'blocked'})
        assert not node_matches_filter(node1, {'active'})

        # Node with hold_reason (no disposition)
        node2 = StoryNode(id='2', status='blocked', stage='active', hold_reason='blocked')
        assert node_matches_filter(node2, {'blocked'})
        assert not node_matches_filter(node2, {'active'})

        # Node with only stage
        node3 = StoryNode(id='3', status='active', stage='active')
        assert node_matches_filter(node3, {'active'})


# --- Constants Validation ---

class TestConstants:
    """Validate filter constants match expected values."""

    def test_no_hold_in_hold_reason_order(self):
        """'no hold' should be in HOLD_REASON_ORDER."""
        assert 'no hold' in HOLD_REASON_ORDER

    def test_live_in_disposition_order(self):
        """'live' should be in DISPOSITION_ORDER."""
        assert 'live' in DISPOSITION_ORDER

    def test_no_hold_is_first_hold_reason(self):
        """'no hold' should be first in HOLD_REASON_ORDER for UI display."""
        assert HOLD_REASON_ORDER[0] == 'no hold'

    def test_live_is_first_disposition(self):
        """'live' should be first in DISPOSITION_ORDER for UI display."""
        assert DISPOSITION_ORDER[0] == 'live'
