BEGIN;

DROP INDEX IF EXISTS ix_analysis_results_video_date;
DROP INDEX IF EXISTS ix_analysis_results_athlete_date;

ALTER TABLE analysis_results
    DROP COLUMN IF EXISTS analysis_date,
    DROP COLUMN IF EXISTS risk_category,
    DROP COLUMN IF EXISTS composite_risk_score,
    DROP COLUMN IF EXISTS training_load_score,
    DROP COLUMN IF EXISTS asymmetry_score,
    DROP COLUMN IF EXISTS biomechanical_score,
    DROP COLUMN IF EXISTS historical_score,
    DROP COLUMN IF EXISTS algorithm_version;

ALTER TABLE analysis_results
    ADD CONSTRAINT analysis_results_video_id_key UNIQUE (video_id);

DROP INDEX IF EXISTS ix_injury_history_athlete_injury_date;
DROP INDEX IF EXISTS ix_injury_history_athlete_id;

ALTER TABLE injury_history
    DROP CONSTRAINT IF EXISTS ck_injury_history_recovery_after_injury,
    DROP CONSTRAINT IF EXISTS ck_injury_history_status_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_severity_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_affected_side_valid,
    DROP CONSTRAINT IF EXISTS ck_injury_history_body_part_not_empty,
    DROP CONSTRAINT IF EXISTS ck_injury_history_injury_type_not_empty,
    DROP COLUMN IF EXISTS updated_at,
    DROP COLUMN IF EXISTS created_at,
    DROP COLUMN IF EXISTS remarks,
    DROP COLUMN IF EXISTS recovery_date,
    DROP COLUMN IF EXISTS status,
    DROP COLUMN IF EXISTS affected_side;

COMMIT;
