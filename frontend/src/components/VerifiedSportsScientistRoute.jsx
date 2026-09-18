import React, { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { getSportsScientistProfile } from "../services/api";


function VerifiedSportsScientistRoute({ children }) {
  const location = useLocation();
  const [state, setState] = useState({
    loading: true,
    verified: false,
    unauthenticated: false,
  });

  useEffect(() => {
    let cancelled = false;

    async function verify() {
      try {
        const profile = await getSportsScientistProfile();
        if (!cancelled) {
          setState({
            loading: false,
            verified: profile.verification_status === "VERIFIED",
            unauthenticated: false,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            loading: false,
            verified: false,
            unauthenticated: ["Not authenticated", "Invalid token", "User not found"].includes(error.message),
          });
        }
      }
    }

    verify();

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.loading) {
    return <p>Checking Sports Scientist access...</p>;
  }

  if (state.unauthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!state.verified) {
    return <Navigate to="/request-professional-role" replace />;
  }

  return children;
}


export default VerifiedSportsScientistRoute;
