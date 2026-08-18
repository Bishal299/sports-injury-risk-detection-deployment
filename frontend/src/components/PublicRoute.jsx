import React from "react";
import { Navigate, useNavigationType } from "react-router-dom";


function PublicRoute({ children }) {

  const token = localStorage.getItem("access_token");
  const navigationType = useNavigationType();

  // Going back from a protected screen to Login is treated as a logout.
  // This ensures the browser cannot move forward into a protected route.
  if (token && navigationType === "POP") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");

    return children;
  }

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}


export default PublicRoute;
