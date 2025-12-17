-- Story Tree SQLite Schema v3.1.0
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
            'pending', 'approved', 'planned', 'queued', 'paused',
            'active',
            'reviewing', 'verifying', 'implemented',
            'ready', 'polish', 'released',
            'legacy', 'deprecated', 'archived'
        )),
    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    version INTEGER DEFAULT 1  -- v3.1: For vetting cache invalidation
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

-- v3.1: Vetting decisions cache for Entity Resolution
-- Stores LLM classification decisions to avoid repeated analysis
CREATE TABLE IF NOT EXISTS vetting_decisions (
    pair_key TEXT PRIMARY KEY,  -- Canonical: smaller_id|larger_id
    story_a_id TEXT NOT NULL,
    story_a_version INTEGER NOT NULL,
    story_b_id TEXT NOT NULL,
    story_b_version INTEGER NOT NULL,
    classification TEXT NOT NULL CHECK (classification IN (
        'duplicate', 'scope_overlap', 'competing',
        'incompatible', 'false_positive'
    )),
    action_taken TEXT CHECK (action_taken IN (
        'SKIP', 'DELETE_CONCEPT', 'REJECT_CONCEPT', 'BLOCK_CONCEPT',
        'TRUE_MERGE', 'PICK_BETTER', 'HUMAN_REVIEW', 'DEFER_PENDING'
    )),
    decided_at TEXT NOT NULL,
    FOREIGN KEY (story_a_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (story_b_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON story_nodes(status);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);
CREATE INDEX IF NOT EXISTS idx_vetting_story_a ON vetting_decisions(story_a_id);
CREATE INDEX IF NOT EXISTS idx_vetting_story_b ON vetting_decisions(story_b_id);

CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;
