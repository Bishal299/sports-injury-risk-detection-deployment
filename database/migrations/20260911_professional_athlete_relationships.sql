BEGIN;

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
    CONSTRAINT ck_professional_athlete_relationships_role_valid
        CHECK (professional_role IN ('COACH', 'PHYSIOTHERAPIST', 'SPORTS_SCIENTIST')),
    CONSTRAINT ck_professional_athlete_relationships_status_valid
        CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED', 'REVOKED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_professional_athlete_relationships_active_pending_pair
    ON professional_athlete_relationships(professional_user_id, athlete_id, professional_role)
    WHERE status IN ('PENDING', 'ACTIVE');

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_user_id
    ON professional_athlete_relationships(professional_user_id);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_athlete_id
    ON professional_athlete_relationships(athlete_id);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_role
    ON professional_athlete_relationships(professional_role);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_status
    ON professional_athlete_relationships(status);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_professional_status
    ON professional_athlete_relationships(professional_user_id, status);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_athlete_status
    ON professional_athlete_relationships(athlete_id, status);

CREATE INDEX IF NOT EXISTS ix_professional_athlete_relationships_role_status
    ON professional_athlete_relationships(professional_role, status);

COMMIT;
