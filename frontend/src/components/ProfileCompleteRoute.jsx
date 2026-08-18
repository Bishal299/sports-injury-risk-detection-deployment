import React from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAthleteProfile } from "../context/AthleteProfileContext";


function ProfileCompleteRoute({ children }) {

  const location = useLocation();
  const {
    hasAthleteProfile,
    loadingProfileStatus,
  } = useAthleteProfile();

  if (loadingProfileStatus) {
    return <p>Checking athlete profile...</p>;
  }

  if (hasAthleteProfile === false) {
    return (
      <Navigate
        to="/athlete-profile"
        replace
        state={{ intendedPath: location.pathname }}
      />
    );
  }

  return children;
}


export default ProfileCompleteRoute;
