const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


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
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Login failed"
    );
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
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Google login failed"
    );
  }

  return data;
}


export async function getCurrentUser() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/users/me`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch user"
    );
  }

  return data;
}

export async function getAthleteProfile() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/athletes/profile`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
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

export async function uploadVideo(videoFile, activity) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

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
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/videos`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}/analyze`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
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
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
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

export async function triggerMovementAnalysis(videoId) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/analysis/${videoId}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
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

export async function getMovementAnalysisStatus(videoId) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/analysis/${videoId}/status`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to fetch analysis status"
    );
  }

  return data;
}

export async function getMovementAnalysisResult(videoId) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/analysis/${videoId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
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

export async function downloadReportFile(videoId, fileType = "csv") {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const endpoint = `${API_BASE_URL}/analysis/${videoId}/${fileType}`;
  const response = await fetch(endpoint, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
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
  a.download = `movement_analysis_${videoId}.${fileType}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}