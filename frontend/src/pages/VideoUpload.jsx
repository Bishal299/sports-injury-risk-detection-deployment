import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadVideo } from "../services/api";
import DashboardLayout from "../layouts/DashboardLayout";

import "../styles/video-upload.css";


function VideoUpload() {

  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [videoFile, setVideoFile] = useState(null);
  const [activity, setActivity] = useState("");

  const [uploading, setUploading] = useState(false);

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [uploadedVideo, setUploadedVideo] = useState(null);

  const [dragActive, setDragActive] = useState(false);


  // -----------------------------
  // Select File
  // -----------------------------

  const selectFile = (file) => {

    if (!file) {
      return;
    }

    setSuccess("");
    setError("");
    setUploadedVideo(null);

    if (!file.type.startsWith("video/")) {
      setError("Please select a valid video file.");
      return;
    }

    setVideoFile(file);
  };


  const handleFileChange = (event) => {

    const file = event.target.files[0];

    selectFile(file);

  };


  // -----------------------------
  // Drag & Drop
  // -----------------------------

  const handleDragOver = (event) => {

    event.preventDefault();

    setDragActive(true);

  };


  const handleDragLeave = (event) => {

    event.preventDefault();

    setDragActive(false);

  };


  const handleDrop = (event) => {

    event.preventDefault();

    setDragActive(false);

    const file = event.dataTransfer.files[0];

    selectFile(file);

  };


  // -----------------------------
  // Upload
  // -----------------------------

  const handleUpload = async (event) => {

    event.preventDefault();

    setSuccess("");
    setError("");

    if (!videoFile) {

      setError(
        "Please select a video file before uploading."
      );

      return;
    }


    try {

      setUploading(true);

      const data = await uploadVideo(
        videoFile,
        activity
      );

      setUploadedVideo(data);

      setSuccess(
        "Video uploaded successfully!"
      );

      setVideoFile(null);
      setActivity("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

    } catch (error) {

      setError(error.message);

    } finally {

      setUploading(false);

    }

  };


  // -----------------------------
  // Format File Size
  // -----------------------------

  const formatFileSize = (bytes) => {

    if (!bytes) {
      return "0 MB";
    }

    const mb = bytes / (1024 * 1024);

    if (mb < 1) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${mb.toFixed(1)} MB`;

  };


  return (
   <DashboardLayout> 
    <div className="upload-page">


      {/* HEADER */}

      <div className="upload-header">

        <div>

          <p className="page-eyebrow">
            VIDEO ANALYSIS
          </p>

          <h1>
            Upload Training Video
          </h1>

          <p>
            Upload a sports video for injury-risk analysis.
          </p>

        </div>


        <button
          type="button"
          className="upload-back-button"
          onClick={() => navigate("/my-videos")}
        >
          ← My Videos
        </button>

      </div>


      {/* SUCCESS */}

      {success && (

        <div className="upload-success">

          <div className="success-icon">
            ✓
          </div>

          <div>

            <strong>
              Video uploaded successfully
            </strong>

            <p>
              Your video has been added to your video library.
            </p>

          </div>

        </div>

      )}


      {/* ERROR */}

      {error && (

        <div className="upload-error">

          <div className="error-icon">
            !
          </div>

          <p>
            {error}
          </p>

        </div>

      )}


      <form
        className="upload-form"
        onSubmit={handleUpload}
      >


        {/* VIDEO UPLOAD AREA */}

        <section className="upload-section">

          <div className="upload-section-heading">

            <div className="upload-section-number">
              01
            </div>

            <div>

              <h2>
                Select Video
              </h2>

              <p>
                Choose a training or sports video from your device.
              </p>

            </div>

          </div>


          <div
            className={`drop-zone ${
              dragActive ? "drop-zone-active" : ""
            } ${
              videoFile ? "drop-zone-selected" : ""
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() =>
              fileInputRef.current?.click()
            }
          >

            <input
              ref={fileInputRef}
              type="file"
              accept="video/mp4,video/mov,video/avi,video/x-matroska,video/*"
              onChange={handleFileChange}
              hidden
            />


            {!videoFile ? (

              <>

                <div className="upload-icon">
                  ↑
                </div>

                <h3>
                  Drop your video here
                </h3>

                <p>
                  or <span>browse files</span>
                </p>

                <small>
                  MP4, MOV, AVI or MKV
                </small>

              </>

            ) : (

              <>

                <div className="selected-file-icon">
                  ✓
                </div>

                <h3>
                  {videoFile.name}
                </h3>

                <p>
                  {formatFileSize(videoFile.size)}
                </p>

                <span className="change-file">
                  Click to change video
                </span>

              </>

            )}

          </div>

        </section>


        {/* ACTIVITY */}

        <section className="upload-section">

          <div className="upload-section-heading">

            <div className="upload-section-number">
              02
            </div>

            <div>

              <h2>
                Activity
              </h2>

              <p>
                Tell us what activity is shown in the video.
              </p>

            </div>

          </div>


          <div className="activity-field">

            <label htmlFor="activity">
              Activity
            </label>

            <input
              id="activity"
              type="text"
              value={activity}
              onChange={(event) =>
                setActivity(event.target.value)
              }
              placeholder="e.g. Running, Squat, Football"
            />

            <span>
              This helps organize your video library.
            </span>

          </div>

        </section>


        {/* SELECTED VIDEO */}

        {videoFile && (

          <section className="selected-video-card">

            <div className="selected-video-info">

              <div className="file-preview-icon">
                ▶
              </div>

              <div>

                <strong>
                  {videoFile.name}
                </strong>

                <p>
                  {formatFileSize(videoFile.size)}
                </p>

              </div>

            </div>

            <span className="ready-badge">
              Ready
            </span>

          </section>

        )}


        {/* UPLOAD BUTTON */}

        <div className="upload-actions">

          <button
            type="button"
            className="cancel-upload-button"
            onClick={() =>
              navigate("/my-videos")
            }
            disabled={uploading}
          >
            Cancel
          </button>


          <button
            type="submit"
            className="submit-upload-button"
            disabled={uploading || !videoFile}
          >

            {uploading ? (

              <>
                <span className="upload-spinner"></span>
                Uploading...
              </>

            ) : (

              <>
                ↑ Upload Video
              </>

            )}

          </button>

        </div>


      </form>


      {/* UPLOAD RESULT */}

      {uploadedVideo && (

        <section className="upload-result">

          <div className="result-header">

            <div className="result-success-icon">
              ✓
            </div>

            <div>

              <h2>
                Upload Complete
              </h2>

              <p>
                Your video is now available in your library.
              </p>

            </div>

          </div>


          <div className="result-grid">

            <div>
              <span>Activity</span>
              <strong>
                {uploadedVideo.activity || "Not specified"}
              </strong>
            </div>


            <div>
              <span>Status</span>
              <strong>
                {uploadedVideo.processing_status}
              </strong>
            </div>


            <div>
              <span>Duration</span>
              <strong>
                {uploadedVideo.duration != null
                  ? `${Number(uploadedVideo.duration).toFixed(1)} sec`
                  : "—"}
              </strong>
            </div>


            <div>
              <span>FPS</span>
              <strong>
                {uploadedVideo.fps || "—"}
              </strong>
            </div>


            <div>
              <span>Resolution</span>
              <strong>
                {uploadedVideo.resolution || "—"}
              </strong>
            </div>

          </div>


          <button
            type="button"
            className="view-videos-button"
            onClick={() =>
              navigate("/my-videos")
            }
          >
            View My Videos →
          </button>

        </section>

      )}

    </div>
   </DashboardLayout>
  );

}


export default VideoUpload;