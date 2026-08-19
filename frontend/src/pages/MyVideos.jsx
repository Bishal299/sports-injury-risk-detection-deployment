import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../layouts/DashboardLayout";

import {
  getMyVideos,
  deleteVideo,
  analyzeVideo
} from "../services/api";

import "../styles/my-videos.css";


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

        setVideos(data);

      } catch (error) {

        setError(error.message);

      } finally {

        setLoading(false);

      }

    };

    loadVideos();

  }, []);
  
  const handleAnalysis = async (videoId) => {
  try {
    setAnalyzingId(videoId);
    setError("");

    await analyzeVideo(videoId);

    setVideos((currentVideos) =>
      currentVideos.map((video) =>
        video.video_id === videoId
          ? {
              ...video,
              processing_status: "frames_extracted"
            }
          : video
      )
    );

  } catch (error) {

    setError(error.message);

  } finally {

    setAnalyzingId(null);

  }
};

  // -----------------------------
  // Delete Video
  // -----------------------------

  const handleDelete = async (videoId) => {

    const confirmed = window.confirm(
      "Are you sure you want to delete this video?"
    );

    if (!confirmed) {
      return;
    }

    try {

      setDeletingId(videoId);
      setError("");

      await deleteVideo(videoId);

      setVideos((currentVideos) =>
        currentVideos.filter(
          (video) => video.video_id !== videoId
        )
      );

    } catch (error) {

      setError(error.message);

    } finally {

      setDeletingId(null);

    }

  };


  // -----------------------------
  // Loading
  // -----------------------------

  if (loading) {

    return (
      <div className="videos-page">

        <div className="videos-loading">

          <div className="loading-spinner"></div>

          <p>Loading your videos...</p>

        </div>

      </div>
    );

  }


  // -----------------------------
  // Error
  // -----------------------------

  if (error && videos.length === 0) {

    return (
      <div className="videos-page">

        <div className="videos-header">

          <div>

            <p className="page-eyebrow">
              VIDEO LIBRARY
            </p>

            <h1>My Videos</h1>

            <p>
              Manage your uploaded training videos.
            </p>

          </div>

        </div>


        <div className="videos-error">

          <div className="error-icon">
            !
          </div>

          <h2>Unable to load videos</h2>

          <p>
            {error}
          </p>

          <button
            className="secondary-button"
            onClick={() => navigate("/dashboard")}
          >
            Back to Dashboard
          </button>

        </div>

      </div>
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

          <p className="page-eyebrow">
            VIDEO LIBRARY
          </p>

          <h1>
            My Videos
          </h1>

          <p className="page-description">
            Review and manage your uploaded training videos.
          </p>

        </div>


        <button
          className="primary-button"
          onClick={() => navigate("/video-upload")}
        >
          <span>+</span>
          Upload Video
        </button>

      </div>


      {/* Error while deleting */}

      {error && (

        <div className="inline-error">
          {error}
        </div>

      )}


      {/* Empty State */}

      {videos.length === 0 ? (

        <div className="empty-videos">

          <div className="empty-video-icon">
            ▶
          </div>

          <h2>
            No videos yet
          </h2>

          <p>
            Upload your first training video to start
            monitoring your sports performance.
          </p>

          <button
            className="primary-button"
            onClick={() => navigate("/video-upload")}
          >
            Upload Your First Video
          </button>

        </div>

      ) : (

        <>

          {/* Video count */}

          <div className="video-library-info">

            <span>
              {videos.length}{" "}
              {videos.length === 1 ? "video" : "videos"}
            </span>

          </div>


          {/* Video Grid */}

          <div className="videos-grid">

            {videos.map((video) => {

              const videoUrl =
                video.video_url.startsWith("http")
                  ? video.video_url
                  : `http://127.0.0.1:8000${video.video_url}`;


              return (

                <article
                  className="video-card"
                  key={video.video_id}
                >


                  {/* Video */}

                  <div className="video-preview">

                    <video
                      controls
                      preload="metadata"
                    >

                      <source
                        src={videoUrl}
                        type="video/mp4"
                      />

                      Your browser does not support video playback.

                    </video>

                  </div>


                  {/* Content */}

                  <div className="video-card-content">


                    {/* Title + status */}

                    <div className="video-title-row">

                      <div>

                        <h2>
                          {video.activity ||
                            "Untitled Activity"}
                        </h2>

                        <p className="video-upload-date">
                          Uploaded{" "}
                          {new Date(
                            video.uploaded_at
                          ).toLocaleDateString()}
                        </p>

                      </div>


                      <span className="video-status">
                        {video.processing_status ||
                          "Uploaded"}
                      </span>

                    </div>


                    {/* Metadata */}

                    <div className="video-metadata">


                      <div className="metadata-item">

                        <span className="metadata-label">
                          Duration
                        </span>

                        <strong>
                          {video.duration != null
                            ? `${Number(video.duration).toFixed(1)}s`
                            : "—"}
                        </strong>

                      </div>


                      <div className="metadata-item">

                        <span className="metadata-label">
                          FPS
                        </span>

                        <strong>
                          {video.fps || "—"}
                        </strong>

                      </div>


                      <div className="metadata-item">

                        <span className="metadata-label">
                          Resolution
                        </span>

                        <strong>
                          {video.resolution || "—"}
                        </strong>

                      </div>


                   </div>
                  </div>

                    {/* Actions */}

             {/* Actions */}

                    <div className="video-actions">

                      <button
                        className="primary-button"
                        onClick={() => handleAnalysis(video.video_id)}
                        disabled={analyzingId === video.video_id}
                      >
                        {analyzingId === video.video_id
                          ? "Analyzing..."
                          : "Analysis"}
                      </button>

                      <button
                        className="secondary-button"
                        onClick={() => navigate("/video-upload")}
                      >
                        Upload Another
                      </button>

                      <button
                        className="delete-button"
                        onClick={() => handleDelete(video.video_id)}
                        disabled={deletingId === video.video_id}
                      >
                        {deletingId === video.video_id
                          ? "Deleting..."
                          : "Delete"}
                      </button>

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