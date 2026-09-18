BEGIN;

DROP INDEX IF EXISTS ix_coach_athlete_relationships_athlete_status;
DROP INDEX IF EXISTS ix_coach_athlete_relationships_coach_status;
DROP INDEX IF EXISTS ix_coach_athlete_relationships_status;
DROP INDEX IF EXISTS ix_coach_athlete_relationships_athlete_id;
DROP INDEX IF EXISTS ix_coach_athlete_relationships_coach_id;
DROP INDEX IF EXISTS uq_coach_athlete_relationships_active_pending_pair;
DROP TABLE IF EXISTS coach_athlete_relationships;

DROP INDEX IF EXISTS ix_coach_profiles_verification_status;
DROP INDEX IF EXISTS ix_coach_profiles_user_id;
DROP TABLE IF EXISTS coach_profiles;

DROP INDEX IF EXISTS ix_professional_role_requests_requested_role_status;
DROP INDEX IF EXISTS ix_professional_role_requests_status;
DROP INDEX IF EXISTS ix_professional_role_requests_user_id;
DROP TABLE IF EXISTS professional_role_requests;

COMMIT;
