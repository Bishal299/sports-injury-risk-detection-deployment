import React, { useEffect, useState } from "react";
import { Save, ShieldCheck } from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import { getAdminProfile, updateAdminProfile } from "../../services/api";
import "../../styles/admin.css";


function formatDate(value, fallback = "Not tracked") {
  if (!value) return fallback;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return fallback;
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function InfoBlock({ label, value }) {
  return (
    <div className="admin-detail-block">
      <span>{label}</span>
      <strong>{value || "Not provided"}</strong>
    </div>
  );
}

function AdminProfile() {
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    profile_image: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setLoading(true);
      setError("");
      try {
        const data = await getAdminProfile();
        if (!cancelled) {
          setProfile(data);
          setFormData({
            name: data.name || "",
            phone: data.phone || "",
            profile_image: data.profile_image || "",
          });
        }
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load administrator profile.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  function updateField(event) {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    if (!formData.name.trim()) {
      setError("Full name is required.");
      setSaving(false);
      return;
    }

    try {
      const updated = await updateAdminProfile({
        name: formData.name.trim(),
        phone: formData.phone || null,
        profile_image: formData.profile_image || null,
      });
      setProfile(updated);
      setFormData({
        name: updated.name || "",
        phone: updated.phone || "",
        profile_image: updated.profile_image || "",
      });
      setSuccess("Administrator profile updated.");
    } catch (error) {
      setError(error.message || "Failed to update administrator profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN PROFILE</p>
            <h1>ADMIN PROFILE</h1>
            <p>Manage your administrator account information.</p>
          </div>
        </section>

        {loading && <section className="admin-empty-card">Loading administrator profile...</section>}
        {error && <section className="admin-error-card">{error}</section>}
        {success && <section className="admin-success-card">{success}</section>}

        {!loading && profile && (
          <>
            <section className="admin-profile-layout">
              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Account Overview</h2>
                    <p>Non-sensitive information from the authenticated administrator account.</p>
                  </div>
                  <ShieldCheck size={20} />
                </div>
                <div className="admin-detail-grid">
                  <InfoBlock label="Full Name" value={profile.name} />
                  <InfoBlock label="Email" value={profile.email} />
                  <InfoBlock label="Role" value="Administrator" />
                  <InfoBlock label="Account Status" value={profile.status} />
                  <InfoBlock label="Account Created" value={formatDate(profile.created_at, "Not available")} />
                  <InfoBlock label="Last Login" value={formatDate(profile.last_login)} />
                  <InfoBlock label="Phone" value={profile.phone} />
                </div>
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading">
                  <div>
                    <h2>Edit Profile</h2>
                    <p>Role, status, and email are managed outside this page.</p>
                  </div>
                </div>
                <form className="admin-form" onSubmit={handleSubmit}>
                  <label>
                    <span>Full Name</span>
                    <input name="name" value={formData.name} onChange={updateField} required />
                  </label>
                  <label>
                    <span>Email</span>
                    <input value={profile.email || ""} disabled readOnly />
                  </label>
                  <label>
                    <span>Phone</span>
                    <input name="phone" value={formData.phone} onChange={updateField} />
                  </label>
                  <label>
                    <span>Profile Photo URL</span>
                    <input name="profile_image" value={formData.profile_image} onChange={updateField} />
                  </label>
                  <div className="admin-modal-actions">
                    <button className="admin-primary-button" type="submit" disabled={saving}>
                      <Save size={17} />
                      {saving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </form>
              </article>
            </section>

          </>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminProfile;
