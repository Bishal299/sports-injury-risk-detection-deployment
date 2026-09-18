import React, { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { getCoachProfile } from "../services/api";


function VerifiedCoachRoute({ children }) {
  const location = useLocation();
  const [state, setState] = useState({
    loading: true,
    verified: false,
    unauthenticated: false,
  });

  useEffect(() => {
    let cancelled = false;

    async function verifyCoach() {
      try {
        const profile = await getCoachProfile();

        if (!cancelled) {
          setState({
            loading: false,
            verified: profile.verification_status === "VERIFIED",
            unauthenticated: false,
          });
        }
      } catch (error) {
        if (!cancelled) {
          const unauthenticated =
            error.message === "Not authenticated" ||
            error.message === "Invalid token" ||
            error.message === "User not found";

          setState({
            loading: false,
            verified: false,
            unauthenticated,
          });
        }
      }
    }

    verifyCoach();
  }, []);

  if (state.loading) {
    return <p>Checking Coach access...</p>;
  }

  if (state.unauthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!state.verified) {
    return <Navigate to="/request-professional-role" replace />;
  }

  return children;
}


export default VerifiedCoachRoute;
