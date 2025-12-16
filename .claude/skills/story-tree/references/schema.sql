-- Story Tree SQLite Schema v3.0.0
-- Location: .claude/data/story-tree.db

-- ID Format: Root="root", Level 1="1","2","3", Level 2+="1.1","1.3.2"

CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,  -- NULL = dynamic: 3 + implemented/ready children
    status TEXT NOT NULL DEFAULT 'concept'
        CHECK (status IN (
            'infeasible', 'rejected', 'wishlist',
            'concept', 'broken', 'blocked', 'refine',
            'deferred', 'approved', 'planned', 'queued', 'paused',
            'active',
            'reviewing', 'implemented',
            'ready', 'polish', 'released',
            'legacy', 'deprecated', 'archived'
        )),
    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Closure table: ALL ancestor-descendant paths
CREATE TABLE IF NOT EXISTS story_paths (
    ancestor_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    descendant_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,  -- 0=self, 1=parent/child, 2=grandparent
    PRIMARY KEY (ancestor_id, descendant_id)
);

CREATE TABLE IF NOT EXISTS story_commits (
    story_id TEXT NOT NULL REFERENCES story_nodes(id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    commit_date TEXT,
    commit_message TEXT,
    PRIMARY KEY (story_id, commit_hash)
);

-- Metadata keys: version, lastUpdated, lastAnalyzedCommit
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);

CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;
