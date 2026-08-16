import React from "react";

import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import AthleteProfile from "./pages/AthleteProfile";
import VideoUpload from "./pages/VideoUpload";
import MyVideos from "./pages/MyVideos";
import Settings from "./pages/Settings";
import ProtectedRoute from "./components/ProtectedRoute";


function App() {

  return (

    <ThemeProvider>

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
            element={
              <ProtectedRoute>
                <VideoUpload />
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-videos"
            element={
              <ProtectedRoute>
                <MyVideos />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />

        </Routes>

      </BrowserRouter>

    </ThemeProvider>

  );
}


export default App;