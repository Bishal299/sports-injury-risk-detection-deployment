import React, { useEffect, useState } from "react";
import { BadgeCheck, Save } from "lucide-react";

import {
  getCurrentUser,
  getPhysiotherapistProfile,
  updatePhysiotherapistProfile,
} from "../../services/api";
import "../../styles/coach.css";

const fields = ["primary_sport", "other_sports", "years_of_experience", "specialization", "organization", "certifications", "professional_bio", "profile_photo_url"];

function PhysiotherapistProfile() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [currentUser, physioProfile] = await Promise.all([getCurrentUser(), getPhysiotherapistProfile()]);
        if (!cancelled) {
          setUser(currentUser);
          setProfile(physioProfile);
          setFormData(fields.reduce((values, field) => ({ ...values, [field]: physioProfile[field] ?? "" }), {}));
        }
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load profile.");
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
    setSuccess("");
    setError("");
    try {
      const updated = await updatePhysiotherapistProfile({
        ...formData,
        years_of_experience: formData.years_of_experience ? Number(formData.years_of_experience) : null,
      });
      setProfile(updated);
      setSuccess("Physiotherapist profile updated.");
    } catch (error) {
      setError(error.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="coach-page">
        <section className="coach-page-header"><p className="page-eyebrow">PHYSIOTHERAPIST PROFILE</p><h1>Profile</h1><p>Manage your verified Physiotherapist information.</p></section>
        {loading && <section className="coach-empty-card">Loading profile...</section>}
        {error && <section className="coach-error-card">{error}</section>}
        {!loading && !error && profile && (
          <form className="coach-profile-grid" onSubmit={handleSubmit}>
            <section className="coach-profile-summary">
              <div className="coach-avatar">{profile.profile_photo_url ? <img src={profile.profile_photo_url} alt="" /> : <span>{(user?.name || "P").charAt(0).toUpperCase()}</span>}</div>
              <h2>{user?.name || "Physiotherapist"}</h2><p>{user?.email}</p>
              <span className="verified-badge"><BadgeCheck size={16} />Verified Physiotherapist</span>
              <small>{profile.profile_completion || 0}% profile completion</small>
            </section>
            <section className="coach-form-card">
              {success && <div className="coach-success-card">{success}</div>}
              <div className="coach-field-grid">
                <label><span>Primary Sport / Area</span><input value={formData.primary_sport || ""} onChange={(event) => setFormData({ ...formData, primary_sport: event.target.value })} /></label>
                <label><span>Other Sports</span><input value={formData.other_sports || ""} onChange={(event) => setFormData({ ...formData, other_sports: event.target.value })} /></label>
                <label><span>Years of Experience</span><input min="0" type="number" value={formData.years_of_experience || ""} onChange={(event) => setFormData({ ...formData, years_of_experience: event.target.value })} /></label>
                <label><span>Physiotherapy Specialization</span><input value={formData.specialization || ""} onChange={(event) => setFormData({ ...formData, specialization: event.target.value })} /></label>
                <label><span>Organization / Clinic</span><input value={formData.organization || ""} onChange={(event) => setFormData({ ...formData, organization: event.target.value })} /></label>
                <label><span>Profile Photo URL</span><input value={formData.profile_photo_url || ""} onChange={(event) => setFormData({ ...formData, profile_photo_url: event.target.value })} /></label>
              </div>
              <label className="coach-textarea-field"><span>Certifications</span><textarea rows="3" value={formData.certifications || ""} onChange={(event) => setFormData({ ...formData, certifications: event.target.value })} /></label>
              <label className="coach-textarea-field"><span>Professional Bio</span><textarea rows="5" value={formData.professional_bio || ""} onChange={(event) => setFormData({ ...formData, professional_bio: event.target.value })} /></label>
              <div className="coach-form-actions"><button className="primary-button" disabled={saving} type="submit"><Save size={17} />{saving ? "Saving..." : "Save Profile"}</button></div>
            </section>
          </form>
        )}
    </main>
  );
}


export default PhysiotherapistProfile;
