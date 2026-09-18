import React from "react";
import { CalendarClock, Film, Play, Upload } from "lucide-react";

function LatestVideo({ video, status, formatDate, onNavigate }) {
  if (!video) {
    return (
      <section className="athlete-dashboard-card compact-card">
        <div className="athlete-empty-mini">
          <Film size={24} />
          <h2>No videos yet</h2>
          <p>Upload your first sports video to start movement analysis.</p>
          <button
            className="athlete-action-button"
            onClick={() => onNavigate("/video-upload")}
            type="button"
          >
            <Upload size={17} />
            <span>Upload Video</span>
          </button>
        </div>
      </section>
    );
  }

  const isCompleted = status === "Completed";
  const actionLabel = isCompleted ? "View Analysis" : "Analyze Video";

  return (
    <section className="athlete-dashboard-card compact-card">
      <div className="athlete-card-header">
        <div>
          <h2>Latest Video</h2>
          <p>Most recent upload in your library.</p>
        </div>
        <span className={`latest-status ${status.toLowerCase()}`}>
          {status}
        </span>
      </div>

      <div className="latest-video-body">
        <div className="latest-video-icon">
          <Film size={22} />
        </div>
        <div>
          <h3>{video.activity || "Untitled Activity"}</h3>
          <p>
            <CalendarClock size={14} />
            Uploaded {formatDate(video.uploaded_at)}
          </p>
        </div>
      </div>

      <button
        className="athlete-action-button full-width"
        onClick={() => onNavigate(`/analysis/${video.video_id}`)}
        type="button"
      >
        <Play size={17} />
        <span>{actionLabel}</span>
      </button>
    </section>
  );
}

export default LatestVideo;
