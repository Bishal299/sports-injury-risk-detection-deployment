import React, { useEffect, useState } from "react";
import { LogOut, Moon, Save, Sun } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import { getCurrentUser, logoutUser, updateCurrentUser } from "../../services/api";
import { clearAuthSession } from "../../utils/authSession";

import { confirmLogout } from "../../utils/logoutConfirmation";
import "../../styles/coach.css";
import "../../styles/settings.css";


function SportsScientistSettings() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [formData, setFormData] = useState({ name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadSettings() {
      try {
        const user = await getCurrentUser();
        if (!cancelled) setFormData({ name: user.name || "", email: user.email || "", phone: user.phone || "" });
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load account settings.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadSettings();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateCurrentUser({ name: formData.name, phone: formData.phone });
      setFormData((current) => ({ ...current, name: updated.name || "", phone: updated.phone || "" }));
      setSuccess("Account details updated.");
    } catch (error) {
      setError(error.message || "Failed to update settings.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    if (!confirmLogout()) {
      return;
    }

    await logout();
    navigate("/login", { replace: true });
  }


  return (
    <main className="coach-page">
      <section className="coach-page-header">
        <p className="page-eyebrow">SPORTS SCIENTIST SETTINGS</p>
        <h1>Settings</h1>
        <p>Manage supported account and application settings.</p>
      </section>

      {loading && <section className="coach-empty-card">Loading settings...</section>}

      {!loading && (
        <>
          <form className="coach-form-card coach-settings-card" onSubmit={handleSubmit}>
            {error && <div className="coach-error-card">{error}</div>}
            {success && <div className="coach-success-card">{success}</div>}
            <div className="coach-section-heading"><div><h2>Account Information</h2><p>Basic account fields supported by the application.</p></div></div>
            <div className="coach-field-grid">
              <label><span>Full Name</span><input name="name" value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} required /></label>
              <label><span>Email</span><input value={formData.email} disabled readOnly /></label>
              <label><span>Phone</span><input name="phone" value={formData.phone} onChange={(event) => setFormData({ ...formData, phone: event.target.value })} /></label>
            </div>
            <div className="coach-form-actions"><button className="primary-button" disabled={saving} type="submit"><Save size={17} />{saving ? "Saving..." : "Save Settings"}</button></div>
          </form>

          <section className="settings-container scientist-settings-container">
            <article className="settings-card">
              <div className="settings-card-header"><div><h2>Appearance</h2><p>Use the existing application theme preference.</p></div></div>
              <div className="settings-row">
                <div><h3>{theme === "light" ? "Light Mode" : "Dark Mode"}</h3><p>Switch between supported application themes.</p></div>
                <button className="secondary-button" type="button" onClick={toggleTheme}>{theme === "light" ? <Moon size={17} /> : <Sun size={17} />}{theme === "light" ? "Dark Mode" : "Light Mode"}</button>
              </div>
            </article>

            <article className="settings-card">
              <div className="settings-card-header"><div><h2>Password</h2><p>Password management is not currently implemented for this role page.</p></div></div>
              <div className="settings-row">
                <div><h3>Change Password</h3><p>Use the supported authentication flows available in the application.</p></div>
                <button className="secondary-button" type="button" disabled>Unavailable</button>
              </div>
            </article>

            <article className="settings-card">
              <div className="settings-card-header"><div><h2>Session</h2><p>Sign out of this Sports Scientist account.</p></div></div>
              <div className="settings-row">
                <div><h3>Logout</h3><p>Clear your current authentication session.</p></div>
                <button className="secondary-button danger" type="button" onClick={handleLogout}><LogOut size={17} />Logout</button>
              </div>
            </article>
          </section>
        </>
      )}
    </main>
  );
}


export default SportsScientistSettings;
