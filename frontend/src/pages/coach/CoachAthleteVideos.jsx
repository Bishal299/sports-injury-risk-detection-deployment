import React, { useEffect, useState } from "react";
import { ArrowLeft, BarChart3, Clock, Play, Video } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { getCoachAthleteDetail, resolveApiAssetUrl } from "../../services/api";
import "../../styles/coach.css";
import "../../styles/my-videos.css";

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatStatus(value) {
  if (!value) return "Not available";
  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "completed" || normalized === "analyzed") return "status-analyzed";
  if (normalized === "processing") return "status-processing";
  if (["failed", "error", "processing_failed"].includes(normalized)) return "status-failed";
  return "status-uploaded";
}

function CoachAthleteVideos() {
  const { athleteId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadVideos() {
      setLoading(true);
      setError("");
      try {
        const data = await getCoachAthleteDetail(athleteId);
        if (!cancelled) setDetail(data);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load athlete videos.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadVideos();
    return () => {
      cancelled = true;
    };
  }, [athleteId]);

  const profile = detail?.profile;
  const videos = Array.isArray(detail?.videos) ? detail.videos : [];

  return (
    <main className="coach-page">
      <button className="coach-back-button" type="button" onClick={() => navigate("/coach/videos")}>
        <ArrowLeft size={18} />
        Back to Videos
      </button>

      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">ATHLETE VIDEOS</p>
          <h1>{profile?.name || "Athlete Videos"}</h1>
          <p>{profile?.sport || "Sport not set"}</p>
        </div>
        <Video size={28} />
      </section>

      {error && <section className="coach-error-card">{error}</section>}
      {loading && <section className="coach-empty-card">Loading athlete videos...</section>}

      {!loading && !error && videos.length === 0 && (
        <section className="coach-empty-card">
          <h2>No videos uploaded yet.</h2>
          <p>This athlete does not have uploaded videos available to your active Coach relationship.</p>
        </section>
      )}

      {!loading && !error && videos.length > 0 && (
        <section className="videos-list">
          {videos.map((video) => {
            const analysisReady = Boolean(video.latest_analysis_id);
            const analysisStatus = video.analysis_status || video.processing_status;

            return (
              <article className="video-card" key={video.video_id}>
                <div className="video-preview">
                  <div className="video-preview-overlay-tag">
                    <Video size={12} />
                    <span>Video</span>
                  </div>
                  {video.video_url ? (
                    <video controls crossOrigin="anonymous" preload="metadata" playsInline src={resolveApiAssetUrl(video.video_url)} />
                  ) : (
                    <div className="coach-quiet-state">Preview not available</div>
                  )}
                </div>

                <div className="video-card-content">
                  <div className="video-title-row">
                    <div className="video-title-group">
                      <h2>{video.activity || "Untitled Video"}</h2>
                      <p className="video-upload-date">
                        <Clock size={12} />
                        <span>Uploaded {formatDate(video.uploaded_at)}</span>
                      </p>
                    </div>
                    <span className={`video-status-badge ${statusClass(analysisStatus)}`}>
                      <span>{formatStatus(analysisStatus)}</span>
                    </span>
                  </div>

                  <div className="video-metadata">
                    <div className="metadata-item">
                      <span className="metadata-label">Duration</span>
                      <strong>{video.duration != null ? `${Number(video.duration).toFixed(1)}s` : "-"}</strong>
                    </div>
                    <div className="metadata-item">
                      <span className="metadata-label">Analysis</span>
                      <strong>{formatStatus(analysisStatus)}</strong>
                    </div>
                    <div className="metadata-item">
                      <span className="metadata-label">Risk</span>
                      <strong>{video.latest_risk_score ?? video.risk_category ?? "-"}</strong>
                    </div>
                  </div>

                  <div className="video-actions">
                    <button
                      className="primary-button"
                      type="button"
                      disabled={!analysisReady}
                      onClick={() => navigate(`/coach/athletes/${athleteId}/analysis/${video.video_id}?analysisId=${video.latest_analysis_id}`)}
                      title={analysisReady ? "Open stored movement analysis" : "No stored analysis is available for this video"}
                    >
                      {analysisReady ? <Play size={15} /> : <BarChart3 size={15} />}
                      <span>View Analysis</span>
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}

export default CoachAthleteVideos;
