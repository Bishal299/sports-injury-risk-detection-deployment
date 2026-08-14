import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getAthleteProfile,
  createAthleteProfile,
  updateAthleteProfile,
} from "../services/api";


function AthleteProfile() {

  const navigate = useNavigate();

  const [profileExists, setProfileExists] = useState(false);

  const [formData, setFormData] = useState({
    sport: "",
    position: "",
    age: "",
    height: "",
    weight: "",
    training_load: "",
    flexibility: "",
    strength: "",
    balance: "",
    endurance: "",
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
          flexibility: data.flexibility ?? "",
          strength: data.strength ?? "",
          balance: data.balance ?? "",
          endurance: data.endurance ?? "",
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

      const profileData = {
        sport: formData.sport,
        position: formData.position,

        age: Number(formData.age),
        height: Number(formData.height),
        weight: Number(formData.weight),

        training_load: Number(formData.training_load),
        flexibility: Number(formData.flexibility),
        strength: Number(formData.strength),
        balance: Number(formData.balance),
        endurance: Number(formData.endurance),

        coach_notes: formData.coach_notes,
      };


      let data;


      if (profileExists) {

        // Existing profile → UPDATE
        data = await updateAthleteProfile(
          profileData
        );

        setSuccess(
          "Athlete profile updated successfully."
        );

      } else {

        // No profile → CREATE
        data = await createAthleteProfile(
          profileData
        );

        setProfileExists(true);

        setSuccess(
          "Athlete profile created successfully."
        );

      }


      // Make sure the form contains the latest database values
      setFormData({
        sport: data.sport ?? "",
        position: data.position ?? "",
        age: data.age ?? "",
        height: data.height ?? "",
        weight: data.weight ?? "",
        training_load: data.training_load ?? "",
        flexibility: data.flexibility ?? "",
        strength: data.strength ?? "",
        balance: data.balance ?? "",
        endurance: data.endurance ?? "",
        coach_notes: data.coach_notes ?? "",
      });

    } catch (error) {

      setError(error.message);

    } finally {

      setSaving(false);

    }

  };


  if (loading) {

    return (
      <div>
        <h1>Athlete Profile</h1>

        <p>
          Loading profile...
        </p>
      </div>
    );

  }


  return (
    <div>

      <h1>
        Athlete Profile
      </h1>


      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}


      {success && (
        <p style={{ color: "green" }}>
          {success}
        </p>
      )}


      <form onSubmit={handleSubmit}>

        <div>
          <label>Sport</label>
          <br />

          <input
            type="text"
            name="sport"
            value={formData.sport}
            onChange={handleChange}
            placeholder="e.g. Football"
          />
        </div>


        <br />


        <div>
          <label>Position</label>
          <br />

          <input
            type="text"
            name="position"
            value={formData.position}
            onChange={handleChange}
            placeholder="e.g. Forward"
          />
        </div>


        <br />


        <div>
          <label>Age</label>
          <br />

          <input
            type="number"
            name="age"
            value={formData.age}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Height (cm)</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="height"
            value={formData.height}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Weight (kg)</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="weight"
            value={formData.weight}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Training Load</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="training_load"
            value={formData.training_load}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Flexibility</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="flexibility"
            value={formData.flexibility}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Strength</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="strength"
            value={formData.strength}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Balance</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="balance"
            value={formData.balance}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Endurance</label>
          <br />

          <input
            type="number"
            step="0.1"
            name="endurance"
            value={formData.endurance}
            onChange={handleChange}
          />
        </div>


        <br />


        <div>
          <label>Coach Notes</label>
          <br />

          <textarea
            name="coach_notes"
            value={formData.coach_notes}
            onChange={handleChange}
            rows="4"
            cols="40"
          />
        </div>


        <br />


        <button
          type="submit"
          disabled={saving}
        >
          {saving
            ? "Saving..."
            : profileExists
              ? "Update Profile"
              : "Create Profile"
          }
        </button>

      </form>


      <br />


      <button
        onClick={() => navigate("/dashboard")}
      >
        Back to Dashboard
      </button>

    </div>
  );
}


export default AthleteProfile;