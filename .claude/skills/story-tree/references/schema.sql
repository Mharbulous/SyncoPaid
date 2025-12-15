-- Story Tree SQLite Schema
-- Version: 3.0.0
-- Pattern: Closure table for hierarchical data
-- Location: .claude/data/story-tree.db

--------------------------------------------------------------------------------
-- STORY_NODES: Main table storing all story data
--------------------------------------------------------------------------------
-- ID Format:
--   Root: "root"
--   Level 1: "1", "2", "3", etc.
--   Level 2+: Parent.N (e.g., "1.1", "1.3.2")
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,  -- NULL = dynamic: 3 + implemented/ready children
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN (
            -- Red Zone (Can't/Won't)
            'infeasible',   -- Cannot be built
            'rejected',     -- Human rejected
            'wishlist',     -- Rejected for now, may reconsider later
            -- Orange-Yellow Zone (Concept & Broken)
            'concept',      -- Idea, not yet approved
            'broken',       -- Needs debugging (major bug, non-functional)
            'blocked',      -- Planned but blocked by external dependencies
            'refine',       -- Concept needs rework before approval
            -- Yellow Zone (Planning)
            'deferred',     -- Approved but intentionally postponed
            'approved',     -- Human approved, not yet planned
            'planned',      -- Implementation plan created
            'queued',       -- Ready, dependencies met
            'paused',       -- Was active but temporarily on hold
            -- Green Zone (Development)
            'active',       -- Currently being worked on
            -- Cyan-Blue Zone (Testing)
            'reviewing',    -- Implemented, under review/testing
            'implemented',  -- Complete/done
            -- Blue Zone (Production)
            'ready',        -- Production ready, tested
            'polish',       -- Final refinements before release
            'released',     -- Deployed to production
            -- Violet Zone (Post-Production/End-of-Life)
            'legacy',       -- Superseded, still works, dependencies need checking
            'deprecated',   -- Dependencies checked, ready for removal
            'archived'      -- Removed from production
        )),
    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,  -- Freeform notes (rejection reasons, context, constraints, etc.)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

--------------------------------------------------------------------------------
-- STORY_PATHS: Closure table storing ALL ancestor-descendant relationships
--------------------------------------------------------------------------------
-- Benefits:
--   - Get entire subtree in single query (no recursion)
--   - Get all ancestors in single query
--   - O(1) depth calculation
-- Trade-off:
--   - More storage: O(n*depth) rows
--   - Inserts require populating all ancestor paths
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,  -- 0 = self, 1 = parent/child, 2 = grandparent, etc.
    PRIMARY KEY (ancestor_id, descendant_id)
);

--------------------------------------------------------------------------------
-- STORY_COMMITS: Links git commits to stories for implementation tracking
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS story_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);

--------------------------------------------------------------------------------
-- METADATA: Key-value storage for tree-level data
--------------------------------------------------------------------------------
-- Standard keys:
--   version          - Schema version (e.g., "2.4.0")
--   lastUpdated      - Last tree update timestamp
--   lastAnalyzedCommit - Checkpoint for incremental git analysis
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

--------------------------------------------------------------------------------
-- INDEXES
--------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);

--------------------------------------------------------------------------------
-- TRIGGERS
--------------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;
