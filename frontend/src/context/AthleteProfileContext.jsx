import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { getAthleteProfile } from "../services/api";
import { useAuth } from "./AuthContext";

const AthleteProfileContext = createContext();

export function AthleteProfileProvider({ children }) {
  const { user, isAuthenticated } = useAuth();
  const [hasAthleteProfile, setHasAthleteProfile] = useState(null);
  const [loadingProfileStatus, setLoadingProfileStatus] = useState(false);
  const [profileStatusError, setProfileStatusError] = useState("");

  const refreshProfileStatus = useCallback(async () => {
    if (!isAuthenticated || user?.role !== "Athlete") {
      setHasAthleteProfile(null);
      setLoadingProfileStatus(false);
      setProfileStatusError("");
      return;
    }

    setLoadingProfileStatus(true);
    setProfileStatusError("");

    try {
      await getAthleteProfile();
      setHasAthleteProfile(true);
    } catch (error) {
      if (error.message === "Athlete profile not found") {
        setHasAthleteProfile(false);
      } else if (
        error.message === "Not authenticated" ||
        error.message?.includes("expired")
      ) {
        setHasAthleteProfile(null);
        setProfileStatusError("");
      } else {
        setHasAthleteProfile(null);
        setProfileStatusError(error.message);
      }
    } finally {
      setLoadingProfileStatus(false);
    }
  }, [isAuthenticated, user?.role]);

  useEffect(() => {
    if (isAuthenticated && user?.role === "Athlete") {
      refreshProfileStatus();
    } else {
      setHasAthleteProfile(null);
      setLoadingProfileStatus(false);
      setProfileStatusError("");
    }
  }, [isAuthenticated, user?.role, refreshProfileStatus]);

  return (
    <AthleteProfileContext.Provider
      value={{
        hasAthleteProfile,
        loadingProfileStatus,
        profileStatusError,
        refreshProfileStatus,
      }}
    >
      {children}
    </AthleteProfileContext.Provider>
  );
}

export function useAthleteProfile() {
  return useContext(AthleteProfileContext);
}
