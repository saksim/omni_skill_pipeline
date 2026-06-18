CREATE TABLE ingest_jobs (
    job_id UUID PRIMARY KEY,
    modality TEXT NOT NULL,
    status TEXT NOT NULL,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE assets (
    asset_id UUID PRIMARY KEY,
    job_id UUID REFERENCES ingest_jobs(job_id) ON DELETE SET NULL,
    modality TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE evidence_units (
    evidence_id UUID PRIMARY KEY,
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL,
    span_ref TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content TEXT NOT NULL,
    speaker TEXT,
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.000,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (asset_id, sequence_no)
);

CREATE INDEX idx_evidence_units_asset_id ON evidence_units(asset_id);
CREATE INDEX idx_evidence_units_content_type ON evidence_units(content_type);

CREATE TABLE insights (
    insight_id UUID PRIMARY KEY,
    job_id UUID REFERENCES ingest_jobs(job_id) ON DELETE SET NULL,
    insight_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_insights_job_id ON insights(job_id);
CREATE INDEX idx_insights_type ON insights(insight_type);

CREATE TABLE skills (
    skill_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    skill_type TEXT NOT NULL,
    goal TEXT NOT NULL,
    audience TEXT NOT NULL,
    source_modality TEXT NOT NULL,
    current_version TEXT NOT NULL DEFAULT '0.1.0',
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.000,
    review_status TEXT NOT NULL DEFAULT 'draft',
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_review_status ON skills(review_status);

CREATE TABLE skill_versions (
    version_id UUID PRIMARY KEY,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    skill_body JSONB NOT NULL,
    markdown_body TEXT NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (skill_id, version)
);

CREATE INDEX idx_skill_versions_skill_id ON skill_versions(skill_id);

CREATE TABLE publications (
    publication_id UUID PRIMARY KEY,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    publication_type TEXT NOT NULL,
    path TEXT,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_publications_skill_id ON publications(skill_id);
CREATE INDEX idx_publications_type ON publications(publication_type);

CREATE TABLE review_tasks (
    review_task_id UUID PRIMARY KEY,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    decision TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'review_pending',
    reason_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    revision_suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    score_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    thresholds JSONB NOT NULL DEFAULT '{}'::jsonb,
    review_notes TEXT NOT NULL DEFAULT '',
    queue_status TEXT NOT NULL DEFAULT 'pending',
    claimed_by TEXT,
    claimed_at TIMESTAMPTZ,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_review_tasks_skill_id ON review_tasks(skill_id);
CREATE INDEX idx_review_tasks_status ON review_tasks(status);
CREATE INDEX idx_review_tasks_queue_status ON review_tasks(queue_status);

CREATE TABLE lineage_links (
    lineage_link_id UUID PRIMARY KEY,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    related_skill_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.000,
    reason TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (skill_id, related_skill_id, relation_type)
);

CREATE INDEX idx_lineage_links_skill_id ON lineage_links(skill_id);
CREATE INDEX idx_lineage_links_related_skill_id ON lineage_links(related_skill_id);
CREATE INDEX idx_lineage_links_relation_type ON lineage_links(relation_type);

CREATE TABLE tenant_scopes (
    scope_id UUID PRIMARY KEY,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE UNIQUE,
    organization_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT,
    api_key_id TEXT,
    source TEXT NOT NULL DEFAULT 'request_metadata',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenant_scopes_org_project ON tenant_scopes(organization_id, project_id);
