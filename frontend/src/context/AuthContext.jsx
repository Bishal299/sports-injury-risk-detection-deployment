import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getAuthMe, logoutUser as apiLogoutUser } from "../services/api";

export const AUTH_STATUS = {
  INITIAL_AUTH_CHECK: "INITIAL_AUTH_CHECK",
  NO_SESSION: "NO_SESSION",
  AUTHENTICATED: "AUTHENTICATED",
  SESSION_EXPIRED: "SESSION_EXPIRED",
  LOGIN_FAILED: "LOGIN_FAILED",
};

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState(AUTH_STATUS.INITIAL_AUTH_CHECK);
  const [user, setUser] = useState(null);
  const [sessionExpiredMsg, setSessionExpiredMsg] = useState("");
  const authPromiseRef = useRef(null);

  const checkAuth = useCallback(async (isInitial = false) => {
    if (authPromiseRef.current) {
      return authPromiseRef.current;
    }

    const promise = (async () => {
      try {
        const userData = await getAuthMe({ silent401: true });
        setUser(userData);
        setStatus(AUTH_STATUS.AUTHENTICATED);
        setSessionExpiredMsg("");
        return userData;
      } catch (err) {
        setUser(null);
        const hadPreviousSession =
          typeof window !== "undefined" &&
          window.sessionStorage?.getItem("sportrisk_had_session") === "true";

        const isExplicitExpiry = err.message?.toLowerCase().includes("expired");

        if (!isInitial && (hadPreviousSession || isExplicitExpiry)) {
          setStatus(AUTH_STATUS.SESSION_EXPIRED);
          setSessionExpiredMsg("Your session has expired. Please log in again.");
        } else {
          setStatus(AUTH_STATUS.NO_SESSION);
          setSessionExpiredMsg("");
        }
        return null;
      } finally {
        authPromiseRef.current = null;
      }
    })();

    authPromiseRef.current = promise;
    return promise;
  }, []);

  useEffect(() => {
    checkAuth(true);

    const handleExpiredEvent = (event) => {
      setUser(null);
      setStatus(AUTH_STATUS.SESSION_EXPIRED);
      setSessionExpiredMsg(
        event.detail?.message || "Your session has expired. Please log in again."
      );
    };

    const handleLogoutEvent = () => {
      setUser(null);
      setStatus(AUTH_STATUS.NO_SESSION);
      setSessionExpiredMsg("");
    };

    window.addEventListener("session-expired", handleExpiredEvent);
    window.addEventListener("auth-logout", handleLogoutEvent);
    return () => {
      window.removeEventListener("session-expired", handleExpiredEvent);
      window.removeEventListener("auth-logout", handleLogoutEvent);
    };
  }, [checkAuth]);

  const handleLogout = useCallback(async () => {
    setUser(null);
    setStatus(AUTH_STATUS.NO_SESSION);
    setSessionExpiredMsg("");
    try {
      await apiLogoutUser();
    } catch {
      // Ignore network errors on logout
    }
  }, []);

  const clearSessionExpiredMsg = useCallback(() => {
    setSessionExpiredMsg("");
    if (status === AUTH_STATUS.SESSION_EXPIRED) {
      setStatus(AUTH_STATUS.NO_SESSION);
    }
  }, [status]);

  const setAuthenticatedUser = useCallback((userData) => {
    setUser(userData);
    setStatus(AUTH_STATUS.AUTHENTICATED);
    setSessionExpiredMsg("");
    if (typeof window !== "undefined" && window.sessionStorage) {
      window.sessionStorage.setItem("sportrisk_had_session", "true");
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        status,
        user,
        sessionExpiredMsg,
        checkAuth,
        logout: handleLogout,
        clearSessionExpiredMsg,
        setAuthenticatedUser,
        isAuthenticated: status === AUTH_STATUS.AUTHENTICATED,
        isLoading: status === AUTH_STATUS.INITIAL_AUTH_CHECK,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export default AuthContext;
