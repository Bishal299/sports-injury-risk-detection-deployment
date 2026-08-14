import React from "react";

import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import AthleteProfile from "./pages/AthleteProfile";
import VideoUpload from "./pages/VideoUpload";
import MyVideos from "./pages/MyVideos";
import ProtectedRoute from "./components/ProtectedRoute";


function App() {

  return (
    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<Login />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
            path="/athlete-profile"
            element={
                <ProtectedRoute>
                <AthleteProfile />
                </ProtectedRoute>
            }
        />
        <Route
            path="/video-upload"
            element={<VideoUpload />}
        />
        <Route
            path="/my-videos"
            element={<MyVideos />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}


export default App;