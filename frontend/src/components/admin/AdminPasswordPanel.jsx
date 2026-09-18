import React, { useState } from "react";
import { KeyRound, Save } from "lucide-react";

import { changeAdminPassword } from "../../services/api";


function AdminPasswordPanel({ hasLocalPassword }) {
  const [formData, setFormData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function updateField(event) {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    if (formData.new_password !== formData.confirm_password) {
      setError("New password and confirmation do not match.");
      setSaving(false);
      return;
    }

    if (formData.new_password.length < 8) {
      setError("New password must be at least 8 characters.");
      setSaving(false);
      return;
    }

    try {
      await changeAdminPassword(formData);
      setSuccess("Password updated.");
      setFormData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error) {
      setError(error.message || "Failed to update password.");
    } finally {
      setSaving(false);
    }
  }

  if (!hasLocalPassword) {
    return (
      <section className="admin-panel-card">
        <div className="admin-panel-heading">
          <div>
            <h2>Account & Security</h2>
            <p>Password changes are not available for this login method.</p>
          </div>
          <KeyRound size={20} />
        </div>
        <div className="admin-empty-state">
          This administrator account does not use a local password in the current authentication model.
        </div>
      </section>
    );
  }

  return (
    <section className="admin-panel-card">
      <div className="admin-panel-heading">
        <div>
          <h2>Account & Security</h2>
          <p>Change the local password for your administrator account.</p>
        </div>
        <KeyRound size={20} />
      </div>

      {error && <div className="admin-error-card">{error}</div>}
      {success && <div className="admin-success-card">{success}</div>}

      <form className="admin-form" onSubmit={handleSubmit}>
        <label>
          <span>Current Password</span>
          <input
            name="current_password"
            type="password"
            value={formData.current_password}
            onChange={updateField}
            required
          />
        </label>
        <label>
          <span>New Password</span>
          <input
            name="new_password"
            type="password"
            minLength={8}
            value={formData.new_password}
            onChange={updateField}
            required
          />
        </label>
        <label>
          <span>Confirm New Password</span>
          <input
            name="confirm_password"
            type="password"
            minLength={8}
            value={formData.confirm_password}
            onChange={updateField}
            required
          />
        </label>
        <div className="admin-modal-actions">
          <button className="admin-primary-button" type="submit" disabled={saving}>
            <Save size={17} />
            {saving ? "Saving..." : "Update Password"}
          </button>
        </div>
      </form>
    </section>
  );
}


export default AdminPasswordPanel;
