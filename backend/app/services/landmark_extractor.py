def extract_landmarks(results):

    if not results.pose_landmarks:
        return None

    landmarks = results.pose_landmarks[0]

    extracted = []

    for index, landmark in enumerate(landmarks):

        extracted.append({
            "landmark_id": index,
            "x": landmark.x,
            "y": landmark.y,
            "z": landmark.z,
            "visibility": landmark.visibility
        })

    return extracted