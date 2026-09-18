import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth, AUTH_STATUS } from "../context/AuthContext";

function ProtectedRoute({ children }) {
  const location = useLocation();
  const { user, status, isLoading, sessionExpiredMsg } = useAuth();

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
        Verifying session...
      </div>
    );
  }

  if (status !== AUTH_STATUS.AUTHENTICATED || !user) {
    const expiredMsg =
      status === AUTH_STATUS.SESSION_EXPIRED || sessionExpiredMsg
        ? sessionExpiredMsg || "Your session has expired. Please log in again."
        : null;

    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
          expiredMessage: expiredMsg,
        }}
      />
    );
  }

  return children;
}

export default ProtectedRoute;
