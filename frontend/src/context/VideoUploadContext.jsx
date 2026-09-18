import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { uploadVideo } from "../services/api";


const VideoUploadContext = createContext(null);


export function VideoUploadProvider({ children }) {
  const navigate = useNavigate();
  const [uploadState, setUploadState] = useState({
    isUploading: false,
    total: 0,
    completed: 0,
    failed: 0,
    successful: [],
    error: "",
  });

  const startUpload = useCallback(async (files, activity) => {
    const selectedFiles = Array.from(files || []);

    if (selectedFiles.length === 0) {
      throw new Error("Please select at least one video before uploading.");
    }

    setUploadState({
      isUploading: true,
      total: selectedFiles.length,
      completed: 0,
      failed: 0,
      successful: [],
      error: "",
    });

    const successful = [];
    const errors = [];

    for (const file of selectedFiles) {
      try {
        const uploaded = await uploadVideo(file, activity);
        successful.push(uploaded);
      } catch (error) {
        errors.push(`${file.name}: ${error.message || "Upload failed"}`);
      } finally {
        setUploadState((current) => ({
          ...current,
          completed: current.completed + 1,
          failed: errors.length,
          successful: [...successful],
          error: errors.join("\n"),
        }));
      }
    }

    setUploadState({
      isUploading: false,
      total: selectedFiles.length,
      completed: selectedFiles.length,
      failed: errors.length,
      successful,
      error: errors.join("\n"),
    });

    window.dispatchEvent(new Event("videos-updated"));

    if (successful.length > 0) {
      navigate("/my-videos");
      return successful;
    }

    if (errors.length > 0) {
      throw new Error(errors.join("\n"));
    }

    return successful;
  }, [navigate]);

  const value = useMemo(() => ({
    uploadState,
    startUpload,
  }), [startUpload, uploadState]);

  return (
    <VideoUploadContext.Provider value={value}>
      {children}
    </VideoUploadContext.Provider>
  );
}


export function useVideoUpload() {
  const context = useContext(VideoUploadContext);

  if (!context) {
    throw new Error("useVideoUpload must be used within VideoUploadProvider");
  }

  return context;
}
