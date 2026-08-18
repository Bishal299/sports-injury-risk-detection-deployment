import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import {
  Eye,
  EyeOff,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

import {
  loginUser,
  loginWithGoogle
} from "../services/api";
import { useAthleteProfile } from "../context/AthleteProfileContext";
import "../styles/auth.css";


function Login() {

  const navigate = useNavigate();
  const { refreshProfileStatus } = useAthleteProfile();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const googleButtonRef = useRef(null);

  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {

      setLoading(true);

      const data = await loginUser({
        email,
        password,
      });

      localStorage.setItem(
        "access_token",
        data.access_token
      );

      localStorage.setItem(
        "token_type",
        data.token_type
      );

      await refreshProfileStatus();
      navigate("/dashboard");

    } catch (error) {

      setError(error.message);

    } finally {

      setLoading(false);

    }

  };

  const handleGoogleCredential = async (response) => {
  setError("");
  setGoogleLoading(true);

  try {
    const data = await loginWithGoogle(
      response.credential
    );

    localStorage.setItem(
      "access_token",
      data.access_token
    );

    localStorage.setItem(
      "token_type",
      data.token_type
    );

    await refreshProfileStatus();
    navigate("/dashboard");

  } catch (error) {

    setError(error.message);

  } finally {

    setGoogleLoading(false);

  }
 };

 useEffect(() => {

  const initializeGoogle = () => {

    if (
      !window.google ||
      !googleButtonRef.current
    ) {
      return;
    }

    window.google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,

      callback: handleGoogleCredential,
    });

    window.google.accounts.id.renderButton(
      googleButtonRef.current,
      {
        theme: "outline",
        size: "large",
        width: 400,
        text: "continue_with",
        shape: "rectangular",
      }
    );
  };


  if (window.google) {

    initializeGoogle();

  } else {

    const interval = setInterval(() => {

      if (window.google) {

        clearInterval(interval);

        initializeGoogle();

      }

    }, 100);

    return () => clearInterval(interval);
  }

 }, []);


  return (

    <div className="auth-page">

      {/* Left branding section */}

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
              AI-POWERED SPORTS ANALYTICS
            </p>

            <h1>
              Train smarter.
              <br />
              Stay safer.
            </h1>

            <p>
              Monitor your athletic performance and
              identify potential injury risks through
              intelligent video analysis.
            </p>

          </div>


          <div className="auth-trust">

            <ShieldCheck size={20} />

            <span>
              Built for athletes and performance teams
            </span>

          </div>

        </div>

      </div>


      {/* Login section */}

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
              WELCOME BACK
            </p>

            <h1>
              Sign in to your account
            </h1>

            <p>
              Continue monitoring your performance
              and injury risk.
            </p>

          </div>


          {error && (

            <div className="auth-error">
              {error}
            </div>

          )}


          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >

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

              <div className="password-label-row">

                <label htmlFor="password">
                  Password
                </label>

                <button
                  type="button"
                  className="forgot-password"
                  onClick={() => {}}
                >
                  Forgot password?
                </button>

              </div>


              <div className="input-wrapper">

                <Lock size={19} />

                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  autoComplete="current-password"
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


            {/* Submit */}

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >

              {loading
                ? "Signing in..."
                : (
                  <>
                    Sign in
                    <ArrowRight size={19} />
                  </>
                )
              }

            </button>

          </form>


          {/* Google placeholder */}

          <div className="auth-divider">

            <span>or</span>

          </div>


          {/* <button
            type="button"
            className="google-button"
            onClick={() => {}}
          >

            <span className="google-icon">
              G
            </span>

            Continue with Google

          </button> */}
          <div
            ref={googleButtonRef}
            className="google-button-container"
          />


          <p className="auth-footer">

            Don't have an account?{" "}

            <Link to="/register">
              Create an account
            </Link>

          </p>

        </div>

      </div>

    </div>

  );
}


export default Login;
