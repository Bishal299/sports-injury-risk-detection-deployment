import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

import { registerUser } from "../services/api";
import "../styles/auth.css";


function Register() {

  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");
    setSuccess("");


    if (!name || !email || !password) {

      setError(
        "Please fill in all required fields."
      );

      return;

    }


    try {

      setLoading(true);

      await registerUser({
        name,
        email,
        password,
      });


      setSuccess(
        "Account created successfully. Redirecting to login..."
      );


      setTimeout(() => {
        navigate("/login");
      }, 1200);


    } catch (error) {

      setError(error.message);

    } finally {

      setLoading(false);

    }

  };


  return (

    <div className="auth-page">

      {/* Branding */}

      <div className="auth-brand">

        <div className="auth-brand-content">

          <div className="auth-logo">

            <div className="auth-logo-icon">
              S
            </div>

            <div>
              <h2>SportRisk</h2>
              <span>Injury Detection</span>
            </div>

          </div>


          <div className="auth-brand-text">

            <p className="auth-eyebrow">
              START YOUR JOURNEY
            </p>

            <h1>
              Build a safer
              <br />
              training routine.
            </h1>

            <p>
              Create your athlete account and get
              started with intelligent sports performance
              monitoring.
            </p>

          </div>


          <div className="auth-trust">

            <ShieldCheck size={20} />

            <span>
              Your performance data stays protected
            </span>

          </div>

        </div>

      </div>


      {/* Form */}

      <div className="auth-form-section">

        <div className="auth-form-wrapper">

          <div className="auth-mobile-logo">

            <div className="auth-logo-icon">
              S
            </div>

            <div>
              <h2>SportRisk</h2>
              <span>Injury Detection</span>
            </div>

          </div>


          <div className="auth-heading">

            <p className="auth-eyebrow">
              GET STARTED
            </p>

            <h1>
              Create your account
            </h1>

            <p>
              Set up your athlete profile in a few
              simple steps.
            </p>

          </div>


          {error && (

            <div className="auth-error">
              {error}
            </div>

          )}


          {success && (

            <div className="auth-success">
              {success}
            </div>

          )}


          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >

            {/* Name */}

            <div className="form-group">

              <label htmlFor="name">
                Full name
              </label>

              <div className="input-wrapper">

                <User size={19} />

                <input
                  id="name"
                  type="text"
                  placeholder="Your full name"
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  autoComplete="name"
                />

              </div>

            </div>


            {/* Email */}

            <div className="form-group">

              <label htmlFor="email">
                Email address
              </label>

              <div className="input-wrapper">

                <Mail size={19} />

                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  autoComplete="email"
                />

              </div>

            </div>


            {/* Password */}

            <div className="form-group">

              <label htmlFor="password">
                Password
              </label>

              <div className="input-wrapper">

                <Lock size={19} />

                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  placeholder="Create a password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  autoComplete="new-password"
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                >

                  {showPassword
                    ? <EyeOff size={19} />
                    : <Eye size={19} />
                  }

                </button>

              </div>

            </div>


            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >

              {loading
                ? "Creating account..."
                : (
                  <>
                    Create account
                    <ArrowRight size={19} />
                  </>
                )
              }

            </button>

          </form>


          <div className="auth-divider">
            <span>or</span>
          </div>


          <button
            type="button"
            className="google-button"
            onClick={() => {}}
          >

            <span className="google-icon">
              G
            </span>

            Sign up with Google

          </button>


          <p className="auth-footer">

            Already have an account?{" "}

            <Link to="/login">
              Sign in
            </Link>

          </p>

        </div>

      </div>

    </div>

  );
}


export default Register;