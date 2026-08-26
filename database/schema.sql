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
    injury_type VARCHAR(255) NOT NULL,
    body_part VARCHAR(100) NOT NULL,
    injury_date DATE,
    recovery_status VARCHAR(50)
);

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
    video_id UUID UNIQUE NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
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
    completed_at TIMESTAMP
);
