import React, { useEffect, useState } from "react";
import { BadgeCheck, Save } from "lucide-react";

import {
  getCurrentUser,
  getSportsScientistProfile,
  updateCurrentUser,
  updateSportsScientistProfile,
} from "../../services/api";
import "../../styles/coach.css";


const profileFields = [
  "primary_sport",
  "other_sports",
  "years_of_experience",
  "specialization",
  "organization",
  "certifications",
  "professional_bio",
  "profile_photo_url",
];


function SportsScientistProfile() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const [currentUser, scientistProfile] = await Promise.all([
          getCurrentUser(),
          getSportsScientistProfile(),
        ]);

        if (!cancelled) {
          setUser(currentUser);
          setProfile(scientistProfile);
          setFormData({
            name: currentUser.name || "",
            email: currentUser.email || "",
            phone: currentUser.phone || "",
            ...profileFields.reduce((values, field) => {
              values[field] = scientistProfile[field] ?? "";
              return values;
            }, {}),
          });
        }
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load Sports Scientist profile.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfile();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const [updatedUser, updatedProfile] = await Promise.all([
        updateCurrentUser({
          name: formData.name,
          phone: formData.phone,
        }),
        updateSportsScientistProfile({
          primary_sport: formData.primary_sport || null,
          other_sports: formData.other_sports || null,
          years_of_experience: formData.years_of_experience ? Number(formData.years_of_experience) : null,
          specialization: formData.specialization || null,
          organization: formData.organization || null,
          certifications: formData.certifications || null,
          professional_bio: formData.professional_bio || null,
          profile_photo_url: formData.profile_photo_url || null,
        }),
      ]);

      setUser(updatedUser);
      setProfile(updatedProfile);
      setFormData((current) => ({
        ...current,
        name: updatedUser.name || "",
        phone: updatedUser.phone || "",
      }));
      setSuccess("Sports Scientist profile updated.");
    } catch (error) {
      setError(error.message || "Failed to update Sports Scientist profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header">
        <p className="page-eyebrow">SPORTS SCIENTIST PROFILE</p>
        <h1>Profile</h1>
        <p>Manage your verified Sports Scientist information.</p>
      </section>

      {loading && <section className="coach-empty-card">Loading profile...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && profile && (
        <form className="coach-profile-grid" onSubmit={handleSubmit}>
          <section className="coach-profile-summary">
            <div className="coach-avatar">
              {formData.profile_photo_url ? <img src={formData.profile_photo_url} alt="" /> : <span>{(user?.name || "S").charAt(0).toUpperCase()}</span>}
            </div>
            <h2>{user?.name || "Sports Scientist"}</h2>
            <p>{user?.email}</p>
            <span className="verified-badge"><BadgeCheck size={16} />Sports Scientist</span>
            <div className="completion-track coach-completion-track">
              <div className="completion-fill" style={{ width: `${profile.profile_completion || 0}%` }} />
            </div>
            <small>{profile.profile_completion || 0}% profile completion</small>
          </section>

          <section className="coach-form-card">
            {success && <div className="coach-success-card">{success}</div>}

            <div className="coach-field-grid">
              <label><span>Name</span><input name="name" value={formData.name || ""} onChange={handleChange} required /></label>
              <label><span>Email</span><input value={formData.email || ""} disabled readOnly /></label>
              <label><span>Phone</span><input name="phone" value={formData.phone || ""} onChange={handleChange} /></label>
              <label><span>Professional Role</span><input value="Sports Scientist" disabled readOnly /></label>
              <label><span>Approval Status</span><input value={profile.verification_status || ""} disabled readOnly /></label>
              <label><span>Specialization</span><input name="specialization" value={formData.specialization || ""} onChange={handleChange} /></label>
              <label><span>Years of Experience</span><input min="0" name="years_of_experience" type="number" value={formData.years_of_experience || ""} onChange={handleChange} /></label>
              <label><span>Organization / Institution</span><input name="organization" value={formData.organization || ""} onChange={handleChange} /></label>
              <label><span>Primary / Interested Sport</span><input name="primary_sport" value={formData.primary_sport || ""} onChange={handleChange} /></label>
              <label><span>Interested Sports</span><input name="other_sports" value={formData.other_sports || ""} onChange={handleChange} /></label>
              <label><span>Profile Photo URL</span><input name="profile_photo_url" value={formData.profile_photo_url || ""} onChange={handleChange} /></label>
            </div>

            <label className="coach-textarea-field"><span>Analytical Expertise</span><textarea name="certifications" rows="3" value={formData.certifications || ""} onChange={handleChange} /></label>
            <label className="coach-textarea-field"><span>Professional Bio</span><textarea name="professional_bio" rows="5" value={formData.professional_bio || ""} onChange={handleChange} /></label>

            <div className="coach-form-actions">
              <button className="primary-button" disabled={saving} type="submit"><Save size={17} />{saving ? "Saving..." : "Save Profile"}</button>
            </div>
          </section>
        </form>
      )}
    </main>
  );
}


export default SportsScientistProfile;
