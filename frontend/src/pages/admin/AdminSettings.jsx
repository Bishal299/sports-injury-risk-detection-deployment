import React, { useEffect, useState } from "react";
import { LogOut, Moon, Sun } from "lucide-react";
import { useNavigate } from "react-router-dom";

import AdminPasswordPanel from "../../components/admin/AdminPasswordPanel";
import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import DashboardLayout from "../../layouts/DashboardLayout";
import { getAdminProfile, logoutUser } from "../../services/api";
import { clearAuthSession } from "../../utils/authSession";
import { confirmLogout } from "../../utils/logoutConfirmation";
import "../../styles/admin.css";


function InfoBlock({ label, value }) {
  return (
    <div className="admin-detail-block">
      <span>{label}</span>
      <strong>{value || "Not provided"}</strong>
    </div>
  );
}

function AdminSettings() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function fetchProfile() {
      try {
        setLoading(true);
        const data = await getAdminProfile();
        if (active) {
          setProfile(data);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Failed to load admin profile");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    fetchProfile();

    return () => {
      active = false;
    };
  }, []);

  async function handleLogout() {
    if (!confirmLogout()) {
      return;
    }

    await logout();
    navigate("/login", { replace: true });
  }


  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN SETTINGS</p>
            <h1>Settings</h1>
            <p>Manage supported administrator account and application preferences.</p>
          </div>
        </section>

        {loading && <section className="admin-empty-card">Loading administrator settings...</section>}
        {error && <section className="admin-error-card">{error}</section>}

        {!loading && profile && (
          <>
            <section className="admin-settings-grid">
              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Appearance</h2>
                    <p>Use the existing persisted application theme preference.</p>
                  </div>
                </div>
                <div className="admin-settings-row">
                  <div>
                    <h3>{theme === "light" ? "Light Mode" : "Dark Mode"}</h3>
                    <p>System preference is not supported by the current theme implementation.</p>
                  </div>
                  <button className="admin-secondary-button" type="button" onClick={toggleTheme}>
                    {theme === "light" ? <Moon size={17} /> : <Sun size={17} />}
                    {theme === "light" ? "Dark Mode" : "Light Mode"}
                  </button>
                </div>
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Notifications</h2>
                    <p>No persistent notification preference system is currently available.</p>
                  </div>
                </div>
                <div className="admin-empty-state">
                  Notification settings are not supported by the existing application model.
                </div>
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Account Information</h2>
                    <p>Current authenticated administrator account details.</p>
                  </div>
                </div>
                <div className="admin-detail-grid">
                  <InfoBlock label="Email" value={profile.email} />
                  <InfoBlock label="Role" value="Administrator" />
                  <InfoBlock label="Account Status" value={profile.status} />
                </div>
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Session</h2>
                    <p>Clear the current administrator session on this device.</p>
                  </div>
                </div>
                <div className="admin-settings-row">
                  <div>
                    <h3>Logout</h3>
                    <p>Sign out and return to the login page.</p>
                  </div>
                  <button className="admin-secondary-button danger" type="button" onClick={handleLogout}>
                    <LogOut size={17} />
                    Logout
                  </button>
                </div>
              </article>
            </section>

            <AdminPasswordPanel hasLocalPassword={profile.has_local_password} />
          </>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminSettings;
