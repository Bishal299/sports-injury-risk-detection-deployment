DELETE FROM professional_athlete_relationships par
USING coach_athlete_relationships car
WHERE par.relationship_id = car.relationship_id
  AND par.professional_role = 'COACH';
