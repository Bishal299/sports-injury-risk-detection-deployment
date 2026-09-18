ALTER TABLE coach_tasks
    ADD COLUMN IF NOT EXISTS analysis_id UUID REFERENCES analysis_results(analysis_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS video_id UUID REFERENCES videos(video_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_coach_tasks_analysis_id
    ON coach_tasks(analysis_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_video_id
    ON coach_tasks(video_id);
