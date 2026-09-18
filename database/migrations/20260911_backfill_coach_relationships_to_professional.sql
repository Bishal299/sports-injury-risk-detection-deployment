INSERT INTO professional_athlete_relationships (
    relationship_id,
    professional_user_id,
    athlete_id,
    professional_role,
    status,
    requested_by,
    requested_at,
    responded_at,
    accepted_at,
    created_at,
    updated_at
)
SELECT
    car.relationship_id,
    cp.user_id,
    car.athlete_id,
    'COACH',
    car.status,
    car.requested_by,
    car.requested_at,
    car.responded_at,
    car.accepted_at,
    car.created_at,
    car.updated_at
FROM coach_athlete_relationships car
JOIN coach_profiles cp ON cp.coach_id = car.coach_id
WHERE NOT EXISTS (
    SELECT 1
    FROM professional_athlete_relationships par
    WHERE par.relationship_id = car.relationship_id
)
ON CONFLICT DO NOTHING;
