BEGIN;

CREATE TABLE IF NOT EXISTS injury_history (
    injury_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    injury_type VARCHAR(100) NOT NULL,
    body_part VARCHAR(100) NOT NULL,
    affected_side VARCHAR(20) DEFAULT 'NOT_APPLICABLE' NOT NULL,
    severity VARCHAR(50) DEFAULT 'MODERATE' NOT NULL,
    status VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL,
    injury_date DATE NOT NULL,
    recovery_date DATE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE injury_history
    ADD COLUMN IF NOT EXISTS affected_side VARCHAR(20) DEFAULT 'NOT_APPLICABLE' NOT NULL,
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL,
    ADD COLUMN IF NOT EXISTS recovery_date DATE,
    ADD COLUMN IF NOT EXISTS remarks TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

UPDATE injury_history
SET
    injury_type = COALESCE(NULLIF(trim(injury_type), ''), 'Unknown injury'),
    body_part = COALESCE(NULLIF(trim(body_part), ''), 'Unknown'),
    affected_side = CASE UPPER(COALESCE(NULLIF(trim(affected_side), ''), 'NOT_APPLICABLE'))
        WHEN 'LEFT' THEN 'LEFT'
        WHEN 'RIGHT' THEN 'RIGHT'
        WHEN 'BILATERAL' THEN 'BILATERAL'
        ELSE 'NOT_APPLICABLE'
    END,
    severity = CASE UPPER(COALESCE(NULLIF(trim(severity), ''), 'MODERATE'))
        WHEN 'MILD' THEN 'MILD'
        WHEN 'MODERATE' THEN 'MODERATE'
        WHEN 'SEVERE' THEN 'SEVERE'
        ELSE 'MODERATE'
    END,
    status = CASE UPPER(COALESCE(NULLIF(trim(status), ''), 'UNKNOWN'))
        WHEN 'ACTIVE' THEN 'ACTIVE'
        WHEN 'RECOVERED' THEN 'RECOVERED'
        WHEN 'CHRONIC' THEN 'CHRONIC'
        ELSE 'UNKNOWN'
    END,
    injury_date = COALESCE(injury_date, CURRENT_DATE);

ALTER TABLE injury_history
    ALTER COLUMN injury_type TYPE VARCHAR(100),
    ALTER COLUMN injury_type SET NOT NULL,
    ALTER COLUMN body_part SET NOT NULL,
    ALTER COLUMN affected_side SET NOT NULL,
    ALTER COLUMN severity SET NOT NULL,
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN injury_date SET NOT NULL;

ALTER TABLE injury_history
    DROP CONSTRAINT IF EXISTS ck_injury_history_injury_type_not_empty,
    DROP CONSTRAINT IF EXISTS ck_injury_history_body_part_not_empty,
    DROP CONSTRAINT IF EXISTS ck_injury_history_affected_side_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_severity_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_status_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_recovery_after_injury;

ALTER TABLE injury_history
    ADD CONSTRAINT ck_injury_history_injury_type_not_empty CHECK (char_length(trim(injury_type)) > 0),
    ADD CONSTRAINT ck_injury_history_body_part_not_empty CHECK (char_length(trim(body_part)) > 0),
    ADD CONSTRAINT ck_injury_history_affected_side_valid CHECK (affected_side IN ('LEFT', 'RIGHT', 'BILATERAL', 'NOT_APPLICABLE')),
    ADD CONSTRAINT ck_injury_history_severity_valid CHECK (severity IN ('MILD', 'MODERATE', 'SEVERE')),
    ADD CONSTRAINT ck_injury_history_status_valid CHECK (status IN ('ACTIVE', 'RECOVERED', 'CHRONIC', 'UNKNOWN')),
    ADD CONSTRAINT ck_injury_history_recovery_after_injury CHECK (recovery_date IS NULL OR recovery_date >= injury_date);

CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_id ON injury_history(athlete_id);
CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_injury_date ON injury_history(athlete_id, injury_date);

ALTER TABLE analysis_results
    DROP CONSTRAINT IF EXISTS analysis_results_video_id_key,
    ADD COLUMN IF NOT EXISTS algorithm_version VARCHAR(50) DEFAULT '1.0-phase1-filtered' NOT NULL,
    ADD COLUMN IF NOT EXISTS historical_score FLOAT,
    ADD COLUMN IF NOT EXISTS biomechanical_score FLOAT,
    ADD COLUMN IF NOT EXISTS asymmetry_score FLOAT,
    ADD COLUMN IF NOT EXISTS training_load_score FLOAT,
    ADD COLUMN IF NOT EXISTS composite_risk_score FLOAT,
    ADD COLUMN IF NOT EXISTS risk_category VARCHAR(50),
    ADD COLUMN IF NOT EXISTS analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

CREATE INDEX IF NOT EXISTS ix_analysis_results_athlete_date ON analysis_results(athlete_id, analysis_date);
CREATE INDEX IF NOT EXISTS ix_analysis_results_video_date ON analysis_results(video_id, analysis_date);

COMMIT;

-- Rollback:
-- BEGIN;
-- DROP INDEX IF EXISTS ix_analysis_results_video_date;
-- DROP INDEX IF EXISTS ix_analysis_results_athlete_date;
-- ALTER TABLE analysis_results
--     DROP COLUMN IF EXISTS analysis_date,
--     DROP COLUMN IF EXISTS risk_category,
--     DROP COLUMN IF EXISTS composite_risk_score,
--     DROP COLUMN IF EXISTS training_load_score,
--     DROP COLUMN IF EXISTS asymmetry_score,
--     DROP COLUMN IF EXISTS biomechanical_score,
--     DROP COLUMN IF EXISTS historical_score,
--     DROP COLUMN IF EXISTS algorithm_version;
-- ALTER TABLE analysis_results ADD CONSTRAINT analysis_results_video_id_key UNIQUE (video_id);
-- DROP INDEX IF EXISTS ix_injury_history_athlete_injury_date;
-- DROP INDEX IF EXISTS ix_injury_history_athlete_id;
-- ALTER TABLE injury_history
--     DROP CONSTRAINT IF EXISTS ck_injury_history_recovery_after_injury,
--     DROP CONSTRAINT IF EXISTS ck_injury_history_status_valid,
--     DROP CONSTRAINT IF EXISTS ck_injury_history_severity_valid,
--     DROP CONSTRAINT IF EXISTS ck_injury_history_affected_side_valid,
--     DROP CONSTRAINT IF EXISTS ck_injury_history_body_part_not_empty,
--     DROP CONSTRAINT IF EXISTS ck_injury_history_injury_type_not_empty,
--     DROP COLUMN IF EXISTS updated_at,
--     DROP COLUMN IF EXISTS created_at,
--     DROP COLUMN IF EXISTS remarks,
--     DROP COLUMN IF EXISTS recovery_date,
--     DROP COLUMN IF EXISTS status,
--     DROP COLUMN IF EXISTS affected_side;
-- COMMIT;
