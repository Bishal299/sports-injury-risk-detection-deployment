CREATE TABLE IF NOT EXISTS rehabilitation_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rehabilitation_plan_id UUID NOT NULL REFERENCES rehabilitation_plans(rehabilitation_plan_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase VARCHAR(50) NOT NULL,
    due_date DATE,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    completed_at TIMESTAMP,
    athlete_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_rehabilitation_activities_phase_valid
        CHECK (phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')),
    CONSTRAINT ck_rehabilitation_activities_priority_valid
        CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT ck_rehabilitation_activities_status_valid
        CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED'))
);

CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_plan_id
    ON rehabilitation_activities(rehabilitation_plan_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_status
    ON rehabilitation_activities(status);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_phase
    ON rehabilitation_activities(phase);
