
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { loginUser } from "../services/api";


function Login() {

  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
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

    if (!formData.email.trim()) {
      setError("Email is required");
      return;
    }

    if (!formData.password) {
      setError("Password is required");
      return;
    }


    try {

      setLoading(true);

      const data = await loginUser(formData);

      console.log("Login response:", data);


      // Store JWT token
      localStorage.setItem(
        "access_token",
        data.access_token
      );


      // Store token type
      localStorage.setItem(
        "token_type",
        data.token_type
      );


      // Go to dashboard
      navigate("/dashboard");


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
        Login
      </h2>


      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}


      <form onSubmit={handleSubmit}>

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


        <button
          type="submit"
          disabled={loading}
        >
          {loading
            ? "Logging in..."
            : "Login"
          }
        </button>

      </form>


      <p>
        Don't have an account?{" "}

        <Link to="/register">
          Register
        </Link>
      </p>

    </div>
  );
}


export default Login;