-- Story Tree SQLite Schema v4.0.0 (Three-Field System)
-- Location: .claude/data/story-tree.db

-- ID Format: Root="root", Level 1="1","2","3", Level 2+="1.1","1.3.2"

CREATE TABLE IF NOT EXISTS story_nodes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    capacity INTEGER,  -- NULL = dynamic: 3 + implemented/ready children

    -- Three-field workflow system (v4.0)
    -- Replaces single 'status' column with orthogonal dimensions
    stage TEXT NOT NULL DEFAULT 'concept'
        CHECK (stage IN (
            'concept', 'approved', 'planned', 'active',
            'reviewing', 'verifying', 'implemented', 'ready', 'polish', 'released'
        )),
    hold_reason TEXT DEFAULT NULL
        CHECK (hold_reason IS NULL OR hold_reason IN (
            'queued', 'pending', 'paused', 'blocked', 'broken', 'polish', 'conflict', 'wishlist'
        )),
    disposition TEXT DEFAULT NULL
        CHECK (disposition IS NULL OR disposition IN (
            'rejected', 'infeasible', 'duplicative', 'legacy', 'deprecated', 'archived'
        )),
    human_review INTEGER DEFAULT 0
        CHECK (human_review IN (0, 1)),

    project_path TEXT,
    last_implemented TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    version INTEGER DEFAULT 1  -- For vetting cache invalidation
);

-- Constraint: Cannot be both held AND disposed (mutually exclusive)
-- Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT, enforced in app logic

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

-- Vetting decisions cache for Entity Resolution
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
        'SKIP', 'DELETE_CONCEPT', 'REJECT_CONCEPT', 'DUPLICATIVE_CONCEPT',
        'BLOCK_CONCEPT', 'TRUE_MERGE', 'PICK_BETTER', 'HUMAN_REVIEW', 'DEFER_PENDING'
    )),
    decided_at TEXT NOT NULL,
    FOREIGN KEY (story_a_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (story_b_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_paths_descendant ON story_paths(descendant_id);
CREATE INDEX IF NOT EXISTS idx_paths_depth ON story_paths(depth);
CREATE INDEX IF NOT EXISTS idx_commits_hash ON story_commits(commit_hash);
CREATE INDEX IF NOT EXISTS idx_vetting_story_a ON vetting_decisions(story_a_id);
CREATE INDEX IF NOT EXISTS idx_vetting_story_b ON vetting_decisions(story_b_id);

-- Three-field system indexes (v4.0)
CREATE INDEX IF NOT EXISTS idx_active_pipeline ON story_nodes(stage)
    WHERE disposition IS NULL AND hold_reason IS NULL;
CREATE INDEX IF NOT EXISTS idx_held_stories ON story_nodes(hold_reason)
    WHERE hold_reason IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_disposed_stories ON story_nodes(disposition)
    WHERE disposition IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_needs_review ON story_nodes(human_review)
    WHERE human_review = 1;

-- Triggers
CREATE TRIGGER IF NOT EXISTS story_nodes_updated_at
AFTER UPDATE ON story_nodes
FOR EACH ROW
BEGIN
    UPDATE story_nodes SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =============================================================================
-- THREE-FIELD SYSTEM REFERENCE
-- =============================================================================
--
-- STAGE (10 values): Linear workflow position
--   concept → approved → planned → active → reviewing → verifying
--   → implemented → ready → polish → released
--
-- HOLD_REASON (8 values + NULL): Why work is stopped (orthogonal to stage)
--   NULL     = Not held, work can proceed
--   queued   = Waiting for automated processing (algorithm hasn't run yet)
--   pending  = Awaiting human decision (algorithm ran but can't decide)
--   paused   = Execution blocked by critical issue
--   blocked  = External dependency
--   broken   = Something wrong with story definition
--   polish   = Needs refinement before proceeding
--   conflict = Inconsistent with another story, needs human resolution
--   wishlist = Indefinite hold, maybe someday (can be revived when priorities change)
--
-- DISPOSITION (6 values + NULL): Terminal state (exits pipeline)
--   NULL        = Active in pipeline
--   rejected    = Human decided not to implement (indicates non-goal)
--   infeasible  = Cannot implement
--   duplicative = Algorithm detected duplicate/overlap with existing story (not a goal signal)
--   legacy      = Old but functional (released only)
--   deprecated  = Being phased out (released only)
--   archived    = No longer relevant
--
-- HUMAN_REVIEW: Boolean flag for items needing human attention
--   Typically TRUE when hold_reason IS NOT NULL
--
-- VALID COMBINATIONS:
--   - disposition IS NOT NULL → Story has exited pipeline (stage preserved)
--   - hold_reason IS NOT NULL → Work stopped, but stage shows where to resume
--   - Both NULL → Active in pipeline at given stage
--   - Cannot have BOTH hold_reason AND disposition (mutually exclusive)
-- =============================================================================
