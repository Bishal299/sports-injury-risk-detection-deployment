import React, { useState } from "react";
import { uploadVideo } from "../services/api";


function VideoUpload() {

  const [videoFile, setVideoFile] = useState(null);
  const [activity, setActivity] = useState("");

  const [uploading, setUploading] = useState(false);

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [uploadedVideo, setUploadedVideo] = useState(null);


  const handleFileChange = (event) => {

    const file = event.target.files[0];

    setVideoFile(file);

    setSuccess("");
    setError("");

  };


  const handleUpload = async (event) => {

    event.preventDefault();

    setSuccess("");
    setError("");

    if (!videoFile) {

      setError("Please select a video file.");

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

      // Clear selected file
      setVideoFile(null);

      // Reset file input
      event.target.reset();

    } catch (error) {

      setError(error.message);

    } finally {

      setUploading(false);

    }

  };


  return (
    <div>

      <h1>
        Upload Sports Video
      </h1>


      {success && (
        <p style={{ color: "green" }}>
          {success}
        </p>
      )}


      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}


      <form onSubmit={handleUpload}>

        <div>

          <label>
            Activity
          </label>

          <br />

          <input
            type="text"
            value={activity}
            onChange={(event) =>
              setActivity(event.target.value)
            }
            placeholder="e.g. Running, Squat, Football"
          />

        </div>


        <br />


        <div>

          <label>
            Video
          </label>

          <br />

          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
          />

        </div>


        <br />


        {videoFile && (
          <p>
            Selected: {videoFile.name}
          </p>
        )}


        <button
          type="submit"
          disabled={uploading}
        >
          {uploading
            ? "Uploading..."
            : "Upload Video"
          }
        </button>

      </form>


      {uploadedVideo && (

        <div>

          <h2>
            Upload Details
          </h2>

          <p>
            <strong>Video ID:</strong>{" "}
            {uploadedVideo.video_id}
          </p>

          <p>
            <strong>Activity:</strong>{" "}
            {uploadedVideo.activity}
          </p>

          <p>
            <strong>Status:</strong>{" "}
            {uploadedVideo.processing_status}
          </p>

          <p>
            <strong>Duration:</strong>{" "}
            {uploadedVideo.duration}
          </p>

          <p>
            <strong>FPS:</strong>{" "}
            {uploadedVideo.fps}
          </p>

          <p>
            <strong>Resolution:</strong>{" "}
            {uploadedVideo.resolution}
          </p>

        </div>

      )}

    </div>
  );
}


export default VideoUpload;