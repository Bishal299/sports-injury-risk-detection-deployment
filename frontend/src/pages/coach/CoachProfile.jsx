import React, { useEffect, useState } from "react";
import { BadgeCheck, Save } from "lucide-react";

import {
  getCoachProfile,
  getCurrentUser,
  updateCoachProfile,
} from "../../services/api";
import "../../styles/coach.css";


const editableFields = [
  "primary_sport",
  "other_sports",
  "years_of_experience",
  "coaching_specialization",
  "organization",
  "certifications",
  "professional_bio",
  "profile_photo_url",
];


function CoachProfile() {
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
        const [currentUser, coachProfile] = await Promise.all([
          getCurrentUser(),
          getCoachProfile(),
        ]);

        if (!cancelled) {
          setUser(currentUser);
          setProfile(coachProfile);
          setFormData(
            editableFields.reduce((values, field) => {
              values[field] = coachProfile[field] ?? "";
              return values;
            }, {})
          );
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message || "Failed to load Coach profile.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setSuccess("");
    setError("");

    try {
      const updated = await updateCoachProfile({
        ...formData,
        years_of_experience: formData.years_of_experience
          ? Number(formData.years_of_experience)
          : null,
      });
      setProfile(updated);
      setSuccess("Coach profile updated.");
    } catch (error) {
      setError(error.message || "Failed to update Coach profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="coach-page">
        <section className="coach-page-header">
          <p className="page-eyebrow">COACH PROFILE</p>
          <h1>Profile</h1>
          <p>Manage your verified Coach information.</p>
        </section>

        {loading && <div className="coach-empty-card">Loading profile...</div>}
        {error && <div className="coach-error-card">{error}</div>}

        {!loading && !error && profile && (
          <form className="coach-profile-grid" onSubmit={handleSubmit}>
            <section className="coach-profile-summary">
              <div className="coach-avatar">
                {profile.profile_photo_url ? (
                  <img src={profile.profile_photo_url} alt="" />
                ) : (
                  <span>{(user?.name || "C").charAt(0).toUpperCase()}</span>
                )}
              </div>

              <h2>{user?.name || "Coach"}</h2>
              <p>{user?.email}</p>

              <span className="verified-badge">
                <BadgeCheck size={16} />
                Verified Coach
              </span>

              <div className="completion-track coach-completion-track">
                <div
                  className="completion-fill"
                  style={{ width: `${profile.profile_completion || 0}%` }}
                />
              </div>
              <small>{profile.profile_completion || 0}% profile completion</small>
            </section>

            <section className="coach-form-card">
              {success && <div className="coach-success-card">{success}</div>}

              <div className="coach-field-grid">
                <label>
                  <span>Primary Sport</span>
                  <input
                    name="primary_sport"
                    value={formData.primary_sport || ""}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  <span>Other Sports</span>
                  <input
                    name="other_sports"
                    value={formData.other_sports || ""}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  <span>Years of Experience</span>
                  <input
                    min="0"
                    name="years_of_experience"
                    type="number"
                    value={formData.years_of_experience || ""}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  <span>Coaching Specialization</span>
                  <input
                    name="coaching_specialization"
                    value={formData.coaching_specialization || ""}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  <span>Organization</span>
                  <input
                    name="organization"
                    value={formData.organization || ""}
                    onChange={handleChange}
                  />
                </label>

                <label>
                  <span>Profile Photo URL</span>
                  <input
                    name="profile_photo_url"
                    value={formData.profile_photo_url || ""}
                    onChange={handleChange}
                  />
                </label>
              </div>

              <label className="coach-textarea-field">
                <span>Certifications</span>
                <textarea
                  name="certifications"
                  rows="3"
                  value={formData.certifications || ""}
                  onChange={handleChange}
                />
              </label>

              <label className="coach-textarea-field">
                <span>Professional Bio</span>
                <textarea
                  name="professional_bio"
                  rows="5"
                  value={formData.professional_bio || ""}
                  onChange={handleChange}
                />
              </label>

              <div className="coach-form-actions">
                <button className="primary-button" disabled={saving} type="submit">
                  <Save size={17} />
                  {saving ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </section>
          </form>
        )}
    </main>
  );
}


export default CoachProfile;
