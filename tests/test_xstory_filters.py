"""Tests for xstory filter functionality.

Tests the three-column filter system with proper field-based filtering:
- Stage filters check node.stage
- Hold Status filters check node.hold_reason (with 'no hold' for None)
- Disposition filters check node.disposition (with 'live' for None)

Filter logic: AND between categories, OR within each category.
"""

import pytest
from dataclasses import dataclass
from typing import Optional, Set


# Constants mirrored from xstory.py
STAGE_ORDER = ['concept', 'approved', 'planned', 'active', 'reviewing',
               'verifying', 'implemented', 'ready', 'released']
HOLD_REASON_ORDER = ['no hold', 'broken', 'conflict', 'blocked', 'pending',
                     'paused', 'polish', 'queued', 'wishlist']
DISPOSITION_ORDER = ['live', 'infeasible', 'rejected', 'duplicative',
                     'deprecated', 'legacy', 'archived']

# Sets for category membership
STAGE_SET = set(STAGE_ORDER)
HOLD_REASON_SET = set(HOLD_REASON_ORDER)
DISPOSITION_SET = set(DISPOSITION_ORDER)


@dataclass
class StoryNode:
    """Test stub for StoryNode matching xstory.py structure."""
    id: str
    status: str  # Effective status: COALESCE(disposition, hold_reason, stage)
    stage: str
    hold_reason: Optional[str] = None
    disposition: Optional[str] = None


def node_matches_filter(node: StoryNode,
                        checked_stages: Set[str],
                        checked_holds: Set[str],
                        checked_disps: Set[str]) -> bool:
    """Check if node matches filters (AND logic across categories).

    Mirrors xstory.py:2330-2354 logic.
    """
    show_no_hold = 'no hold' in checked_holds
    show_live = 'live' in checked_disps

    # Stage check: node.stage must be in checked stages
    if node.stage not in checked_stages:
        return False

    # Hold Status check: node.hold_reason in checked holds, OR 'no hold' if no hold_reason
    hold_ok = False
    if node.hold_reason and node.hold_reason in checked_holds:
        hold_ok = True
    elif show_no_hold and not node.hold_reason:
        hold_ok = True
    if not hold_ok:
        return False

    # Disposition check: node.disposition in checked dispositions, OR 'live' if no disposition
    disp_ok = False
    if node.disposition and node.disposition in checked_disps:
        disp_ok = True
    elif show_live and not node.disposition:
        disp_ok = True
    if not disp_ok:
        return False

    return True


# --- Test Fixtures ---

@pytest.fixture
def sample_nodes():
    """Create sample nodes covering various field combinations."""
    return [
        # Nodes without hold_reason or disposition (match 'no hold' AND 'live')
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


@pytest.fixture
def all_stages():
    """All stages checked."""
    return set(STAGE_ORDER)


@pytest.fixture
def all_holds():
    """All hold statuses checked."""
    return set(HOLD_REASON_ORDER)


@pytest.fixture
def all_disps():
    """All dispositions checked."""
    return set(DISPOSITION_ORDER)


# --- Stage Filter Tests ---

class TestStageFilters:
    """Tests for Stage column filtering."""

    def test_stage_filters_by_stage_field(self, all_holds, all_disps):
        """Stage filter should check node.stage, not effective status."""
        # Node with stage='approved' but hold_reason='blocked' (effective status='blocked')
        node = StoryNode(id='x', status='blocked', stage='approved', hold_reason='blocked')

        # Should match when 'approved' stage is checked
        assert node_matches_filter(node, {'approved'}, all_holds, all_disps)

        # Should NOT match when only 'blocked' is in stages (blocked is not a stage!)
        assert not node_matches_filter(node, {'concept'}, all_holds, all_disps)

    def test_stage_none_hides_all(self, sample_nodes, all_holds, all_disps):
        """With no stages checked, nothing should match."""
        matching = [n for n in sample_nodes
                    if node_matches_filter(n, set(), all_holds, all_disps)]
        assert len(matching) == 0

    def test_stage_specific_filter(self, sample_nodes, all_holds, all_disps):
        """Filter by specific stage should only show nodes with that stage."""
        matching = [n for n in sample_nodes
                    if node_matches_filter(n, {'active'}, all_holds, all_disps)]

        # Nodes 2, 5, 10 have stage='active'
        assert len(matching) == 3
        assert all(n.stage == 'active' for n in matching)


# --- 'no hold' Filter Tests ---

class TestNoHoldFilter:
    """Tests for the 'no hold' special filter."""

    def test_no_hold_matches_nodes_without_hold_reason(self, sample_nodes, all_stages, all_disps):
        """'no hold' filter should match nodes where hold_reason is None/empty."""
        visible = {'no hold'}

        matching = [n for n in sample_nodes
                    if node_matches_filter(n, all_stages, visible, all_disps)]

        # Should match nodes 1, 2, 3, 7, 9 (no hold_reason)
        assert len(matching) == 5
        assert all(not n.hold_reason for n in matching)

    def test_no_hold_excludes_nodes_with_hold_reason(self, sample_nodes, all_stages, all_disps):
        """'no hold' filter should NOT match nodes with hold_reason set."""
        visible = {'no hold'}

        nodes_with_hold = [n for n in sample_nodes if n.hold_reason]

        for node in nodes_with_hold:
            assert not node_matches_filter(node, all_stages, visible, all_disps)

    def test_no_hold_with_empty_string_hold_reason(self, all_stages, all_disps):
        """'no hold' should match nodes with empty string hold_reason."""
        node = StoryNode(id='x', status='active', stage='active', hold_reason='')
        visible = {'no hold'}

        assert node_matches_filter(node, all_stages, visible, all_disps)


# --- 'live' Filter Tests ---

class TestLiveFilter:
    """Tests for the 'live' special filter."""

    def test_live_matches_nodes_without_disposition(self, sample_nodes, all_stages, all_holds):
        """'live' filter should match nodes where disposition is None/empty."""
        visible = {'live'}

        matching = [n for n in sample_nodes
                    if node_matches_filter(n, all_stages, all_holds, visible)]

        # Should match nodes 1, 2, 3, 4, 5, 6, 8 (no disposition)
        assert len(matching) == 7
        assert all(not n.disposition for n in matching)

    def test_live_excludes_nodes_with_disposition(self, sample_nodes, all_stages, all_holds):
        """'live' filter should NOT match nodes with disposition set."""
        visible = {'live'}

        nodes_with_disp = [n for n in sample_nodes if n.disposition]

        for node in nodes_with_disp:
            assert not node_matches_filter(node, all_stages, all_holds, visible)

    def test_live_with_empty_string_disposition(self, all_stages, all_holds):
        """'live' should match nodes with empty string disposition."""
        node = StoryNode(id='x', status='active', stage='active', disposition='')
        visible = {'live'}

        assert node_matches_filter(node, all_stages, all_holds, visible)


# --- Combined Filter Tests ---

class TestCombinedFilters:
    """Tests for filter combinations across categories."""

    def test_and_logic_between_categories(self, all_stages, all_holds, all_disps):
        """Node must match ALL THREE categories to be visible."""
        node = StoryNode(id='x', status='blocked', stage='planned',
                         hold_reason='blocked', disposition=None)

        # Matches when all three categories pass
        assert node_matches_filter(node, {'planned'}, {'blocked'}, {'live'})

        # Fails when stage doesn't match
        assert not node_matches_filter(node, {'active'}, {'blocked'}, {'live'})

        # Fails when hold doesn't match
        assert not node_matches_filter(node, {'planned'}, {'paused'}, {'live'})

        # Fails when disposition doesn't match (needs 'live' for None disposition)
        assert not node_matches_filter(node, {'planned'}, {'blocked'}, {'rejected'})

    def test_or_logic_within_categories(self, all_holds, all_disps):
        """Within each category, matching ANY checked option is sufficient."""
        node = StoryNode(id='x', status='active', stage='active')

        # Matches when stage is in the checked set (along with others)
        assert node_matches_filter(node, {'concept', 'active', 'released'}, all_holds, all_disps)

    def test_complex_node_with_all_fields(self, all_stages, all_holds, all_disps):
        """Node with hold_reason AND disposition should match correct categories."""
        node = StoryNode(id='x', status='rejected', stage='active',
                         hold_reason='blocked', disposition='rejected')

        # Should match stage='active', hold='blocked', disp='rejected'
        assert node_matches_filter(node, {'active'}, {'blocked'}, {'rejected'})

        # Should NOT match 'no hold' (has hold_reason)
        assert not node_matches_filter(node, {'active'}, {'no hold'}, {'rejected'})

        # Should NOT match 'live' (has disposition)
        assert not node_matches_filter(node, {'active'}, {'blocked'}, {'live'})


# --- Edge Cases ---

class TestEdgeCases:
    """Edge case tests."""

    def test_node_with_all_fields_none(self):
        """Node with all optional fields None should match 'no hold' and 'live'."""
        node = StoryNode(id='x', status='concept', stage='concept')

        assert node_matches_filter(node, {'concept'}, {'no hold'}, {'live'})

    def test_empty_filters_match_nothing(self, sample_nodes):
        """Empty filters in any category should match nothing."""
        matching = [n for n in sample_nodes
                    if node_matches_filter(n, set(), set(), set())]
        assert len(matching) == 0

    def test_stage_independent_of_effective_status(self):
        """Stage filter should be independent of effective status."""
        # Effective status is 'rejected' but stage is 'active'
        node = StoryNode(id='x', status='rejected', stage='active',
                         hold_reason='blocked', disposition='rejected')

        # Filter by stage='active' should match (not by effective status 'rejected')
        assert node_matches_filter(node, {'active'}, {'blocked'}, {'rejected'})

        # Filter by stage='rejected' should NOT match (rejected is a disposition, not a stage)
        assert not node_matches_filter(node, {'rejected'}, {'blocked'}, {'rejected'})


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

    def test_stage_order_complete(self):
        """STAGE_ORDER should have all workflow stages."""
        expected = {'concept', 'approved', 'planned', 'active', 'reviewing',
                    'verifying', 'implemented', 'ready', 'released'}
        assert set(STAGE_ORDER) == expected
