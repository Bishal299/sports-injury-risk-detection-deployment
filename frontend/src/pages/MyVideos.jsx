import React, { useEffect, useState } from "react";
import { getMyVideos } from "../services/api";


function MyVideos() {

  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


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


  if (loading) {
    return <h2>Loading videos...</h2>;
  }


  if (error) {
    return (
      <div>
        <h2>My Videos</h2>

        <p style={{ color: "red" }}>
          {error}
        </p>
      </div>
    );
  }


  return (

    <div>

      <h1>My Videos</h1>


      {videos.length === 0 ? (

        <p>
          You have not uploaded any videos yet.
        </p>

      ) : (

        <div>

          {videos.map((video) => (

            <div
              key={video.video_id}
              style={{
                border: "1px solid #ccc",
                padding: "15px",
                marginBottom: "20px",
                maxWidth: "600px"
              }}
            >

              <h2>
                {video.activity || "Untitled Activity"}
              </h2>


              <p>
                <strong>Status:</strong>{" "}
                {video.processing_status}
              </p>


              <p>
                <strong>Duration:</strong>{" "}
                {video.duration} seconds
              </p>


              <p>
                <strong>FPS:</strong>{" "}
                {video.fps}
              </p>


              <p>
                <strong>Resolution:</strong>{" "}
                {video.resolution}
              </p>


              <p>
                <strong>Uploaded:</strong>{" "}
                {new Date(
                  video.uploaded_at
                ).toLocaleString()}
              </p>


            <video
                controls
                width="625"
                preload="metadata"
                >
                <source
                    src={
                    video.video_url.startsWith("http")
                        ? video.video_url
                        : `http://127.0.0.1:8000${video.video_url}`
                    }
                    type="video/mp4"
                />

                Your browser does not support video playback.
            </video>

            </div>

          ))}

        </div>

      )}

    </div>

  );

}


export default MyVideos;