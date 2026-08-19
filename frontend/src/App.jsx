import React from "react";

import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import AthleteProfile from "./pages/AthleteProfile";
import VideoUpload from "./pages/VideoUpload";
import MyVideos from "./pages/MyVideos";
import Settings from "./pages/Settings";
import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import ProfileCompleteRoute from "./components/ProfileCompleteRoute";


function App() {

  return (

    <ThemeProvider>

      <BrowserRouter>

        <Routes>

          <Route
            path="/"
            element={<Landing />}
          />

          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />

          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
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
                <ProfileCompleteRoute>
                  <VideoUpload />
                </ProfileCompleteRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-videos"
            element={
              <ProtectedRoute>
                <ProfileCompleteRoute>
                  <MyVideos />
                </ProfileCompleteRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ProfileCompleteRoute>
                  <Dashboard />
                </ProfileCompleteRoute>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <ProfileCompleteRoute>
                  <Settings />
                </ProfileCompleteRoute>
              </ProtectedRoute>
            }
          />

        </Routes>

      </BrowserRouter>

    </ThemeProvider>

  );
}


export default App;
