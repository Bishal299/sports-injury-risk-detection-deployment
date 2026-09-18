import React from "react";
import { Navigate } from "react-router-dom";

import { useAuth, AUTH_STATUS } from "../context/AuthContext";
import { getDefaultRouteForRole } from "../utils/roleRoutes";

function RoleRoute({ allowedRoles, children }) {
  const { user, status, isLoading } = useAuth();

  if (isLoading) {
    return <p>Checking permissions...</p>;
  }

  if (status !== AUTH_STATUS.AUTHENTICATED || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
  }

  return children;
}

export default RoleRoute;
