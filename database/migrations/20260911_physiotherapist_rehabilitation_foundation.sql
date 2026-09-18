CREATE TABLE IF NOT EXISTS rehabilitation_plans (
    rehabilitation_plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    physiotherapist_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    injury_context TEXT,
    start_date DATE,
    target_date DATE,
    current_phase VARCHAR(50) NOT NULL DEFAULT 'ASSESSMENT',
    progress DOUBLE PRECISION NOT NULL DEFAULT 0,
    goals JSON,
    completed_activities JSON,
    pending_activities JSON,
    recent_assessment TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_rehabilitation_plans_status_valid
        CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT ck_rehabilitation_plans_phase_valid
        CHECK (current_phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')),
    CONSTRAINT ck_rehabilitation_plans_progress_range
        CHECK (progress IS NULL OR (progress >= 0 AND progress <= 100))
);

CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_athlete_id
    ON rehabilitation_plans(athlete_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_physiotherapist_user_id
    ON rehabilitation_plans(physiotherapist_user_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_status
    ON rehabilitation_plans(status);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_physio_athlete_status
    ON rehabilitation_plans(physiotherapist_user_id, athlete_id, status);

CREATE TABLE IF NOT EXISTS physiotherapist_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    physiotherapist_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255),
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_physiotherapist_notes_athlete_id
    ON physiotherapist_notes(athlete_id);
CREATE INDEX IF NOT EXISTS ix_physiotherapist_notes_physiotherapist_user_id
    ON physiotherapist_notes(physiotherapist_user_id);
CREATE INDEX IF NOT EXISTS ix_physiotherapist_notes_physio_athlete
    ON physiotherapist_notes(physiotherapist_user_id, athlete_id);
