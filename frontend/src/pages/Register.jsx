import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { registerUser } from "../services/api";


function Register() {

  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    role: "Athlete",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);


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

    // Basic validation
    if (!formData.name.trim()) {
      setError("Name is required");
      return;
    }

    if (!formData.email.trim()) {
      setError("Email is required");
      return;
    }

    if (!formData.password) {
      setError("Password is required");
      return;
    }

    if (formData.password.length < 8) {
      setError(
        "Password must be at least 8 characters"
      );
      return;
    }

    if (formData.password.length > 72) {
      setError(
        "Password must not exceed 72 characters"
      );
      return;
    }


    try {

      setLoading(true);

      const result = await registerUser(formData);

      console.log("Registration successful:", result);

      setSuccess(
        "Registration successful! Redirecting to login..."
      );

      setTimeout(() => {
        navigate("/login");
      }, 1500);

    } catch (error) {

      setError(error.message);

    } finally {

      setLoading(false);

    }
  };


  return (
    <div>

      <h1>
        Sports Injury Risk Detection
      </h1>

      <h2>
        Create Account
      </h2>


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

        {/* Name */}

        <div>
          <label>
            Name
          </label>

          <br />

          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter your name"
          />
        </div>


        <br />


        {/* Email */}

        <div>
          <label>
            Email
          </label>

          <br />

          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email"
          />
        </div>


        <br />


        {/* Password */}

        <div>
          <label>
            Password
          </label>

          <br />

          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
          />
        </div>


        <br />


        {/* Phone */}

        <div>
          <label>
            Phone
          </label>

          <br />

          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="Enter your phone number"
          />
        </div>


        <br />


        {/* Role */}

        <div>
          <label>
            Role
          </label>

          <br />

          <select
            name="role"
            value={formData.role}
            onChange={handleChange}
          >

            <option value="Athlete">
              Athlete
            </option>

            <option value="Coach">
              Coach
            </option>

            <option value="Physiotherapist">
              Physiotherapist
            </option>

            <option value="Sports Scientist">
              Sports Scientist
            </option>

            <option value="Administrator">
              Administrator
            </option>

          </select>

        </div>


        <br />


        <button
          type="submit"
          disabled={loading}
        >
          {loading
            ? "Creating Account..."
            : "Register"
          }
        </button>

      </form>


      <p>
        Already have an account?{" "}
        <Link to="/login">
          Login
        </Link>
      </p>

    </div>
  );
}


export default Register;