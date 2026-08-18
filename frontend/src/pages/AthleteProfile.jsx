import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// import DashboardLayout from "../layouts/DashboardLayout";

import {
  getAthleteProfile,
  createAthleteProfile,
  updateAthleteProfile,
} from "../services/api";
import { useAthleteProfile } from "../context/AthleteProfileContext";

import DashboardLayout from "../layouts/DashboardLayout";

import "../styles/athlete-profile.css";


function AthleteProfile() {

  const navigate = useNavigate();
  const { refreshProfileStatus } = useAthleteProfile();

  const [profileExists, setProfileExists] = useState(false);

  const [formData, setFormData] = useState({
    sport: "",
    position: "",
    age: "",
    height: "",
    weight: "",
    training_load: "",
    coach_notes: "",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  // Load existing athlete profile
  useEffect(() => {

    const loadProfile = async () => {

      try {

        const data = await getAthleteProfile();

        setProfileExists(true);

        setFormData({
          sport: data.sport ?? "",
          position: data.position ?? "",
          age: data.age ?? "",
          height: data.height ?? "",
          weight: data.weight ?? "",
          training_load: data.training_load ?? "",
          coach_notes: data.coach_notes ?? "",
        });

      } catch (error) {

        console.log(
          "No existing athlete profile:",
          error.message
        );

        setProfileExists(false);

      } finally {

        setLoading(false);

      }

    };

    loadProfile();

  }, []);


  const handleChange = (event) => {

    const {
      name,
      value
    } = event.target;

    setFormData({
      ...formData,
      [name]: value,
    });

  };


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");
    setSuccess("");

    try {

      setSaving(true);

      const optionalNumber = (value) =>
        value === "" ? null : Number(value);

      const profileData = {

        sport: formData.sport,
        position: formData.position,

        age: Number(formData.age),
        height: Number(formData.height),
        weight: Number(formData.weight),

        training_load: optionalNumber(formData.training_load),

        coach_notes: formData.coach_notes,

      };


      let data;


      if (profileExists) {

        data = await updateAthleteProfile(
          profileData
        );

        setSuccess(
          "Athlete profile updated successfully."
        );

      } else {

        data = await createAthleteProfile(
          profileData
        );

        setProfileExists(true);

        setSuccess(
          "Athlete profile created successfully."
        );

      }


      setFormData({
        sport: data.sport ?? "",
        position: data.position ?? "",
        age: data.age ?? "",
        height: data.height ?? "",
        weight: data.weight ?? "",
        training_load: data.training_load ?? "",
        coach_notes: data.coach_notes ?? "",
      });

      await refreshProfileStatus();


    } catch (error) {

      setError(error.message);

    } finally {

      setSaving(false);

    }

  };


  if (loading) {

    return (
      <DashboardLayout>

        <div className="profile-loading">

          <div className="profile-spinner"></div>

          <p>
            Loading athlete profile...
          </p>

        </div>

      </DashboardLayout>
    );

  }


  return (

    <DashboardLayout>

      <div className="profile-page">


        {/* PAGE HEADER */}

        <div className="profile-page-header">

          <div>

            <p className="profile-eyebrow">
              ATHLETE
            </p>

            <h1>
              Athlete Profile
            </h1>

            <p>
              Manage your personal and performance information.
            </p>

          </div>


          <div className="profile-status">

            <span className="status-dot"></span>

            {profileExists
              ? "Profile active"
              : "Profile not created"
            }

          </div>

        </div>


        {/* ALERTS */}

        {error && (

          <div className="profile-alert profile-alert-error">

            <span>!</span>

            <p>{error}</p>

          </div>

        )}


        {success && (

          <div className="profile-alert profile-alert-success">

            <span>✓</span>

            <p>{success}</p>

          </div>

        )}


        {/* FORM */}

        <form
          className="profile-form"
          onSubmit={handleSubmit}
        >


          {/* BASIC INFORMATION */}

          <section className="profile-section">

            <div className="section-heading">

              <div className="section-icon">
                01
              </div>

              <div>

                <h2>
                  Basic Information
                </h2>

                <p>
                  Your sport and playing position.
                </p>

              </div>

            </div>


            <div className="form-grid">

              <div className="form-field">

                <label htmlFor="sport">
                  Sport
                </label>

                <input
                  id="sport"
                  type="text"
                  name="sport"
                  value={formData.sport}
                  onChange={handleChange}
                  placeholder="e.g. Football"
                  required
                />

              </div>


              <div className="form-field">

                <label htmlFor="position">
                  Position
                </label>

                <input
                  id="position"
                  type="text"
                  name="position"
                  value={formData.position}
                  onChange={handleChange}
                  placeholder="e.g. Forward"
                  required
                />

              </div>

            </div>

          </section>


          {/* BODY INFORMATION */}

          <section className="profile-section">

            <div className="section-heading">

              <div className="section-icon">
                02
              </div>

              <div>

                <h2>
                  Physical Information
                </h2>

                <p>
                  Basic physical measurements.
                </p>

              </div>

            </div>


            <div className="form-grid form-grid-three">

              <div className="form-field">

                <label htmlFor="age">
                  Age
                </label>

                <input
                  id="age"
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  min="1"
                  max="100"
                  placeholder="21"
                  required
                />

              </div>


              <div className="form-field">

                <label htmlFor="height">
                  Height
                  <span>cm</span>
                </label>

                <input
                  id="height"
                  type="number"
                  step="0.1"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  placeholder="173"
                  required
                />

              </div>


              <div className="form-field">

                <label htmlFor="weight">
                  Weight
                  <span>kg</span>
                </label>

                <input
                  id="weight"
                  type="number"
                  step="0.1"
                  name="weight"
                  value={formData.weight}
                  onChange={handleChange}
                  placeholder="65"
                  required
                />

              </div>

            </div>

          </section>


          {/* TRAINING CONTEXT */}

          <section className="profile-section">

            <div className="section-heading">

              <div className="section-icon">
                03
              </div>

              <div>

                <h2>
                  Training Context
                </h2>

                <p>
                  Optional information about your current workload.
                </p>

              </div>

            </div>


            <div className="form-grid">

              <div className="form-field">

                <label htmlFor="training_load">
                  Weekly Training Load
                  <span>AU/week</span>
                </label>

                <input
                  id="training_load"
                  type="number"
                  step="0.1"
                  name="training_load"
                  value={formData.training_load}
                  onChange={handleChange}
                  placeholder="e.g. 1800"
                />

                <small>
                  Add your last 7 days of session RPE (0–10) × training duration in minutes.
                </small>

              </div>


            </div>

          </section>


          {/* COACH NOTES */}

          <section className="profile-section">

            <div className="section-heading">

              <div className="section-icon">
                04
              </div>

              <div>

                <h2>
                  Coach Notes
                </h2>

                <p>
                  Additional information about your training.
                </p>

              </div>

            </div>


            <div className="form-field">

              <textarea
                id="coach_notes"
                name="coach_notes"
                value={formData.coach_notes}
                onChange={handleChange}
                rows="5"
                placeholder="Add any relevant notes about your training, previous observations, or goals..."
              />

            </div>

          </section>


          {/* ACTIONS */}

          <div className="profile-actions">

            <button
              type="button"
              className="secondary-button"
              onClick={() =>
                navigate("/dashboard")
              }
            >
              Cancel
            </button>


            <button
              type="submit"
              className="save-profile-button"
              disabled={saving}
            >

              {saving ? (
                <>
                  <span className="button-spinner"></span>
                  Saving...
                </>
              ) : (
                <>
                  {profileExists
                    ? "Save Changes"
                    : "Create Profile"
                  }
                </>
              )}

            </button>

          </div>


        </form>

      </div>

    </DashboardLayout>

  );

}


export default AthleteProfile;
