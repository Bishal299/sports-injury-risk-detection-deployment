import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useVideoUpload } from "../../context/VideoUploadContext";

import "../../styles/video-upload.css";


function VideoUpload() {

  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const { uploadState, startUpload } = useVideoUpload();

  const [videoFiles, setVideoFiles] = useState([]);
  const [activity, setActivity] = useState("");

  const [error, setError] = useState("");

  const [dragActive, setDragActive] = useState(false);


  // -----------------------------
  // Select File
  // -----------------------------

  const selectFiles = (files) => {

    const selectedFiles = Array.from(files || []);

    if (selectedFiles.length === 0) {
      return;
    }

    setError("");

    const invalidFile = selectedFiles.find(
      (file) => !file.type.startsWith("video/")
    );

    if (invalidFile) {
      setError(`${invalidFile.name} is not a valid video file.`);
      return;
    }

    setVideoFiles(selectedFiles);
  };


  const handleFileChange = (event) => {

    selectFiles(event.target.files);

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

    selectFiles(event.dataTransfer.files);

  };


  // -----------------------------
  // Upload
  // -----------------------------

  const handleUpload = async (event) => {

    event.preventDefault();

    setError("");

    if (videoFiles.length === 0) {

      setError(
        "Please select at least one video before uploading."
      );

      return;
    }


    try {

      const selectedFiles = videoFiles;

      setVideoFiles([]);
      setActivity("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await startUpload(selectedFiles, activity);

    } catch (error) {

      setError(error.message);

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
              Upload Training Videos
          </h1>

          <p>
            Upload one or more sports videos. Analysis starts only when you open a video from My Videos.
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
              Choose one or more training or sports videos from your device.
              </p>

            </div>

          </div>


          <div
            className={`drop-zone ${
              dragActive ? "drop-zone-active" : ""
            } ${
              videoFiles.length ? "drop-zone-selected" : ""
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
              multiple
              onChange={handleFileChange}
              hidden
            />


            {videoFiles.length === 0 ? (

              <>

                <div className="upload-icon">
                  ↑
                </div>

                <h3>
                  Drop your videos here
                </h3>

                <p>
                  or <span>browse files</span>
                </p>

                <small>
                  MP4, MOV, AVI or MKV. Multiple files are supported.
                </small>

              </>

            ) : (

              <>

                <div className="selected-file-icon">
                  ✓
                </div>

                <h3>
                  {videoFiles.length === 1
                    ? videoFiles[0].name
                    : `${videoFiles.length} videos selected`}
                </h3>

                <p>
                  {formatFileSize(
                    videoFiles.reduce((sum, file) => sum + file.size, 0)
                  )}
                </p>

                <span className="change-file">
                  Click to change selection
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

        {videoFiles.length > 0 && (

          <section className="selected-videos-list">

            {videoFiles.map((file) => (
              <div className="selected-video-card" key={`${file.name}-${file.size}`}>
                <div className="selected-video-info">

                  <div className="file-preview-icon">
                    ▶
                  </div>

                  <div>

                    <strong>
                      {file.name}
                    </strong>

                    <p>
                      {formatFileSize(file.size)}
                    </p>

                  </div>

                </div>

                <span className="ready-badge">
                  Ready
                </span>
              </div>
            ))}

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
          >
            Cancel
          </button>


          <button
            type="submit"
            className="submit-upload-button"
            disabled={uploadState.isUploading || videoFiles.length === 0}
          >

            {uploadState.isUploading ? (

              <>
                <span className="upload-spinner"></span>
                Uploading {uploadState.completed}/{uploadState.total}
              </>

            ) : (

              <>
                ↑ Upload {videoFiles.length > 1 ? "Videos" : "Video"}
              </>

            )}

          </button>

        </div>


      </form>


      {/* ACTIVE UPLOAD STATUS */}

      {uploadState.isUploading && (

        <section className="upload-result">

          <div className="result-header">

            <div className="result-success-icon">
              ✓
            </div>

            <div>

              <h2>
                Uploading videos
              </h2>

              <p>
                You can move to another sidebar section. Uploading will continue.
              </p>

            </div>

          </div>


          <div className="upload-progress-track">
            <div
              className="upload-progress-fill"
              style={{
                width: `${uploadState.total ? (uploadState.completed / uploadState.total) * 100 : 0}%`,
              }}
            />
          </div>

        </section>

      )}

    </div>
   </DashboardLayout>
  );

}


export default VideoUpload;
