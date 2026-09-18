import React, { useEffect, useState } from "react";
import { Save } from "lucide-react";

import { getCurrentUser, updateCurrentUser } from "../../services/api";
import "../../styles/coach.css";


function PhysiotherapistSettings() {
  const [formData, setFormData] = useState({ name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const user = await getCurrentUser();
        if (!cancelled) setFormData({ name: user.name || "", email: user.email || "", phone: user.phone || "" });
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load account settings.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
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

  return (
    <main className="coach-page">
        <section className="coach-page-header"><p className="page-eyebrow">PHYSIOTHERAPIST SETTINGS</p><h1>Settings</h1><p>Manage basic account details for your Physiotherapist account.</p></section>
        {loading && <section className="coach-empty-card">Loading settings...</section>}
        {!loading && (
          <form className="coach-form-card coach-settings-card" onSubmit={handleSubmit}>
            {error && <div className="coach-error-card">{error}</div>}
            {success && <div className="coach-success-card">{success}</div>}
            <div className="coach-field-grid">
              <label><span>Full Name</span><input name="name" value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} required /></label>
              <label><span>Email</span><input value={formData.email} disabled readOnly /></label>
              <label><span>Phone</span><input name="phone" value={formData.phone} onChange={(event) => setFormData({ ...formData, phone: event.target.value })} /></label>
            </div>
            <div className="coach-form-actions"><button className="primary-button" disabled={saving} type="submit"><Save size={17} />{saving ? "Saving..." : "Save Settings"}</button></div>
          </form>
        )}
    </main>
  );
}


export default PhysiotherapistSettings;
