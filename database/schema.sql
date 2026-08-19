-- MISTY Brain Database Schema
-- Phase 0: SQLite

-- Concepts table: stores nodes in the knowledge graph
CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    concept_type TEXT NOT NULL DEFAULT 'generic',
    activation_level REAL DEFAULT 0.0,
    created_at REAL NOT NULL,
    metadata TEXT DEFAULT '{}',
    UNIQUE(name)
);

-- Relations table: stores edges in the knowledge graph
CREATE TABLE IF NOT EXISTS relations (
    relation_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    confidence REAL DEFAULT 1.0,
    created_at REAL NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (source_id) REFERENCES concepts(concept_id),
    FOREIGN KEY (target_id) REFERENCES concepts(concept_id)
);

-- Episodes table: stores episodic memories
CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    context TEXT DEFAULT '{}',
    timestamp REAL NOT NULL,
    emotional_valence REAL DEFAULT 0.0,
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0
);

-- Brain states table: stores snapshots of brain state for analysis
CREATE TABLE IF NOT EXISTS brain_states (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_count INTEGER NOT NULL,
    current_phase TEXT NOT NULL,
    active_concepts TEXT DEFAULT '{}',
    emotional_state TEXT DEFAULT '{}',
    last_input TEXT DEFAULT '',
    last_output TEXT DEFAULT '',
    timestamp REAL NOT NULL
);

-- Procedures table: stores learned procedural rules (Phase 2)
CREATE TABLE IF NOT EXISTS procedures (
    procedure_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    use_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

-- Training packages table (Phase 12): durable catalog of versioned
-- structured knowledge packages registered through the training registry.
CREATE TABLE IF NOT EXISTS training_packages (
    package_id TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    department TEXT NOT NULL DEFAULT 'general',
    languages TEXT DEFAULT '[]',
    package_json TEXT NOT NULL DEFAULT '{}',
    provenance TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    registered_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (package_id, version)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
CREATE INDEX IF NOT EXISTS idx_concepts_type ON concepts(concept_type);
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_episodes_timestamp ON episodes(timestamp);
CREATE INDEX IF NOT EXISTS idx_brain_states_timestamp ON brain_states(timestamp);
CREATE INDEX IF NOT EXISTS idx_procedures_name ON procedures(name);

-- Phase 40: per-user long-term memory and personalization.
CREATE TABLE IF NOT EXISTS misty_user_memory (
    user_id TEXT NOT NULL,
    memory_kind TEXT NOT NULL,           -- 'profile' | 'fact' | 'episode'
    memory_key TEXT NOT NULL DEFAULT '', -- fact_id / episode_id / 'profile'
    memory_json TEXT NOT NULL DEFAULT '{}',
    updated_at REAL NOT NULL,
    PRIMARY KEY (user_id, memory_kind, memory_key)
);
CREATE INDEX IF NOT EXISTS idx_user_memory_user ON misty_user_memory(user_id);
