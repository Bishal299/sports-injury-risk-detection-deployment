import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getAthleteProfile,
  createAthleteProfile,
  updateAthleteProfile,
  getInjuryHistory,
  createInjuryHistory,
  updateInjuryHistory,
  deleteInjuryHistory,
} from "../../services/api";
import { useAthleteProfile } from "../../context/AthleteProfileContext";

import DashboardLayout from "../../layouts/DashboardLayout";

import "../../styles/athlete-profile.css";


function AthleteProfile() {

  const navigate = useNavigate();
  const { refreshProfileStatus } = useAthleteProfile();

  const [profileExists, setProfileExists] = useState(false);
  const [athleteId, setAthleteId] = useState(null);

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
  const [injuries, setInjuries] = useState([]);
  const [injuryFormOpen, setInjuryFormOpen] = useState(false);
  const [editingInjuryId, setEditingInjuryId] = useState(null);
  const [savingInjury, setSavingInjury] = useState(false);
  const [injuryForm, setInjuryForm] = useState({
    injury_type: "",
    body_part: "",
    affected_side: "NOT_APPLICABLE",
    severity: "MILD",
    status: "RECOVERED",
    injury_date: "",
    recovery_date: "",
    remarks: "",
  });


  const formatLabel = (value) => {
    if (!value) return "N/A";
    return value
      .toLowerCase()
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  };


  const resetInjuryForm = () => {
    setEditingInjuryId(null);
    setInjuryForm({
      injury_type: "",
      body_part: "",
      affected_side: "NOT_APPLICABLE",
      severity: "MILD",
      status: "RECOVERED",
      injury_date: "",
      recovery_date: "",
      remarks: "",
    });
  };


  const loadInjuryHistory = async (id) => {
    if (!id) return;
    const records = await getInjuryHistory(id);
    setInjuries(records);
  };


  // Load existing athlete profile
  useEffect(() => {

    const loadProfile = async () => {

      try {

        const data = await getAthleteProfile();

        setProfileExists(true);
        setAthleteId(data.athlete_id);

        setFormData({
          sport: data.sport ?? "",
          position: data.position ?? "",
          age: data.age ?? "",
          height: data.height ?? "",
          weight: data.weight ?? "",
          training_load: data.training_load ?? "",
          coach_notes: data.coach_notes ?? "",
        });

        await loadInjuryHistory(data.athlete_id);

      } catch (error) {

        console.log(
          "No existing athlete profile:",
          error.message
        );

        setProfileExists(false);
        setAthleteId(null);

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


  const handleInjuryChange = (event) => {
    const { name, value } = event.target;

    setInjuryForm({
      ...injuryForm,
      [name]: value,
      ...(name === "status" && value === "ACTIVE"
        ? { recovery_date: "" }
        : {}),
    });
  };


  const handleEditInjury = (injury) => {
    setEditingInjuryId(injury.injury_id);
    setInjuryForm({
      injury_type: injury.injury_type ?? "",
      body_part: injury.body_part ?? "",
      affected_side: injury.affected_side ?? "NOT_APPLICABLE",
      severity: injury.severity ?? "MILD",
      status: injury.status ?? "UNKNOWN",
      injury_date: injury.injury_date ?? "",
      recovery_date: injury.recovery_date ?? "",
      remarks: injury.remarks ?? "",
    });
    setInjuryFormOpen(true);
    setError("");
    setSuccess("");
  };


  const handleCancelInjury = () => {
    resetInjuryForm();
    setInjuryFormOpen(false);
  };


  const handleSaveInjury = async () => {
    setError("");
    setSuccess("");

    if (!athleteId) {
      setError("Create your athlete profile before adding injury history.");
      return;
    }

    if (!injuryForm.injury_type.trim() || !injuryForm.body_part.trim() || !injuryForm.injury_date) {
      setError("Injury type, body part, and injury date are required.");
      return;
    }

    if (injuryForm.status === "ACTIVE" && injuryForm.recovery_date) {
      setError("Active injuries should not include a recovery date.");
      return;
    }

    try {
      setSavingInjury(true);

      const payload = {
        ...injuryForm,
        injury_type: injuryForm.injury_type.trim(),
        body_part: injuryForm.body_part.trim(),
        recovery_date: injuryForm.recovery_date || null,
        remarks: injuryForm.remarks || null,
      };

      if (editingInjuryId) {
        await updateInjuryHistory(athleteId, editingInjuryId, payload);
        setSuccess("Injury history updated successfully.");
      } else {
        await createInjuryHistory(athleteId, payload);
        setSuccess("Injury history added successfully.");
      }

      await loadInjuryHistory(athleteId);
      resetInjuryForm();
      setInjuryFormOpen(false);
    } catch (error) {
      setError(error.message);
    } finally {
      setSavingInjury(false);
    }
  };


  const handleDeleteInjury = async (injury) => {
    if (!athleteId) return;

    const confirmed = window.confirm(
      `Delete injury record "${injury.injury_type}"?`
    );

    if (!confirmed) return;

    try {
      setError("");
      setSuccess("");
      await deleteInjuryHistory(athleteId, injury.injury_id);
      await loadInjuryHistory(athleteId);
      setSuccess("Injury history deleted successfully.");
    } catch (error) {
      setError(error.message);
    }
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
        setAthleteId(data.athlete_id);

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

      if (data.athlete_id) {
        setAthleteId(data.athlete_id);
        await loadInjuryHistory(data.athlete_id);
      }

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


          {/* <div className="profile-status">

            <span className="status-dot"></span>

            {profileExists
              ? "Profile active"
              : "Profile not created"
            }

          </div> */}

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


          {/* INJURY HISTORY */}

          <section className="profile-section injury-history-section">

            <div className="section-heading section-heading-actions">

              <div className="section-icon">
                03
              </div>

              <div>

                <h2>
                  Injury History
                </h2>

                <p>
                  Optional records used only for historical risk assessment.
                </p>

              </div>

              {profileExists && (
                <button
                  type="button"
                  className="secondary-button compact-button"
                  onClick={() => {
                    resetInjuryForm();
                    setInjuryFormOpen(true);
                  }}
                >
                  + Add Injury
                </button>
              )}

            </div>


            {!profileExists && (
              <div className="injury-empty-state">
                Create your athlete profile first, then you can add optional injury history.
              </div>
            )}


            {profileExists && injuries.length === 0 && !injuryFormOpen && (
              <div className="injury-empty-state">
                <strong>No injury history added.</strong>
                <span>
                  Injury history is optional, but adding previous injuries can improve historical injury-risk assessment.
                </span>
                <button
                  type="button"
                  className="save-profile-button compact-button"
                  onClick={() => setInjuryFormOpen(true)}
                >
                  + Add Injury
                </button>
              </div>
            )}


            {profileExists && injuries.length > 0 && (
              <div className="injury-table-wrap">
                <table className="injury-table">
                  <thead>
                    <tr>
                      <th>Injury</th>
                      <th>Body Part</th>
                      <th>Side</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {injuries.map((injury) => (
                      <tr key={injury.injury_id}>
                        <td data-label="Injury">{injury.injury_type}</td>
                        <td data-label="Body Part">{injury.body_part}</td>
                        <td data-label="Side">{formatLabel(injury.affected_side)}</td>
                        <td data-label="Severity">{formatLabel(injury.severity)}</td>
                        <td data-label="Status">{formatLabel(injury.status)}</td>
                        <td data-label="Date">{injury.injury_date}</td>
                        <td data-label="Actions">
                          <div className="injury-row-actions">
                            <button
                              type="button"
                              className="secondary-button table-action-button"
                              onClick={() => handleEditInjury(injury)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="secondary-button table-action-button danger-button"
                              onClick={() => handleDeleteInjury(injury)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}


            {injuryFormOpen && (
              <div className="injury-form-panel">
                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="injury_type">Injury Type *</label>
                    <input
                      id="injury_type"
                      type="text"
                      name="injury_type"
                      value={injuryForm.injury_type}
                      onChange={handleInjuryChange}
                      placeholder="e.g. ACL Injury"
                    />
                  </div>

                  <div className="form-field">
                    <label htmlFor="body_part">Body Part *</label>
                    <input
                      id="body_part"
                      type="text"
                      name="body_part"
                      value={injuryForm.body_part}
                      onChange={handleInjuryChange}
                      placeholder="e.g. Knee"
                    />
                  </div>
                </div>

                <div className="form-grid form-grid-three">
                  <div className="form-field">
                    <label htmlFor="affected_side">Affected Side</label>
                    <select
                      id="affected_side"
                      name="affected_side"
                      value={injuryForm.affected_side}
                      onChange={handleInjuryChange}
                    >
                      <option value="LEFT">Left</option>
                      <option value="RIGHT">Right</option>
                      <option value="BILATERAL">Bilateral</option>
                      <option value="NOT_APPLICABLE">Not Applicable</option>
                    </select>
                  </div>

                  <div className="form-field">
                    <label htmlFor="severity">Severity *</label>
                    <select
                      id="severity"
                      name="severity"
                      value={injuryForm.severity}
                      onChange={handleInjuryChange}
                    >
                      <option value="MILD">Mild</option>
                      <option value="MODERATE">Moderate</option>
                      <option value="SEVERE">Severe</option>
                    </select>
                  </div>

                  <div className="form-field">
                    <label htmlFor="status">Status *</label>
                    <select
                      id="status"
                      name="status"
                      value={injuryForm.status}
                      onChange={handleInjuryChange}
                    >
                      <option value="ACTIVE">Active</option>
                      <option value="RECOVERED">Recovered</option>
                      <option value="CHRONIC">Chronic</option>
                      <option value="UNKNOWN">Unknown</option>
                    </select>
                  </div>
                </div>

                <div className="form-grid">
                  <div className="form-field">
                    <label htmlFor="injury_date">Injury Date *</label>
                    <input
                      id="injury_date"
                      type="date"
                      name="injury_date"
                      value={injuryForm.injury_date}
                      onChange={handleInjuryChange}
                    />
                  </div>

                  <div className="form-field">
                    <label htmlFor="recovery_date">Recovery Date</label>
                    <input
                      id="recovery_date"
                      type="date"
                      name="recovery_date"
                      value={injuryForm.recovery_date}
                      onChange={handleInjuryChange}
                      disabled={injuryForm.status === "ACTIVE"}
                    />
                  </div>
                </div>

                <div className="form-field">
                  <label htmlFor="injury_remarks">Remarks</label>
                  <textarea
                    id="injury_remarks"
                    name="remarks"
                    value={injuryForm.remarks}
                    onChange={handleInjuryChange}
                    rows="3"
                    placeholder="Optional notes about treatment, recovery, or restrictions..."
                  />
                </div>

                <div className="injury-form-actions">
                  <button
                    type="button"
                    className="secondary-button compact-button"
                    onClick={handleCancelInjury}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="save-profile-button compact-button"
                    onClick={handleSaveInjury}
                    disabled={savingInjury}
                  >
                    {savingInjury ? "Saving..." : editingInjuryId ? "Update Injury" : "Save Injury"}
                  </button>
                </div>
              </div>
            )}

          </section>


          {/* TRAINING CONTEXT */}

          <section className="profile-section">

            <div className="section-heading">

              <div className="section-icon">
                04
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
                05
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
