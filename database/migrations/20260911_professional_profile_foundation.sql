BEGIN;

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
    CONSTRAINT ck_professional_profiles_role_valid
        CHECK (professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_profiles_verification_status_valid
        CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    CONSTRAINT ck_professional_profiles_experience_non_negative
        CHECK (years_of_experience IS NULL OR years_of_experience >= 0),
    CONSTRAINT ck_professional_profiles_completion_range
        CHECK (profile_completion IS NULL OR (profile_completion >= 0 AND profile_completion <= 100))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_profiles_user_role
    ON professional_profiles(user_id, professional_role);

CREATE INDEX IF NOT EXISTS ix_professional_profiles_user_id
    ON professional_profiles(user_id);

CREATE INDEX IF NOT EXISTS ix_professional_profiles_professional_role
    ON professional_profiles(professional_role);

CREATE INDEX IF NOT EXISTS ix_professional_profiles_verification_status
    ON professional_profiles(verification_status);

CREATE INDEX IF NOT EXISTS ix_professional_profiles_role_status
    ON professional_profiles(professional_role, verification_status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_role_requests_user_role_pending
    ON professional_role_requests(user_id, requested_role)
    WHERE status = 'PENDING';

INSERT INTO professional_profiles (
    user_id,
    professional_role,
    verification_status,
    primary_sport,
    other_sports,
    years_of_experience,
    specialization,
    organization,
    certifications,
    professional_bio,
    profile_photo_url,
    profile_completion,
    created_at,
    updated_at
)
SELECT
    user_id,
    'COACH',
    verification_status,
    primary_sport,
    other_sports,
    years_of_experience,
    coaching_specialization,
    organization,
    certifications,
    professional_bio,
    profile_photo_url,
    profile_completion,
    created_at,
    updated_at
FROM coach_profiles
ON CONFLICT (user_id, professional_role) DO UPDATE
SET
    verification_status = EXCLUDED.verification_status,
    primary_sport = EXCLUDED.primary_sport,
    other_sports = EXCLUDED.other_sports,
    years_of_experience = EXCLUDED.years_of_experience,
    specialization = EXCLUDED.specialization,
    organization = EXCLUDED.organization,
    certifications = EXCLUDED.certifications,
    professional_bio = EXCLUDED.professional_bio,
    profile_photo_url = EXCLUDED.profile_photo_url,
    profile_completion = EXCLUDED.profile_completion,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;
