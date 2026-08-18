import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { getAthleteProfile } from "../services/api";


const AthleteProfileContext = createContext();


export function AthleteProfileProvider({ children }) {

  const [hasAthleteProfile, setHasAthleteProfile] = useState(null);
  const [loadingProfileStatus, setLoadingProfileStatus] = useState(true);
  const [profileStatusError, setProfileStatusError] = useState("");

  const refreshProfileStatus = useCallback(async () => {

    const token = localStorage.getItem("access_token");

    if (!token) {
      setHasAthleteProfile(null);
      setProfileStatusError("");
      setLoadingProfileStatus(false);
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
      } else {
        setHasAthleteProfile(null);
        setProfileStatusError(error.message);
      }
    } finally {
      setLoadingProfileStatus(false);
    }

  }, []);

  useEffect(() => {
    refreshProfileStatus();
  }, [refreshProfileStatus]);

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
