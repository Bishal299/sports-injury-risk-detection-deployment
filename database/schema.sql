-- Sports Injury Risk Detection Database Schema

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'athlete' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS athletes (
    athlete_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    sport VARCHAR(100),
    position VARCHAR(100),
    age INTEGER,
    height FLOAT,
    weight FLOAT,
    training_load FLOAT,
    flexibility FLOAT,
    strength FLOAT,
    balance FLOAT,
    endurance FLOAT,
    coach_notes TEXT
);

CREATE TABLE IF NOT EXISTS injury_history (
    injury_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    injury_type VARCHAR(100) NOT NULL,
    body_part VARCHAR(100) NOT NULL,
    affected_side VARCHAR(20) DEFAULT 'NOT_APPLICABLE' NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL,
    injury_date DATE NOT NULL,
    recovery_date DATE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_injury_history_injury_type_not_empty CHECK (char_length(trim(injury_type)) > 0),
    CONSTRAINT ck_injury_history_body_part_not_empty CHECK (char_length(trim(body_part)) > 0),
    CONSTRAINT ck_injury_history_affected_side_valid CHECK (affected_side IN ('LEFT', 'RIGHT', 'BILATERAL', 'NOT_APPLICABLE')),
    CONSTRAINT ck_injury_history_severity_valid CHECK (severity IN ('MILD', 'MODERATE', 'SEVERE')),
    CONSTRAINT ck_injury_history_status_valid CHECK (status IN ('ACTIVE', 'RECOVERED', 'CHRONIC', 'UNKNOWN')),
    CONSTRAINT ck_injury_history_recovery_after_injury CHECK (recovery_date IS NULL OR recovery_date >= injury_date)
);

CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_id ON injury_history(athlete_id);
CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_injury_date ON injury_history(athlete_id, injury_date);

CREATE TABLE IF NOT EXISTS videos (
    video_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    activity VARCHAR(255),
    video_url TEXT,
    duration FLOAT,
    fps INTEGER,
    resolution VARCHAR(50),
    quality_score FLOAT,
    processing_status VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    knee_valgus FLOAT,
    hip_stability FLOAT,
    trunk_lean FLOAT,
    stride_length FLOAT,
    joint_alignment FLOAT,
    symmetry_score FLOAT,
    fatigue_score FLOAT,
    movement_quality FLOAT,
    overall_risk_score FLOAT,
    risk_level VARCHAR(50),
    algorithm_version VARCHAR(50) DEFAULT '1.0-phase1-filtered' NOT NULL,
    historical_score FLOAT,
    biomechanical_score FLOAT,
    asymmetry_score FLOAT,
    training_load_score FLOAT,
    composite_risk_score FLOAT,
    risk_category VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    progress INTEGER DEFAULT 0 NOT NULL,
    stage VARCHAR(255) DEFAULT 'Preparing video...' NOT NULL,
    error_message TEXT,
    skeleton_video_url TEXT,
    csv_report_url TEXT,
    pdf_report_url TEXT,
    summary_metrics JSONB,
    time_series_data JSONB,
    recommendations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_analysis_results_athlete_date ON analysis_results(athlete_id, analysis_date);
CREATE INDEX IF NOT EXISTS ix_analysis_results_video_date ON analysis_results(video_id, analysis_date);

CREATE TABLE IF NOT EXISTS professional_role_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    requested_role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    primary_sport VARCHAR(100),
    organization VARCHAR(255),
    specialization VARCHAR(255),
    years_of_experience INTEGER,
    certifications TEXT,
    professional_bio TEXT,
    supporting_document_url TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_professional_role_requests_requested_role_valid CHECK (requested_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_role_requests_status_valid CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT ck_professional_role_requests_experience_non_negative CHECK (years_of_experience IS NULL OR years_of_experience >= 0)
);

CREATE INDEX IF NOT EXISTS ix_professional_role_requests_user_id ON professional_role_requests(user_id);
CREATE INDEX IF NOT EXISTS ix_professional_role_requests_status ON professional_role_requests(status);
CREATE INDEX IF NOT EXISTS ix_professional_role_requests_requested_role_status ON professional_role_requests(requested_role, status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_role_requests_user_role_pending ON professional_role_requests(user_id, requested_role) WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS professional_profiles (
    professional_profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    professional_role VARCHAR(50) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    primary_sport VARCHAR(100),
    other_sports TEXT,
    years_of_experience INTEGER,
    specialization VARCHAR(255),
    organization VARCHAR(255),
    certifications TEXT,
    professional_bio TEXT,
    profile_photo_url TEXT,
    profile_completion FLOAT DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_professional_profiles_role_valid CHECK (professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_profiles_verification_status_valid CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    CONSTRAINT ck_professional_profiles_experience_non_negative CHECK (years_of_experience IS NULL OR years_of_experience >= 0),
    CONSTRAINT ck_professional_profiles_completion_range CHECK (profile_completion IS NULL OR (profile_completion >= 0 AND profile_completion <= 100))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_profiles_user_role ON professional_profiles(user_id, professional_role);
CREATE INDEX IF NOT EXISTS ix_professional_profiles_user_id ON professional_profiles(user_id);
CREATE INDEX IF NOT EXISTS ix_professional_profiles_professional_role ON professional_profiles(professional_role);
CREATE INDEX IF NOT EXISTS ix_professional_profiles_verification_status ON professional_profiles(verification_status);
CREATE INDEX IF NOT EXISTS ix_professional_profiles_role_status ON professional_profiles(professional_role, verification_status);

CREATE TABLE IF NOT EXISTS professional_athlete_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professional_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    professional_role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    requested_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    responded_at TIMESTAMP,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_professional_athlete_relationships_role_valid CHECK (professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_athlete_relationships_status_valid CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_athlete_relationships_active_pending_pair ON professional_athlete_relationships(professional_user_id, athlete_id, professional_role) WHERE status IN ('PENDING', 'ACTIVE');
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_user_id ON professional_athlete_relationships(professional_user_id);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_athlete_id ON professional_athlete_relationships(athlete_id);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_role ON professional_athlete_relationships(professional_role);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_status ON professional_athlete_relationships(status);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_status ON professional_athlete_relationships(professional_user_id, status);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_athlete_status ON professional_athlete_relationships(athlete_id, status);
CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_role_status ON professional_athlete_relationships(professional_role, status);

CREATE TABLE IF NOT EXISTS rehabilitation_plans (
    rehabilitation_plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    physiotherapist_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    injury_context TEXT,
    start_date DATE,
    target_date DATE,
    current_phase VARCHAR(50) DEFAULT 'ASSESSMENT' NOT NULL,
    progress FLOAT DEFAULT 0 NOT NULL,
    goals JSONB,
    completed_activities JSONB,
    pending_activities JSONB,
    recent_assessment TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_rehabilitation_plans_status_valid CHECK (status IN ('ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED')),
    CONSTRAINT ck_rehabilitation_plans_phase_valid CHECK (current_phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')),
    CONSTRAINT ck_rehabilitation_plans_progress_range CHECK (progress >= 0 AND progress <= 100)
);

CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_athlete_id ON rehabilitation_plans(athlete_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_physiotherapist_user_id ON rehabilitation_plans(physiotherapist_user_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_status ON rehabilitation_plans(status);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_plans_physio_athlete_status ON rehabilitation_plans(physiotherapist_user_id, athlete_id, status);

CREATE TABLE IF NOT EXISTS rehabilitation_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rehabilitation_plan_id UUID NOT NULL REFERENCES rehabilitation_plans(rehabilitation_plan_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase VARCHAR(50) DEFAULT 'ASSESSMENT' NOT NULL,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    completed_at TIMESTAMP,
    athlete_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_rehabilitation_activities_title_not_empty CHECK (char_length(trim(title)) > 0),
    CONSTRAINT ck_rehabilitation_activities_phase_valid CHECK (phase IN ('ASSESSMENT', 'MOBILITY', 'STRENGTH', 'BALANCE_STABILITY', 'MOVEMENT_CORRECTION', 'SPORT_SPECIFIC_TRAINING', 'RETURN_TO_SPORT')),
    CONSTRAINT ck_rehabilitation_activities_priority_valid CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT ck_rehabilitation_activities_status_valid CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED'))
);

CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_plan_id ON rehabilitation_activities(rehabilitation_plan_id);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_status ON rehabilitation_activities(status);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_phase ON rehabilitation_activities(phase);
CREATE INDEX IF NOT EXISTS ix_rehabilitation_activities_due_date ON rehabilitation_activities(due_date);

CREATE TABLE IF NOT EXISTS coach_profiles (
    coach_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    primary_sport VARCHAR(100),
    other_sports TEXT,
    years_of_experience INTEGER,
    coaching_specialization VARCHAR(255),
    organization VARCHAR(255),
    certifications TEXT,
    professional_bio TEXT,
    profile_photo_url TEXT,
    verification_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    profile_completion FLOAT DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_coach_profiles_verification_status_valid CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    CONSTRAINT ck_coach_profiles_experience_non_negative CHECK (years_of_experience IS NULL OR years_of_experience >= 0),
    CONSTRAINT ck_coach_profiles_completion_range CHECK (profile_completion IS NULL OR (profile_completion >= 0 AND profile_completion <= 100))
);

CREATE INDEX IF NOT EXISTS ix_coach_profiles_user_id ON coach_profiles(user_id);
CREATE INDEX IF NOT EXISTS ix_coach_profiles_verification_status ON coach_profiles(verification_status);

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

CREATE INDEX IF NOT EXISTS ix_coach_tasks_coach_id ON coach_tasks(coach_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_athlete_id ON coach_tasks(athlete_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_analysis_id ON coach_tasks(analysis_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_video_id ON coach_tasks(video_id);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_status ON coach_tasks(status);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_due_date ON coach_tasks(due_date);
CREATE INDEX IF NOT EXISTS ix_coach_tasks_coach_athlete_status ON coach_tasks(coach_id, athlete_id, status);

CREATE TABLE IF NOT EXISTS coach_athlete_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL REFERENCES coach_profiles(coach_id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athletes(athlete_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    responded_at TIMESTAMP,
    accepted_at TIMESTAMP,
    requested_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_coach_athlete_relationships_status_valid CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_coach_athlete_relationships_active_pending_pair ON coach_athlete_relationships(coach_id, athlete_id) WHERE status IN ('PENDING', 'ACTIVE');
CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_coach_id ON coach_athlete_relationships(coach_id);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_athlete_id ON coach_athlete_relationships(athlete_id);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_status ON coach_athlete_relationships(status);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_coach_status ON coach_athlete_relationships(coach_id, status);
CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_athlete_status ON coach_athlete_relationships(athlete_id, status);
