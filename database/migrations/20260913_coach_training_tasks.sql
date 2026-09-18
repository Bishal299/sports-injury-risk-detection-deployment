CREATE TABLE IF NOT EXISTS coach_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL REFERENCES coach_profiles(coach_id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES analysis_results(analysis_id) ON DELETE SET NULL,
    video_id UUID REFERENCES videos(video_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    status VARCHAR(20) DEFAULT 'ASSIGNED' NOT NULL,
    completed_at TIMESTAMP,
    athlete_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_coach_tasks_title_not_empty CHECK (char_length(trim(title)) > 0),
    CONSTRAINT ck_coach_tasks_priority_valid CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT ck_coach_tasks_status_valid CHECK (status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'CANCELLED'))
);

CREATE INDEX IF NOT EXISTS ix_coach_tasks_coach_id
    ON coach_tasks(coach_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_athlete_id
    ON coach_tasks(athlete_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_analysis_id
    ON coach_tasks(analysis_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_video_id
    ON coach_tasks(video_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_status
    ON coach_tasks(status);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_due_date
    ON coach_tasks(due_date);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_coach_athlete_status
    ON coach_tasks(coach_id, athlete_id, status);
