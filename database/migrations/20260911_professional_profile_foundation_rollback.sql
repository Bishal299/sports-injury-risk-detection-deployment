BEGIN;

DROP INDEX IF EXISTS uq_professional_role_requests_user_role_pending;

DROP INDEX IF EXISTS ix_professional_profiles_role_status;
DROP INDEX IF EXISTS ix_professional_profiles_verification_status;
DROP INDEX IF EXISTS ix_professional_profiles_professional_role;
DROP INDEX IF EXISTS ix_professional_profiles_user_id;
DROP INDEX IF EXISTS uq_professional_profiles_user_role;
DROP TABLE IF EXISTS professional_profiles;

COMMIT;
