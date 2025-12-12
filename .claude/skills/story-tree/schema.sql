-- Story Tree SQLite Schema
-- Version: 2.4.0
-- Uses closure table pattern for hierarchical data

-- Main story nodes table
CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,  -- Optional override; if NULL, use dynamic: 3 + implemented/ready children
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN ('concept','approved','rejected','planned','queued','active','in-progress','bugged','implemented','ready','deprecated','infeasible')),
    project_path TEXT,
    last_implemented TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Closure table for tree relationships
-- Stores ALL ancestor-descendant paths, not just parent-child
-- This enables efficient subtree queries without recursion
CREATE TABLE IF NOT EXISTS story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);

-- Git commits linked to stories
CREATE TABLE IF NOT EXISTS story_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);

-- Key-value metadata storage
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);

-- Triggers to maintain updated_at
CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =============================================================================
-- CRITICAL QUERIES
-- =============================================================================

-- QUERY 1: Priority algorithm (find under-capacity nodes, shallower first)
-- Uses dynamic capacity: COALESCE(capacity, 3 + implemented/ready children)
-- Excludes: concept, rejected, deprecated, infeasible, bugged
--
-- SELECT s.*,
--     (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
--     (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
--     COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
--          JOIN story_nodes child ON sp.descendant_id = child.id
--          WHERE sp.ancestor_id = s.id AND sp.depth = 1
--          AND child.status IN ('implemented', 'ready'))) as effective_capacity
-- FROM story_nodes s
-- WHERE s.status NOT IN ('concept', 'rejected', 'deprecated', 'infeasible', 'bugged')
--   AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
--       COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
--            JOIN story_nodes child ON sp.descendant_id = child.id
--            WHERE sp.ancestor_id = s.id AND sp.depth = 1
--            AND child.status IN ('implemented', 'ready')))
-- ORDER BY node_depth ASC
-- LIMIT 1;

-- QUERY 2: Get all children of a node (direct children only)
--
-- SELECT s.* FROM story_nodes s
-- JOIN story_paths st ON s.id = st.descendant_id
-- WHERE st.ancestor_id = :parent_id AND st.depth = 1;

-- QUERY 3: Get entire subtree of a node
--
-- SELECT s.*, st.depth as relative_depth FROM story_nodes s
-- JOIN story_paths st ON s.id = st.descendant_id
-- WHERE st.ancestor_id = :root_id
-- ORDER BY st.depth;

-- QUERY 4: Get ancestors of a node (path from root)
--
-- SELECT s.*, st.depth as distance FROM story_nodes s
-- JOIN story_paths st ON s.id = st.ancestor_id
-- WHERE st.descendant_id = :node_id
-- ORDER BY st.depth DESC;

-- QUERY 5: Get parent of a node
--
-- SELECT s.* FROM story_nodes s
-- JOIN story_paths st ON s.id = st.ancestor_id
-- WHERE st.descendant_id = :node_id AND st.depth = 1;

-- =============================================================================
-- INSERT OPERATIONS
-- =============================================================================

-- INSERT: Add a new node to the tree
-- Step 1: Insert into story_nodes table (capacity NULL = use dynamic)
-- Step 2: Populate closure table with self-reference + all ancestor paths
--
-- INSERT INTO story_nodes (id, title, description, status)
-- VALUES (:new_id, :title, :description, 'concept');
--
-- INSERT INTO story_paths (ancestor_id, descendant_id, depth)
-- SELECT ancestor_id, :new_id, depth + 1
-- FROM story_paths WHERE descendant_id = :parent_id
-- UNION ALL SELECT :new_id, :new_id, 0;

-- =============================================================================
-- DELETE OPERATIONS
-- =============================================================================

-- DELETE: Remove a node and all descendants
-- With ON DELETE CASCADE, deleting from story_nodes automatically cleans story_paths
--
-- DELETE FROM story_nodes WHERE id IN (
--     SELECT descendant_id FROM story_paths WHERE ancestor_id = :node_id
-- );

-- =============================================================================
-- TREE STATISTICS
-- =============================================================================

-- STATS: Count nodes by status
--
-- SELECT status, COUNT(*) as count FROM story_nodes GROUP BY status;

-- STATS: Count nodes by depth
--
-- SELECT
--     (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
--     COUNT(*) as count
-- FROM story_nodes s
-- GROUP BY node_depth;

-- STATS: Total effective capacity vs actual children per level
-- Uses dynamic capacity when no override is set
--
-- SELECT
--     node_depth,
--     SUM(effective_capacity) as total_capacity,
--     SUM(child_count) as total_children
-- FROM (
--     SELECT
--         s.id,
--         COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
--              JOIN story_nodes child ON sp.descendant_id = child.id
--              WHERE sp.ancestor_id = s.id AND sp.depth = 1
--              AND child.status IN ('implemented', 'ready'))) as effective_capacity,
--         (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
--         (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count
--     FROM story_nodes s
-- ) sub
-- GROUP BY node_depth;
