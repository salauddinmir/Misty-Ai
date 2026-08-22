-- MISTY Brain Database Schema (PostgreSQL dialect)
-- Used when MISTY_DB_URL points at a PostgreSQL server (e.g. Supabase).
-- Semantically identical to schema.sql; SQLite-specific syntax replaced.

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

-- Brain states table: stores snapshots of brain state for analysis.
-- PostgreSQL has no AUTOINCREMENT: a SERIAL column is used instead.
CREATE TABLE IF NOT EXISTS brain_states (
    state_id SERIAL PRIMARY KEY,
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
    languages JSONB NOT NULL DEFAULT '[]',
    package_json JSONB NOT NULL DEFAULT '{}',
    provenance TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    registered_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL,
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
    memory_json JSONB NOT NULL DEFAULT '{}',
    updated_at DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, memory_kind, memory_key)
);
CREATE INDEX IF NOT EXISTS idx_user_memory_user ON misty_user_memory(user_id);

-- Phase 46: durable semantic fact store with timestamps.
CREATE TABLE IF NOT EXISTS misty_facts (
    fact_key TEXT NOT NULL,              -- subject:predicate:obj
    subject TEXT NOT NULL DEFAULT '',
    predicate TEXT NOT NULL DEFAULT '',
    obj TEXT NOT NULL DEFAULT '',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    source TEXT NOT NULL DEFAULT 'user_input',
    created_at DOUBLE PRECISION NOT NULL,
    accessed_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (fact_key)
);
CREATE INDEX IF NOT EXISTS idx_facts_source ON misty_facts(source);
CREATE INDEX IF NOT EXISTS idx_facts_confidence ON misty_facts(confidence);

-- Phase 46: bounded audit log for aging and consolidation decisions.
CREATE TABLE IF NOT EXISTS misty_audit_log (
    id BIGSERIAL PRIMARY KEY,
    audit_kind TEXT NOT NULL,            -- 'aging' | 'consolidation'
    fact_key TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL DEFAULT '',     -- decayed | pruned | protected | rehearsed | merged_winner | merged_loser | quarantine_removed
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    detail TEXT NOT NULL DEFAULT '',
    created_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_kind ON misty_audit_log(audit_kind);
CREATE INDEX IF NOT EXISTS idx_audit_created ON misty_audit_log(created_at);
