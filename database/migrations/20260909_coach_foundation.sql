BEGIN;

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
    CONSTRAINT ck_professional_role_requests_requested_role_valid
        CHECK (requested_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_role_requests_status_valid
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT ck_professional_role_requests_experience_non_negative
        CHECK (years_of_experience IS NULL OR years_of_experience >= 0)
);

CREATE INDEX IF NOT EXISTS ix_professional_role_requests_user_id
    ON professional_role_requests(user_id);

CREATE INDEX IF NOT EXISTS ix_professional_role_requests_status
    ON professional_role_requests(status);

CREATE INDEX IF NOT EXISTS ix_professional_role_requests_requested_role_status
    ON professional_role_requests(requested_role, status);

UPDATE professional_role_requests
SET
    request_id = COALESCE(request_id, gen_random_uuid()),
    status = COALESCE(status, 'PENDING'),
    submitted_at = COALESCE(submitted_at, CURRENT_TIMESTAMP),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

ALTER TABLE professional_role_requests
    ALTER COLUMN request_id SET DEFAULT gen_random_uuid(),
    ALTER COLUMN request_id SET NOT NULL,
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN requested_role SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'PENDING',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN submitted_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN submitted_at SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN updated_at SET NOT NULL;

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
    CONSTRAINT ck_coach_profiles_verification_status_valid
        CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    CONSTRAINT ck_coach_profiles_experience_non_negative
        CHECK (years_of_experience IS NULL OR years_of_experience >= 0),
    CONSTRAINT ck_coach_profiles_completion_range
        CHECK (profile_completion IS NULL OR (profile_completion >= 0 AND profile_completion <= 100))
);

CREATE INDEX IF NOT EXISTS ix_coach_profiles_user_id
    ON coach_profiles(user_id);

CREATE INDEX IF NOT EXISTS ix_coach_profiles_verification_status
    ON coach_profiles(verification_status);

UPDATE coach_profiles
SET
    coach_id = COALESCE(coach_id, gen_random_uuid()),
    verification_status = COALESCE(verification_status, 'PENDING'),
    profile_completion = COALESCE(profile_completion, 0),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

ALTER TABLE coach_profiles
    ALTER COLUMN coach_id SET DEFAULT gen_random_uuid(),
    ALTER COLUMN coach_id SET NOT NULL,
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN verification_status SET DEFAULT 'PENDING',
    ALTER COLUMN verification_status SET NOT NULL,
    ALTER COLUMN profile_completion SET DEFAULT 0,
    ALTER COLUMN profile_completion SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN updated_at SET NOT NULL;

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
    CONSTRAINT ck_coach_athlete_relationships_status_valid
        CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_coach_athlete_relationships_active_pending_pair
    ON coach_athlete_relationships(coach_id, athlete_id)
    WHERE status IN ('PENDING', 'ACTIVE');

CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_coach_id
    ON coach_athlete_relationships(coach_id);

CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_athlete_id
    ON coach_athlete_relationships(athlete_id);

CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_status
    ON coach_athlete_relationships(status);

CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_coach_status
    ON coach_athlete_relationships(coach_id, status);

CREATE INDEX IF NOT EXISTS ix_coach_athlete_relationships_athlete_status
    ON coach_athlete_relationships(athlete_id, status);

UPDATE coach_athlete_relationships
SET
    relationship_id = COALESCE(relationship_id, gen_random_uuid()),
    status = COALESCE(status, 'PENDING'),
    requested_at = COALESCE(requested_at, CURRENT_TIMESTAMP),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

ALTER TABLE coach_athlete_relationships
    ALTER COLUMN relationship_id SET DEFAULT gen_random_uuid(),
    ALTER COLUMN relationship_id SET NOT NULL,
    ALTER COLUMN coach_id SET NOT NULL,
    ALTER COLUMN athlete_id SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'PENDING',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN requested_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN requested_at SET NOT NULL,
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN updated_at SET NOT NULL;

COMMIT;
