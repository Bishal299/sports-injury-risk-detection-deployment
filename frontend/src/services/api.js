import { clearAuthSession, getAuthToken } from "../utils/authSession";


const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof window !== "undefined" && window.location) {
    const currentHost = window.location.hostname;
    // Ensure API matches frontend host to avoid cross-site cookie restrictions between localhost and 127.0.0.1
    if (currentHost === "localhost" && (!envUrl || envUrl.includes("127.0.0.1"))) {
      return (envUrl || "http://127.0.0.1:8000").replace("127.0.0.1", "localhost");
    }
    if (currentHost === "127.0.0.1" && envUrl && envUrl.includes("localhost")) {
      return envUrl.replace("localhost", "127.0.0.1");
    }
  }
  return envUrl || "http://127.0.0.1:8000";
};

const API_BASE_URL = getApiBaseUrl();


const nativeFetch =
  typeof window !== "undefined" && window.fetch
    ? window.fetch.bind(window)
    : globalThis.fetch;

let isHandling401 = false;

async function authFetch(url, options = {}) {
  const opts = {
    ...options,
    credentials: "include",
  };

  const response = await nativeFetch(url, opts);

  if (response.status === 401 && typeof window !== "undefined") {
    const urlStr = typeof url === "string" ? url : (url?.url || "");
    const isAuthEndpoint = (
      urlStr.includes("/auth/login") ||
      urlStr.includes("/auth/register")
    );

    if (!isAuthEndpoint && !options.silent401) {
      try {
        const cloned = response.clone();
        const data = await cloned.json().catch(() => ({}));
        const detail = data?.detail || "";
        const isExplicitExpired = typeof detail === "string" && detail.toLowerCase().includes("expired");
        const hadPreviousSession = window.sessionStorage?.getItem("sportrisk_had_session") === "true";

        // Only dispatch session-expired if the token explicitly expired,
        // or if a previously authenticated session is now invalid
        if ((isExplicitExpired || (hadPreviousSession && detail !== "Not authenticated")) && !isHandling401) {
          isHandling401 = true;
          window.sessionStorage?.removeItem("sportrisk_had_session");
          setTimeout(() => {
            isHandling401 = false;
          }, 1000);
          window.dispatchEvent(
            new CustomEvent("session-expired", {
              detail: { message: "Your session has expired. Please log in again." },
            })
          );
        }
      } catch {
        // Ignore JSON parse errors
      }
    }
  }

  return response;
}

// Module-level fetch shadowing to guarantee credentials: "include" and 401 handling
const fetch = authFetch;


function getAuthHeaders() {
  const token = getAuthToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}


export async function registerUser(userData) {
  const response = await fetch(
    `${API_BASE_URL}/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Registration failed"
    );
  }

  return data;
}


export async function loginUser(credentials) {
  const cleanEmail = credentials.email ? credentials.email.trim().toLowerCase() : "";
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: cleanEmail,
        password: credentials.password,
      }),
      silent401: true,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Login failed"
    );
  }

  if (typeof window !== "undefined" && window.sessionStorage) {
    window.sessionStorage.setItem("sportrisk_had_session", "true");
  }

  return data;
}

export async function loginWithGoogle(credential) {
  const response = await fetch(
    `${API_BASE_URL}/auth/google`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        credential,
      }),
      silent401: true,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Google login failed"
    );
  }

  if (typeof window !== "undefined" && window.sessionStorage) {
    window.sessionStorage.setItem("sportrisk_had_session", "true");
  }

  return data;
}


export async function verifyPortalAccess(portalRole) {
  const response = await fetch(
    `${API_BASE_URL}/auth/verify-portal`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        portal_role: portalRole,
      }),
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Failed to verify portal access");
  }

  return data;
}


export async function getAuthMe(options = {}) {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "GET",
    headers: getAuthHeaders(),
    silent401: options.silent401 ?? false,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Not authenticated");
  }

  if (typeof window !== "undefined" && window.sessionStorage) {
    window.sessionStorage.setItem("sportrisk_had_session", "true");
  }

  return data;
}

export async function logoutUser() {
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      silent401: true,
    });
  } catch {
    // Ignore network error on logout
  } finally {
    if (typeof window !== "undefined") {
      window.sessionStorage?.removeItem("sportrisk_had_session");
      window.dispatchEvent(new CustomEvent("auth-logout"));
    }
    clearAuthSession();
  }
}

export async function getCurrentUser() {
  return getAuthMe();
}

export async function getAthleteProfile() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch athlete profile"
    );
  }

  return data;
}


export async function createAthleteProfile(profileData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(profileData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to create athlete profile"
    );
  }

  return data;
}


export async function updateAthleteProfile(profileData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(profileData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to update athlete profile"
    );
  }

  return data;
}

export async function updateCurrentUser(userData) {
  const response = await fetch(
    `${API_BASE_URL}/users/me`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(userData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update account");
  }

  return data;
}

export async function getCoachProfile() {
  const response = await fetch(
    `${API_BASE_URL}/coach/profile`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Coach profile");
  }

  return data;
}

export async function updateCoachProfile(profileData) {
  const response = await fetch(
    `${API_BASE_URL}/coach/profile`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(profileData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update Coach profile");
  }

  return data;
}

export async function getCoachDashboard() {
  const response = await fetch(
    `${API_BASE_URL}/coach/dashboard`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Coach dashboard");
  }

  return data;
}

export async function discoverAthletes(filters = {}) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.append(key, value);
    }
  });

  const query = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/discover${query}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to discover athletes");
  }

  return data;
}

export async function sendCoachConnectionRequest(athleteId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/connection-requests`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to send connection request");
  }

  return data;
}

export async function getCoachConnectedAthletes(filters = {}) {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.append(key, value);
    }
  });

  const query = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(
    `${API_BASE_URL}/coach/athletes${query}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch connected athletes");
  }

  return data;
}

export async function getCoachSentRequests() {
  const response = await fetch(
    `${API_BASE_URL}/coach/requests`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Coach requests");
  }

  return data;
}

export async function coachAcceptAthleteRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/requests/${relationshipId}/accept`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to accept connection request");
  }

  return data;
}

export async function coachRejectAthleteRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/requests/${relationshipId}/reject`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to reject connection request");
  }

  return data;
}



export async function getCoachAthleteProfile(athleteId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/profile`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch athlete profile");
  }

  return data;
}

export async function getCoachAthleteDetail(athleteId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch athlete detail");
  }

  return data;
}

export async function getCoachAthletePhysiotherapists(athleteId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/physiotherapists`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch assigned Physiotherapists");
  }

  return data;
}

export async function getAssignablePhysiotherapists(athleteId, search = "") {
  const params = new URLSearchParams();
  if (search) {
    params.append("search", search);
  }

  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/physiotherapists/available${query}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch verified Physiotherapists");
  }

  return data;
}

export async function assignPhysiotherapistToAthlete(athleteId, physiotherapistUserId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/physiotherapists/${physiotherapistUserId}/assign`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to assign Physiotherapist");
  }

  return data;
}

export async function getCoachAthleteAnalysis(athleteId, analysisId) {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/analyses/${analysisId}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch athlete analysis");
  }

  return data;
}

export async function downloadCoachAthleteReport(athleteId, videoId, fileType = "pdf") {
  const response = await fetch(
    `${API_BASE_URL}/coach/athletes/${athleteId}/videos/${videoId}/${fileType}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    let message = `Failed to download ${fileType.toUpperCase()} report`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileType === "pdf"
    ? `movement_analysis_report_${videoId}.pdf`
    : `video_${videoId}_timeseries.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export function getCoachAthleteTasks(athleteId) {
  return requestJson(`/coach/athletes/${athleteId}/tasks`, { method: "GET" });
}

export function createCoachAthleteTask(athleteId, taskData) {
  return requestJson(`/coach/athletes/${athleteId}/tasks`, {
    method: "POST",
    body: JSON.stringify(taskData),
  });
}

export function updateCoachAthleteTask(taskId, taskData) {
  return requestJson(`/coach/tasks/${taskId}`, {
    method: "PUT",
    body: JSON.stringify(taskData),
  });
}

export function cancelCoachAthleteTask(taskId) {
  return requestJson(`/coach/tasks/${taskId}/cancel`, { method: "POST" });
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...getAuthHeaders(),
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

function buildQuery(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== "") {
          params.append(key, item);
        }
      });
    } else if (value !== undefined && value !== null && value !== "") {
      params.append(key, value);
    }
  });
  return params.toString() ? `?${params.toString()}` : "";
}

export function getPhysiotherapistProfile() {
  return requestJson("/physiotherapist/profile", { method: "GET" });
}

export function updatePhysiotherapistProfile(profileData) {
  return requestJson("/physiotherapist/profile", {
    method: "PUT",
    body: JSON.stringify(profileData),
  });
}

export function getPhysiotherapistDashboard() {
  return requestJson("/physiotherapist/dashboard", { method: "GET" });
}

export function getSportsScientistProfile() {
  return requestJson("/sports-scientist/profile", { method: "GET" });
}

export function updateSportsScientistProfile(profileData) {
  return requestJson("/sports-scientist/profile", {
    method: "PUT",
    body: JSON.stringify(profileData),
  });
}

export function getSportsScientistDashboard() {
  return requestJson("/sports-scientist/dashboard", { method: "GET" });
}

export function getSportsScientistAthletes(filters = {}) {
  return requestJson(`/sports-scientist/athletes${buildQuery(filters)}`, { method: "GET" });
}

export function discoverSportsScientistAthletes(filters = {}) {
  return requestJson(`/sports-scientist/athletes/discover${buildQuery(filters)}`, { method: "GET" });
}

export function sendSportsScientistConnectionRequest(athleteId) {
  return requestJson(`/sports-scientist/athletes/${athleteId}/connection-requests`, { method: "POST" });
}

export function getSportsScientistRequests() {
  return requestJson("/sports-scientist/requests", { method: "GET" });
}

export function acceptSportsScientistIncomingRequest(relationshipId) {
  return requestJson(`/sports-scientist/requests/${relationshipId}/accept`, { method: "POST" });
}

export function rejectSportsScientistIncomingRequest(relationshipId) {
  return requestJson(`/sports-scientist/requests/${relationshipId}/reject`, { method: "POST" });
}

export function removeSportsScientistConnection(relationshipId) {
  return requestJson(`/sports-scientist/relationships/${relationshipId}/remove`, { method: "POST" });
}

export function getSportsScientistBiomechanicalAnalytics() {
  return requestJson("/sports-scientist/biomechanical-analytics", { method: "GET" });
}

export function getSportsScientistInjuryInsights(filters = {}) {
  return requestJson(`/sports-scientist/injury-insights${buildQuery(filters)}`, { method: "GET" });
}

export function getSportsScientistAthleteComparison(filters = {}) {
  return requestJson(`/sports-scientist/athlete-comparison${buildQuery(filters)}`, { method: "GET" });
}

export function getSportsScientistResearchReports(filters = {}) {
  return requestJson(`/sports-scientist/research-reports${buildQuery(filters)}`, { method: "GET" });
}

export async function downloadSportsScientistResearchReport(filters = {}) {
  const response = await fetch(
    `${API_BASE_URL}/sports-scientist/research-reports/pdf${buildQuery(filters)}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    let message = "Failed to download research report";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sports_scientist_research_report.pdf";
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export function discoverPhysiotherapistAthletes(filters = {}) {
  return requestJson(`/physiotherapist/athletes/discover${buildQuery(filters)}`, { method: "GET" });
}

export function sendPhysiotherapistConnectionRequest(athleteId) {
  return requestJson(`/physiotherapist/athletes/${athleteId}/connection-requests`, { method: "POST" });
}

export function getPhysiotherapistSentRequests() {
  return requestJson("/physiotherapist/requests", { method: "GET" });
}

export function acceptPhysiotherapistAssignedRequest(relationshipId) {
  return requestJson(`/physiotherapist/requests/${relationshipId}/accept`, { method: "POST" });
}

export function rejectPhysiotherapistAssignedRequest(relationshipId) {
  return requestJson(`/physiotherapist/requests/${relationshipId}/reject`, { method: "POST" });
}

export function getPhysiotherapistAthletes(filters = {}) {
  return requestJson(`/physiotherapist/athletes${buildQuery(filters)}`, { method: "GET" });
}

export function getPhysiotherapistAthleteDetail(athleteId) {
  return requestJson(`/physiotherapist/athletes/${athleteId}`, { method: "GET" });
}

export function getPhysiotherapistAthleteVideos(athleteId) {
  return requestJson(`/physiotherapist/athletes/${athleteId}/videos`, { method: "GET" });
}

export function getPhysiotherapistAthleteAnalysis(athleteId, analysisId) {
  return requestJson(`/physiotherapist/athletes/${athleteId}/analyses/${analysisId}`, { method: "GET" });
}

export function getPhysiotherapistAthleteVideoAnalysis(athleteId, videoId, analysisId = "") {
  const query = analysisId ? `?analysis_id=${analysisId}` : "";
  return requestJson(`/physiotherapist/athletes/${athleteId}/videos/${videoId}/analysis${query}`, { method: "GET" });
}

export function createRehabilitationPlan(athleteId, planData) {
  return requestJson(`/physiotherapist/athletes/${athleteId}/rehabilitation-plans`, {
    method: "POST",
    body: JSON.stringify(planData),
  });
}

export function updateRehabilitationPlan(planId, planData) {
  return requestJson(`/physiotherapist/rehabilitation-plans/${planId}`, {
    method: "PUT",
    body: JSON.stringify(planData),
  });
}

export function createRehabilitationActivity(planId, activityData) {
  return requestJson(`/physiotherapist/rehabilitation-plans/${planId}/activities`, {
    method: "POST",
    body: JSON.stringify(activityData),
  });
}

export function updateRehabilitationActivity(activityId, activityData) {
  return requestJson(`/physiotherapist/rehabilitation-activities/${activityId}`, {
    method: "PUT",
    body: JSON.stringify(activityData),
  });
}

export function deleteRehabilitationActivity(activityId) {
  return requestJson(`/physiotherapist/rehabilitation-activities/${activityId}`, {
    method: "DELETE",
  });
}

export function createPhysiotherapistNote(athleteId, noteData) {
  return requestJson(`/physiotherapist/athletes/${athleteId}/notes`, {
    method: "POST",
    body: JSON.stringify(noteData),
  });
}

export async function downloadRecoveryReport(athleteId, fileType = "pdf") {
  const response = await fetch(
    `${API_BASE_URL}/physiotherapist/athletes/${athleteId}/recovery-report/${fileType}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    let message = `Failed to download ${fileType.toUpperCase()} recovery report`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileType === "pdf"
    ? `recovery_report_${athleteId}.pdf`
    : `recovery_report_${athleteId}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function downloadPhysiotherapistAthleteReport(athleteId, videoId, fileType = "pdf") {
  const response = await fetch(
    `${API_BASE_URL}/physiotherapist/athletes/${athleteId}/videos/${videoId}/${fileType}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    let message = `Failed to download ${fileType.toUpperCase()} analysis report`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileType === "pdf"
    ? `movement_analysis_report_${videoId}.pdf`
    : `video_${videoId}_timeseries.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function getAthleteCoachRequests() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coach-requests`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Coach requests");
  }

  return data;
}

export async function getAthleteConnectedCoaches() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/connected-coaches`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch connected Coaches");
  }

  return data;
}

export async function acceptCoachRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coach-requests/${relationshipId}/accept`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to accept Coach request");
  }

  window.dispatchEvent(new Event("coach-connections-updated"));

  return data;
}

export async function rejectCoachRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coach-requests/${relationshipId}/reject`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to reject Coach request");
  }

  window.dispatchEvent(new Event("coach-connections-updated"));

  return data;
}

export async function revokeCoachAccess(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coaches/${relationshipId}/revoke`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to revoke Coach access");
  }

  window.dispatchEvent(new Event("coach-connections-updated"));

  return data;
}

export async function getAthletePhysiotherapistRequests() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/physiotherapist-requests`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Physiotherapist requests");
  }

  return data;
}

export async function getAthleteConnectedPhysiotherapists() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/connected-physiotherapists`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch connected Physiotherapists");
  }

  return data;
}

export async function acceptPhysiotherapistRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/physiotherapist-requests/${relationshipId}/accept`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to accept Physiotherapist request");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function rejectPhysiotherapistRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/physiotherapist-requests/${relationshipId}/reject`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to reject Physiotherapist request");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function revokePhysiotherapistAccess(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/physiotherapists/${relationshipId}/revoke`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to revoke Physiotherapist access");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function getAthleteSportsScientistRequests() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/sports-scientist-requests`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Sports Scientist requests");
  }

  return data;
}

export async function getAthleteConnectedSportsScientists() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/connected-sports-scientists`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch connected Sports Scientists");
  }

  return data;
}

export async function acceptSportsScientistRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/sports-scientist-requests/${relationshipId}/accept`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to accept Sports Scientist request");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function rejectSportsScientistRequest(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/sports-scientist-requests/${relationshipId}/reject`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to reject Sports Scientist request");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function revokeSportsScientistAccess(relationshipId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/sports-scientists/${relationshipId}/revoke`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to revoke Sports Scientist access");
  }

  window.dispatchEvent(new Event("professional-connections-updated"));

  return data;
}

export async function getMyRehabilitationPlans() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/rehabilitation-plans`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch rehabilitation plans");
  }

  return data;
}

export async function updateMyRehabilitationActivity(activityId, activityData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/rehabilitation-activities/${activityId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(activityData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update rehabilitation activity");
  }

  return data;
}

export async function getMyCoachTasks() {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coach-tasks`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch Coach tasks");
  }

  return data;
}

export async function updateMyCoachTask(taskId, taskData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/coach-tasks/${taskId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(taskData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update Coach task");
  }

  return data;
}

export function resolveApiAssetUrl(path) {
  if (!path) {
    return "";
  }

  const cleanPath = String(path).replace(/\\/g, "/").trim();

  try {
    const parsedUrl = new URL(cleanPath);
    if (parsedUrl.pathname.startsWith("/uploads/")) {
      return `${API_BASE_URL}${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`;
    }
    return cleanPath;
  } catch {
    // Relative paths are handled below.
  }

  const normalizedPath = cleanPath.startsWith("/") ? cleanPath : `/${cleanPath}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export async function submitProfessionalRoleRequest(requestData) {
  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(requestData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to submit professional role request");
  }

  return data;
}

export async function submitCoachApplication(applicationData) {
  const formData = new FormData();

  Object.entries(applicationData).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      formData.append(key, value);
    }
  });

  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests/coach`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to submit Coach application");
  }

  return data;
}

export async function submitPhysiotherapistApplication(applicationData) {
  const formData = new FormData();

  Object.entries(applicationData).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      formData.append(key, value);
    }
  });

  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests/physiotherapist`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to submit Physiotherapist application");
  }

  return data;
}

export async function submitSportsScientistApplication(applicationData) {
  const formData = new FormData();

  Object.entries(applicationData).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      formData.append(key, value);
    }
  });

  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests/sports-scientist`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to submit Sports Scientist application");
  }

  return data;
}

export async function getMyProfessionalRoleRequests() {
  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests/me`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch professional role requests");
  }

  return data;
}

export async function getMyProfessionalRoleRequestStatus() {
  const response = await fetch(
    `${API_BASE_URL}/professional-role-requests/me/status`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (response.status === 204) {
    return null;
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch professional role request status");
  }

  return data;
}

export async function getAdminProfessionalRoleRequests(filters = {}) {
  const params = new URLSearchParams();

  if (typeof filters === "string") {
    if (filters) {
      params.append("request_status", filters);
    }
  } else {
    if (filters.requestStatus) {
      params.append("request_status", filters.requestStatus);
    }

    if (filters.requestedRole) {
      params.append("requested_role", filters.requestedRole);
    }

    if (filters.search) {
      params.append("search", filters.search);
    }
  }

  const query = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(
    `${API_BASE_URL}/admin/professional-role-requests${query}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch professional requests");
  }

  return data;
}

export function getAdminDashboard(filters = {}) {
  return requestJson(`/admin/dashboard${buildQuery(filters)}`, { method: "GET" });
}

export function getAdminPlatformAnalytics(filters = {}) {
  return requestJson(`/admin/analytics${buildQuery(filters)}`, { method: "GET" });
}

export function getAdminSystemMonitoring(filters = {}) {
  return requestJson(`/admin/system-monitoring${buildQuery(filters)}`, { method: "GET" });
}

export function getNotifications(filters = {}) {
  return requestJson(`/notifications${buildQuery(filters)}`, { method: "GET" });
}

export function getNotificationUnreadCount() {
  return requestJson("/notifications/unread-count", { method: "GET" });
}

export function markNotificationRead(notificationId) {
  return requestJson(`/notifications/${notificationId}/read`, { method: "PATCH" });
}

export function markNotificationUnread(notificationId) {
  return requestJson(`/notifications/${notificationId}/unread`, { method: "PATCH" });
}

export function markAllNotificationsRead() {
  return requestJson("/notifications/read-all", { method: "PATCH" });
}

export function getAdminReports(filters = {}) {
  return requestJson(`/admin/reports${buildQuery(filters)}`, { method: "GET" });
}

export function getAdminProfile() {
  return requestJson("/admin/profile", { method: "GET" });
}

export function updateAdminProfile(profileData) {
  return requestJson("/admin/profile", {
    method: "PUT",
    body: JSON.stringify(profileData),
  });
}

export function changeAdminPassword(passwordData) {
  return requestJson("/admin/profile/password", {
    method: "POST",
    body: JSON.stringify(passwordData),
  });
}

export function getAdminReportDetail(reportId) {
  return requestJson(`/admin/reports/${reportId}`, { method: "GET" });
}

export async function downloadAdminReportPdf(reportId) {
  const response = await fetch(
    `${API_BASE_URL}/admin/reports/${reportId}/pdf`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    let message = "Failed to download report";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `admin_report_${reportId}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export function getAdminUsers(filters = {}) {
  return requestJson(`/admin/users${buildQuery(filters)}`, { method: "GET" });
}

export function getAdminUserDetail(userId) {
  return requestJson(`/admin/users/${userId}`, { method: "GET" });
}

export function createAdministrator(adminData) {
  return requestJson("/admin/users/administrators", {
    method: "POST",
    body: JSON.stringify(adminData),
  });
}

export async function getAdminProfessionalRoleRequest(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/admin/professional-role-requests/${requestId}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch professional request");
  }

  return data;
}

export async function approveProfessionalRoleRequest(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/admin/professional-role-requests/${requestId}/approve`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to approve professional request");
  }

  window.dispatchEvent(new Event("user-role-updated"));

  return data;
}

export async function rejectProfessionalRoleRequest(requestId, rejectionReason) {
  const response = await fetch(
    `${API_BASE_URL}/admin/professional-role-requests/${requestId}/reject`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        rejection_reason: rejectionReason || "",
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to reject professional request");
  }

  return data;
}

export async function getInjuryHistory(athleteId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/${athleteId}/injury-history`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch injury history");
  }

  return data;
}

export async function createInjuryHistory(athleteId, injuryData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/${athleteId}/injury-history`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(injuryData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to add injury history");
  }

  return data;
}

export async function updateInjuryHistory(athleteId, injuryId, injuryData) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/${athleteId}/injury-history/${injuryId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(injuryData),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update injury history");
  }

  return data;
}

export async function deleteInjuryHistory(athleteId, injuryId) {
  const response = await fetch(
    `${API_BASE_URL}/athletes/${athleteId}/injury-history/${injuryId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let message = "Failed to delete injury history";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {}
    throw new Error(message);
  }

  return true;
}

export async function uploadVideo(videoFile, activity) {
  const formData = new FormData();

  formData.append("file", videoFile);

  if (activity) {
    formData.append("activity", activity);
  }

  const response = await fetch(
    `${API_BASE_URL}/videos/upload`,
    {
      method: "POST",

      headers: {
        ...getAuthHeaders(),
      },

      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Video upload failed"
    );
  }

  return data;
}

export async function getMyVideos() {
  const response = await fetch(
    `${API_BASE_URL}/videos`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch videos"
    );
  }

  return data;
}

export async function deleteVideo(videoId) {
  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let message = "Failed to delete video";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // 204 response has no body
    }

    throw new Error(message);
  }

  return true;
}

export async function analyzeVideo(videoId) {
  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}/analyze`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Video analysis failed"
    );
  }

  return data;
}

export async function getVideoDetails(videoId) {
  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch video details"
    );
  }

  return data;
}

export async function triggerMovementAnalysis(videoId, options = {}) {
  const response = await fetch(
    options.force ? `${API_BASE_URL}/analysis/${videoId}?force=true` : `${API_BASE_URL}/analysis/${videoId}`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to start movement analysis"
    );
  }

  return data;
}

export async function getMovementAnalysisStatus(videoId, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/${videoId}/status`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
      signal: options.signal,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(
      data.detail || "Failed to fetch analysis status"
    );
    error.status = response.status;
    error.retryAfter = response.headers.get("Retry-After");
    throw error;
  }

  return data;
}

export async function getMovementAnalysisResult(videoId) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/${videoId}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch analysis results"
    );
  }

  return data;
}

export async function getAnalysisHistory() {
  const response = await fetch(
    `${API_BASE_URL}/analysis/history`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch analysis history");
  }

  return data;
}

export async function getAnalysisById(analysisId) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/history/${analysisId}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch analysis");
  }

  return data;
}

export async function downloadReportFile(videoId, fileType = "csv") {
  let endpoint = `${API_BASE_URL}/analysis/${videoId}/${fileType}`;
  let defaultFilename = `movement_analysis_${videoId}.${fileType}`;

  if (fileType === "ml-dataset") {
    endpoint = `${API_BASE_URL}/analysis/ml-dataset/master`;
    defaultFilename = "ml_dataset.csv";
  } else if (fileType === "ml-csv") {
    endpoint = `${API_BASE_URL}/analysis/${videoId}/ml-csv`;
    defaultFilename = `video_${videoId}_ml.csv`;
  } else if (fileType === "csv") {
    endpoint = `${API_BASE_URL}/analysis/${videoId}/csv`;
    defaultFilename = `video_${videoId}_timeseries.csv`;
  } else if (fileType === "pdf") {
    endpoint = `${API_BASE_URL}/analysis/${videoId}/pdf`;
    defaultFilename = `movement_analysis_report_${videoId}.pdf`;
  }

  const response = await fetch(endpoint, {
    method: "GET",
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    let errMessage = "Download failed";
    try {
      const err = await response.json();
      errMessage = err.detail || errMessage;
    } catch {}
    throw new Error(errMessage);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = defaultFilename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

