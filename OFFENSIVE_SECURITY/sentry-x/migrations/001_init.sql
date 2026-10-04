-- sentry-x schema v1
-- Idempotent: safe to re-run (IF NOT EXISTS everywhere).
-- Apply with: psql -U <user> -d <db> -f migrations/001_init.sql

BEGIN;

CREATE TABLE IF NOT EXISTS scan_sessions (
    id              SERIAL PRIMARY KEY,
    target          VARCHAR(255) NOT NULL,
    scan_date       TIMESTAMPTZ NOT NULL DEFAULT now(),
    status          VARCHAR(50) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'completed', 'failed', 'aborted')),
    authorized_by   VARCHAR(255),         -- who gave written authorization
    authorization_ref VARCHAR(255),       -- ticket/doc reference - no scan without this
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS tool_runs (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    tool_name       VARCHAR(50) NOT NULL,
    success         BOOLEAN NOT NULL,
    duration_seconds NUMERIC(10,3),
    raw_output      TEXT,
    error           TEXT,
    ran_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    vuln_name       TEXT NOT NULL,
    cve_id          VARCHAR(20),
    severity        VARCHAR(20) CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    cvss_score      NUMERIC(3,1),
    port            VARCHAR(20),
    service         VARCHAR(100),
    description     TEXT,
    source          VARCHAR(50) NOT NULL DEFAULT 'ai_analysis'
                        CHECK (source IN ('ai_analysis', 'nvd_lookup', 'manual')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fixes (
    id              SERIAL PRIMARY KEY,
    vulnerability_id INTEGER NOT NULL REFERENCES vulnerabilities(id) ON DELETE CASCADE,
    fix_text        TEXT NOT NULL,
    source          VARCHAR(50) NOT NULL DEFAULT 'ai_analysis',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_summaries (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    raw_scan_json   JSONB NOT NULL,
    ai_analysis     TEXT NOT NULL,
    risk_level      VARCHAR(20) CHECK (risk_level IN ('info', 'low', 'medium', 'high', 'critical')),
    model_used      VARCHAR(100),
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS api_usage (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES scan_sessions(id) ON DELETE SET NULL,
    model           VARCHAR(100) NOT NULL,
    input_tokens    INTEGER NOT NULL,
    output_tokens   INTEGER NOT NULL,
    estimated_cost_usd NUMERIC(10,4),
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_runs_session ON tool_runs(session_id);
CREATE INDEX IF NOT EXISTS idx_vulns_session ON vulnerabilities(session_id);
CREATE INDEX IF NOT EXISTS idx_vulns_cve ON vulnerabilities(cve_id);
CREATE INDEX IF NOT EXISTS idx_fixes_vuln ON fixes(vulnerability_id);
CREATE INDEX IF NOT EXISTS idx_summaries_session ON ai_summaries(session_id);

COMMIT;
