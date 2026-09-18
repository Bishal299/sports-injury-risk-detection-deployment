import React from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getDefaultRouteForRole } from "../utils/roleRoutes";

function PublicRoute({ children }) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "50vh",
          color: "var(--text-secondary, #6b7280)",
          fontSize: "0.95rem",
        }}
      >
        Loading...
      </div>
    );
  }

  if (isAuthenticated && user?.role) {
    return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
  }

  return children;
}

export default PublicRoute;
