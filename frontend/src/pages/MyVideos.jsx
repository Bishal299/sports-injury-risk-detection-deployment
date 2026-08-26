import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../layouts/DashboardLayout";
import {
  Activity,
  Trash2,
  Upload,
  Plus,
  Clock,
  Video as VideoIcon,
  Play,
  Film,
  AlertCircle
} from "lucide-react";

import {
  getMyVideos,
  deleteVideo,
  analyzeVideo
} from "../services/api";

import "../styles/my-videos.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const formatMediaUrl = (url) => {
  if (!url) return "";
  const clean = url.replace(/\\/g, "/");
  if (clean.startsWith("http://") || clean.startsWith("https://")) {
    return clean;
  }
  const normalizedPath = clean.startsWith("/") ? clean : `/${clean}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

const formatDate = (dateString) => {
  if (!dateString) return "Recently";
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  } catch {
    return dateString;
  }
};

function MyVideos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [analyzingId, setAnalyzingId] = useState(null);
  const navigate = useNavigate();

  // -----------------------------
  // Load Videos
  // -----------------------------
  useEffect(() => {
    const loadVideos = async () => {
      try {
        const data = await getMyVideos();
        setVideos(data || []);
      } catch (err) {
        setError(err.message || "Failed to load videos.");
      } finally {
        setLoading(false);
      }
    };

    loadVideos();
  }, []);

  const handleAnalysis = (videoId) => {
    navigate(`/analysis/${videoId}`);
  };

  // -----------------------------
  // Delete Video
  // -----------------------------
  const handleDelete = async (videoId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this video? This will also remove any generated movement analysis data."
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(videoId);
      setError("");

      await deleteVideo(videoId);

      setVideos((currentVideos) =>
        currentVideos.filter((video) => video.video_id !== videoId)
      );
    } catch (err) {
      setError(err.message || "Failed to delete video.");
    } finally {
      setDeletingId(null);
    }
  };

  // -----------------------------
  // Loading State
  // -----------------------------
  if (loading) {
    return (
      <DashboardLayout>
        <div className="videos-page">
          <div className="videos-loading">
            <div className="loading-spinner"></div>
            <p>Loading your training video library...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // -----------------------------
  // Critical Error State (No videos loaded)
  // -----------------------------
  if (error && videos.length === 0) {
    return (
      <DashboardLayout>
        <div className="videos-page">
          <div className="videos-header">
            <div>
              <p className="page-eyebrow">VIDEO LIBRARY</p>
              <h1>My Videos</h1>
              <p className="page-description">Review and manage your uploaded training videos.</p>
            </div>
          </div>

          <div className="videos-error">
            <div className="error-icon">
              <AlertCircle size={24} />
            </div>
            <h2>Unable to load videos</h2>
            <p>{error}</p>
            <button
              className="secondary-button"
              onClick={() => navigate("/dashboard")}
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // -----------------------------
  // Main UI
  // -----------------------------
  return (
    <DashboardLayout>
      <div className="videos-page">
        {/* Header */}
        <div className="videos-header">
          <div>
            <p className="page-eyebrow">VIDEO LIBRARY</p>
            <h1>My Videos</h1>
            <p className="page-description">
              Review and manage your uploaded training videos.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => navigate("/video-upload")}
          >
            <Plus size={16} />
            <span>Upload Video</span>
          </button>
        </div>

        {/* Inline Error Notice */}
        {error && <div className="inline-error">{error}</div>}

        {/* Empty State */}
        {videos.length === 0 ? (
          <div className="empty-videos">
            <div className="empty-video-icon">
              <Film size={26} />
            </div>
            <h2>No videos yet</h2>
            <p>
              Upload your first training video to start extracting biomechanical movement features and kinematic data.
            </p>
            <button
              className="primary-button"
              onClick={() => navigate("/video-upload")}
            >
              <Plus size={16} />
              <span>Upload Video</span>
            </button>
          </div>
        ) : (
          <>
            {/* Video Library Info Bar */}
            <div className="video-library-info">
              <div className="video-count-badge">
                <span>Total:</span>
                <strong>
                  {videos.length} {videos.length === 1 ? "video" : "videos"}
                </strong>
              </div>
            </div>

            {/* Video List (Compact Horizontal Cards) */}
            <div className="videos-list">
              {videos.map((video) => {
                const videoUrl = formatMediaUrl(video.video_url);
                const rawStatus = (video.processing_status || "uploaded").toLowerCase();
                const isAnalyzing = analyzingId === video.video_id || rawStatus === "processing";
                const isCompleted = rawStatus === "analyzed" || rawStatus === "completed";

                let statusBadgeClass = "status-uploaded";
                let statusLabel = "Uploaded";
                let statusIcon = <span className="status-dot">○</span>;

                if (isCompleted) {
                  statusBadgeClass = "status-analyzed";
                  statusLabel = "Analyzed";
                  statusIcon = <span className="status-dot">●</span>;
                } else if (isAnalyzing) {
                  statusBadgeClass = "status-processing";
                  statusLabel = "Analyzing...";
                  statusIcon = <span className="status-dot-pulse">◌</span>;
                }

                return (
                  <article className="video-card" key={video.video_id}>
                    {/* Left: Compact Video Preview & Player */}
                    <div className="video-preview">
                      <div className="video-preview-overlay-tag">
                        <VideoIcon size={12} />
                        <span>HD Preview</span>
                      </div>
                      <video
                        controls
                        preload="metadata"
                        playsInline
                        src={videoUrl}
                      >
                        <source src={videoUrl} type="video/mp4" />
                        Your browser does not support video playback.
                      </video>
                    </div>

                    {/* Right: Video Information, Metadata & Actions */}
                    <div className="video-card-content">
                      {/* Top Row: Title, Upload Date & Status Badge */}
                      <div className="video-title-row">
                        <div className="video-title-group">
                          <h2>{video.activity || "Untitled Activity"}</h2>
                          <p className="video-upload-date">
                            <Clock size={12} />
                            <span>Uploaded {formatDate(video.uploaded_at)}</span>
                          </p>
                        </div>

                        <span className={`video-status-badge ${statusBadgeClass}`}>
                          {statusIcon}
                          <span>{statusLabel}</span>
                        </span>
                      </div>

                      {/* Middle: Compact Metadata Badges */}
                      <div className="video-metadata">
                        <div className="metadata-item">
                          <span className="metadata-label">Duration</span>
                          <strong>
                            {video.duration != null
                              ? `${Number(video.duration).toFixed(1)}s`
                              : "—"}
                          </strong>
                        </div>

                        <div className="metadata-item">
                          <span className="metadata-label">Frame Rate</span>
                          <strong>{video.fps ? `${video.fps} FPS` : "—"}</strong>
                        </div>

                        <div className="metadata-item">
                          <span className="metadata-label">Resolution</span>
                          <strong>{video.resolution || "—"}</strong>
                        </div>
                      </div>

                      {/* Bottom: Action Buttons */}
                      <div className="video-actions">
                        <button
                          className="primary-button"
                          onClick={() => handleAnalysis(video.video_id)}
                          disabled={analyzingId === video.video_id}
                          title="Open AI Movement Analysis"
                        >
                          <Activity size={15} />
                          <span>{analyzingId === video.video_id ? "Analyzing..." : "Analysis"}</span>
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => navigate("/video-upload")}
                          title="Upload a new video"
                        >
                          <Upload size={15} />
                          <span>Upload Another</span>
                        </button>

                        <button
                          className="delete-button"
                          onClick={() => handleDelete(video.video_id)}
                          disabled={deletingId === video.video_id}
                          title="Delete this video"
                        >
                          <Trash2 size={15} />
                          <span>{deletingId === video.video_id ? "Deleting..." : "Delete"}</span>
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

export default MyVideos;