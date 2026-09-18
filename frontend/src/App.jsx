import React from "react";

import {
  BrowserRouter,
  Navigate,
  Routes,
  Route
} from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";
import { VideoUploadProvider } from "./context/VideoUploadContext";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Landing from "./pages/Landing";
import Dashboard from "./pages/athlete/Dashboard";
import AthleteProfile from "./pages/athlete/AthleteProfile";
import VideoUpload from "./pages/athlete/VideoUpload";
import MyVideos from "./pages/athlete/MyVideos";
import MyWork from "./pages/athlete/MyWork";
import MyRehabilitation from "./pages/athlete/MyRehabilitation";
import Settings from "./pages/Settings";
import Analysis from "./pages/athlete/Analysis";
import AnalysisHistory from "./pages/athlete/AnalysisHistory";
import ProfessionalRoleRequest from "./pages/ProfessionalRoleRequest";
import ProfessionalApplication from "./pages/ProfessionalApplication";
import Notifications from "./pages/Notifications";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminProfessionalRequests from "./pages/admin/AdminProfessionalRequests";
import AdminUserManagement from "./pages/admin/AdminUserManagement";
import AdminPlatformAnalytics from "./pages/admin/AdminPlatformAnalytics";
import AdminSystemMonitoring from "./pages/admin/AdminSystemMonitoring";
import AdminReportManagement from "./pages/admin/AdminReportManagement";
import AdminProfile from "./pages/admin/AdminProfile";
import AdminSettings from "./pages/admin/AdminSettings";
import CoachDashboard from "./pages/coach/CoachDashboard";
import CoachProfile from "./pages/coach/CoachProfile";
import CoachSettings from "./pages/coach/CoachSettings";
import DiscoverAthletes from "./pages/coach/DiscoverAthletes";
import MyAthletes from "./pages/coach/MyAthletes";
import CoachRequests from "./pages/coach/CoachRequests";
import CoachAthleteDetail from "./pages/coach/CoachAthleteDetail";
import CoachAthleteVideos from "./pages/coach/CoachAthleteVideos";
import CoachResourceList from "./pages/coach/CoachResourceList";
import CoachLayout from "./layouts/CoachLayout";
import SportsScientistDashboard from "./pages/sports-scientist/SportsScientistDashboard";
import SportsScientistAthletes from "./pages/sports-scientist/SportsScientistAthletes";
import SportsScientistBiomechanicalAnalytics from "./pages/sports-scientist/SportsScientistBiomechanicalAnalytics";
import SportsScientistTeamPerformance from "./pages/sports-scientist/SportsScientistTeamPerformance";
import SportsScientistInjuryInsights from "./pages/sports-scientist/SportsScientistInjuryInsights";
import SportsScientistAthleteComparison from "./pages/sports-scientist/SportsScientistAthleteComparison";
import SportsScientistResearchReports from "./pages/sports-scientist/SportsScientistResearchReports";
import SportsScientistProfile from "./pages/sports-scientist/SportsScientistProfile";
import SportsScientistSettings from "./pages/sports-scientist/SportsScientistSettings";
import SportsScientistLayout from "./layouts/SportsScientistLayout";
import PhysiotherapistDashboard from "./pages/physiotherapist/PhysiotherapistDashboard";
import PhysiotherapistAthletes, { PhysiotherapistDiscoverAthletes } from "./pages/physiotherapist/PhysiotherapistAthletes";
import PhysiotherapistAthleteDetail from "./pages/physiotherapist/PhysiotherapistAthleteDetail";
import PhysiotherapistAthleteVideos from "./pages/physiotherapist/PhysiotherapistAthleteVideos";
import PhysiotherapistMovementAnalytics from "./pages/physiotherapist/PhysiotherapistMovementAnalytics";
import PhysiotherapistRequests from "./pages/physiotherapist/PhysiotherapistRequests";
import PhysiotherapistResourceList from "./pages/physiotherapist/PhysiotherapistResourceList";
import PhysiotherapistProfile from "./pages/physiotherapist/PhysiotherapistProfile";
import PhysiotherapistSettings from "./pages/physiotherapist/PhysiotherapistSettings";
import PhysiotherapistLayout from "./layouts/PhysiotherapistLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import PublicRoute from "./components/PublicRoute";
import ProfileCompleteRoute from "./components/ProfileCompleteRoute";
import RoleRoute from "./components/RoleRoute";
import VerifiedCoachRoute from "./components/VerifiedCoachRoute";
import VerifiedPhysiotherapistRoute from "./components/VerifiedPhysiotherapistRoute";
import VerifiedSportsScientistRoute from "./components/VerifiedSportsScientistRoute";


function App() {

  return (

    <ThemeProvider>

      <BrowserRouter>

        <VideoUploadProvider>

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
                <RoleRoute allowedRoles={["Athlete"]}>
                  <AthleteProfile />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/request-professional-role"
            element={
              <ProtectedRoute>
                <ProfessionalRoleRequest />
              </ProtectedRoute>
            }
          />

          <Route
            path="/request-professional-role/coach"
            element={
              <ProtectedRoute>
                <ProfessionalApplication requestedRole="COACH" />
              </ProtectedRoute>
            }
          />

          <Route
            path="/request-professional-role/physiotherapist"
            element={
              <ProtectedRoute>
                <ProfessionalApplication requestedRole="PHYSIOTHERAPIST" />
              </ProtectedRoute>
            }
          />

          <Route
            path="/request-professional-role/sports-scientist"
            element={
              <ProtectedRoute>
                <ProfessionalApplication requestedRole="SPORTS_SCIENTIST" />
              </ProtectedRoute>
            }
          />

          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <Notifications />
              </ProtectedRoute>
            }
          />

          <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />

          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminDashboard />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/professional-requests"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminProfessionalRequests />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/users"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminUserManagement />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/analytics"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminPlatformAnalytics />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/system-monitoring"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminSystemMonitoring />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route path="/admin/system" element={<Navigate to="/admin/system-monitoring" replace />} />

          <Route
            path="/admin/reports"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminReportManagement />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/profile"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminProfile />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/settings"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Administrator"]}>
                  <AdminSettings />
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/coach"
            element={
              <ProtectedRoute>
                <VerifiedCoachRoute>
                  <CoachLayout />
                </VerifiedCoachRoute>
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/coach/dashboard" replace />} />
            <Route path="dashboard" element={<CoachDashboard />} />
            <Route path="athletes" element={<MyAthletes />} />
            <Route path="athletes/:athleteId" element={<CoachAthleteDetail />} />
            <Route path="athletes/:athleteId/videos" element={<CoachAthleteVideos />} />
            <Route path="athletes/:athleteId/analysis/:videoId" element={<Analysis viewer="coach" />} />
            <Route path="discover-athletes" element={<DiscoverAthletes />} />
            <Route path="requests" element={<CoachRequests />} />
            <Route path="videos" element={<CoachResourceList type="videos" />} />
            <Route path="analyses" element={<CoachResourceList type="analyses" />} />
            <Route path="reports" element={<CoachResourceList type="reports" />} />
            <Route path="profile" element={<CoachProfile />} />
            <Route path="settings" element={<CoachSettings />} />
          </Route>

          <Route
            path="/sports-scientist"
            element={
              <ProtectedRoute>
                <VerifiedSportsScientistRoute>
                  <SportsScientistLayout />
                </VerifiedSportsScientistRoute>
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/sports-scientist/dashboard" replace />} />
            <Route path="dashboard" element={<SportsScientistDashboard />} />
            <Route path="athletes" element={<SportsScientistAthletes />} />
            <Route path="biomechanical-analytics" element={<SportsScientistBiomechanicalAnalytics />} />
            <Route path="team-performance" element={<SportsScientistTeamPerformance />} />
            <Route path="injury-insights" element={<SportsScientistInjuryInsights />} />
            <Route path="injury-prediction-insights" element={<Navigate to="/sports-scientist/injury-insights" replace />} />
            <Route path="athlete-comparison" element={<SportsScientistAthleteComparison />} />
            <Route path="research-reports" element={<SportsScientistResearchReports />} />
            <Route path="profile" element={<SportsScientistProfile />} />
            <Route path="settings" element={<SportsScientistSettings />} />
          </Route>

          <Route
            path="/physiotherapist"
            element={
              <ProtectedRoute>
                <VerifiedPhysiotherapistRoute>
                  <PhysiotherapistLayout />
                </VerifiedPhysiotherapistRoute>
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/physiotherapist/dashboard" replace />} />
            <Route path="dashboard" element={<PhysiotherapistDashboard />} />
            <Route path="athletes" element={<PhysiotherapistAthletes />} />
            <Route path="athletes/:athleteId" element={<PhysiotherapistAthleteDetail />} />
            <Route path="athletes/:athleteId/videos" element={<PhysiotherapistAthleteVideos />} />
            <Route path="athletes/:athleteId/videos/:videoId/analysis" element={<Analysis viewer="physiotherapist" />} />
            <Route path="discover-athletes" element={<PhysiotherapistDiscoverAthletes />} />
            <Route path="requests" element={<PhysiotherapistRequests />} />
            <Route path="rehabilitation" element={<PhysiotherapistResourceList type="rehabilitation" />} />
            <Route path="rehabilitation/:athleteId" element={<PhysiotherapistAthleteDetail />} />
            <Route path="movement-analytics" element={<PhysiotherapistResourceList type="movement-analytics" />} />
            <Route path="movement-analytics/:athleteId" element={<PhysiotherapistMovementAnalytics />} />
            <Route path="recovery-reports" element={<PhysiotherapistResourceList type="reports" />} />
            <Route path="profile" element={<PhysiotherapistProfile />} />
            <Route path="settings" element={<PhysiotherapistSettings />} />
          </Route>

          <Route
            path="/video-upload"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <VideoUpload />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-videos"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <MyVideos />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/analysis/:videoId"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <Analysis />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/analysis-history"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <AnalysisHistory />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-work"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <MyWork />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-rehabilitation"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <MyRehabilitation />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <Dashboard />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <RoleRoute allowedRoles={["Athlete"]}>
                  <ProfileCompleteRoute>
                    <Settings />
                  </ProfileCompleteRoute>
                </RoleRoute>
              </ProtectedRoute>
            }
          />

          </Routes>

        </VideoUploadProvider>

      </BrowserRouter>

    </ThemeProvider>

  );
}


export default App;
