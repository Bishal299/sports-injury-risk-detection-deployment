import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  HeartPulse,
  Lock,
  Mail,
  ShieldCheck,
  UserRound,
  UsersRound,
} from "lucide-react";

import {
  getCurrentUser,
  loginUser,
  loginWithGoogle,
  verifyPortalAccess,
} from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useAthleteProfile } from "../context/AthleteProfileContext";
import { getDefaultRouteForRole } from "../utils/roleRoutes";
import BrandLogo from "../components/BrandLogo";
import "../styles/auth.css";

const PORTAL_OPTIONS = [
  {
    id: "ATHLETE",
    label: "Athlete",
    description: "Track your movement & analyses",
    icon: UserRound,
  },
  {
    id: "COACH",
    label: "Coach",
    description: "Manage athletes & training",
    icon: UsersRound,
  },
  {
    id: "PHYSIOTHERAPIST",
    label: "Physiotherapist",
    description: "Manage rehabilitation & recovery",
    icon: HeartPulse,
  },
  {
    id: "SPORTS_SCIENTIST",
    label: "Sports Scientist",
    description: "Analyze biomechanics & performance",
    icon: Activity,
  },
  {
    id: "ADMINISTRATOR",
    label: "Administrator",
    description: "Manage the SportRisk platform",
    icon: ShieldCheck,
  },
];

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { refreshProfileStatus } = useAthleteProfile();
  const {
    sessionExpiredMsg: authExpiredMsg,
    clearSessionExpiredMsg,
    setAuthenticatedUser,
    checkAuth,
  } = useAuth();

  const [selectedPortal, setSelectedPortal] = useState("ATHLETE");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [portalError, setPortalError] = useState(null);
  const [sessionExpiredMsg, setSessionExpiredMsg] = useState("");

  const portalButtonRefs = useRef([]);
  const selectedPortalRef = useRef(selectedPortal);

  useEffect(() => {
    selectedPortalRef.current = selectedPortal;
  }, [selectedPortal]);

  useEffect(() => {
    if (location.state?.expiredMessage) {
      setSessionExpiredMsg(location.state.expiredMessage);
    } else if (authExpiredMsg) {
      setSessionExpiredMsg(authExpiredMsg);
    } else {
      setSessionExpiredMsg("");
    }
  }, [location.state, authExpiredMsg]);

  const handleSelectPortal = (portalId) => {
    setSelectedPortal(portalId);
    if (portalError) {
      setPortalError(null);
    }
    if (error) {
      setError("");
    }
  };

  const handlePortalKeyDown = (event, index) => {
    let nextIndex = index;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      nextIndex = (index + 1) % PORTAL_OPTIONS.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      nextIndex = (index - 1 + PORTAL_OPTIONS.length) % PORTAL_OPTIONS.length;
    } else if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      handleSelectPortal(PORTAL_OPTIONS[index].id);
      return;
    } else {
      return;
    }

    const nextOption = PORTAL_OPTIONS[nextIndex];
    handleSelectPortal(nextOption.id);
    if (portalButtonRefs.current[nextIndex]) {
      portalButtonRefs.current[nextIndex].focus();
    }
  };

  const processPortalRedirect = async (portalId) => {
    const portalVerification = await verifyPortalAccess(portalId);

    if (portalVerification.authorized) {
      if (portalVerification.user_role === "Athlete") {
        await refreshProfileStatus();
      }
      navigate(
        portalVerification.default_route ||
          getDefaultRouteForRole(portalVerification.user_role)
      );
      return true;
    }

    const activeOption = PORTAL_OPTIONS.find((p) => p.id === portalId);
    setPortalError({
      headline: portalVerification.headline || "Access Unavailable",
      message:
        portalVerification.message ||
        "This account is not authorized for the selected portal.",
      secondary_message: portalVerification.secondary_message,
      defaultRoute:
        portalVerification.default_route ||
        getDefaultRouteForRole(portalVerification.user_role),
      canContinueAsAthlete: Boolean(portalVerification.can_continue_as_athlete),
      requestRoleUrl: portalVerification.request_role_url,
      targetRoleLabel: activeOption ? activeOption.label : portalId,
      userRole: portalVerification.user_role,
    });
    return false;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setPortalError(null);
    setSessionExpiredMsg("");
    clearSessionExpiredMsg();

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const loginRes = await loginUser({
        email: cleanEmail,
        password,
      });

      if (loginRes?.user) {
        setAuthenticatedUser(loginRes.user);
      } else {
        await checkAuth();
      }

      await processPortalRedirect(selectedPortal);
    } catch (err) {
      setError(err.message || "Failed to sign in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleCredential = async (credentialResponse) => {
    setError("");
    setPortalError(null);
    setSessionExpiredMsg("");
    clearSessionExpiredMsg();
    setGoogleLoading(true);

    try {
      const token = credentialResponse?.credential;
      if (!token) {
        throw new Error("No Google credential received.");
      }

      const loginRes = await loginWithGoogle(token);
      if (loginRes?.user) {
        setAuthenticatedUser(loginRes.user);
      } else {
        await checkAuth();
      }

      await processPortalRedirect(selectedPortalRef.current);
    } catch (err) {
      setError(err.message || "Google authentication failed. Please try again.");
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleContinueToAuthorizedPortal = async (targetRoute) => {
    try {
      const currentUser = await getCurrentUser();
      if (currentUser.role === "Athlete") {
        await refreshProfileStatus();
      }
      navigate(targetRoute || getDefaultRouteForRole(currentUser.role));
    } catch {
      navigate(targetRoute || "/dashboard");
    }
  };

  return (
    <div className="auth-page">
      {/* Left branding section */}
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-logo">
            <BrandLogo />
          </div>

          <div className="auth-brand-text">
            <p className="auth-eyebrow">AI-POWERED SPORTS ANALYTICS</p>

            <h1>
              Train smarter.
              <br />
              Stay safer.
            </h1>

            <p>
              Monitor your athletic performance and identify potential injury
              risks through intelligent video analysis.
            </p>
          </div>

          <div className="auth-trust">
            <ShieldCheck size={20} />
            <span>Built for athletes and performance teams</span>
          </div>
        </div>
      </div>

      {/* Login section */}
      <div className="auth-form-section">
        <div className="auth-form-wrapper">
          <div className="auth-mobile-logo">
            <BrandLogo />
          </div>

          <div className="auth-heading">
            <p className="auth-eyebrow">WELCOME BACK</p>
            <h1>Sign in to your account</h1>
            <p>
              Select your portal and continue monitoring your performance and
              injury risk.
            </p>
          </div>

          {/* Role Portal Selector */}
          <div className="portal-selector-section">
            <div className="portal-selector-header">
              <span className="portal-selector-label">Login as</span>
              <span className="portal-selector-hint">
                Selected:{" "}
                <strong>
                  {PORTAL_OPTIONS.find((p) => p.id === selectedPortal)?.label}
                </strong>
              </span>
            </div>

            <div
              className="portal-grid"
              role="radiogroup"
              aria-label="Select SportRisk login portal"
            >
              {PORTAL_OPTIONS.map((portal, index) => {
                const IconComponent = portal.icon;
                const isSelected = selectedPortal === portal.id;

                return (
                  <button
                    key={portal.id}
                    ref={(el) => (portalButtonRefs.current[index] = el)}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    tabIndex={isSelected ? 0 : -1}
                    className={`portal-card ${
                      isSelected ? "portal-card--selected" : ""
                    } ${portal.id === "ADMINISTRATOR" ? "portal-card--admin" : ""}`}
                    onClick={() => handleSelectPortal(portal.id)}
                    onKeyDown={(e) => handlePortalKeyDown(e, index)}
                  >
                    <div className="portal-card-top">
                      <div className="portal-card-identity">
                        <div className="portal-icon-wrapper">
                          <IconComponent size={16} />
                        </div>
                        <span className="portal-title">{portal.label}</span>
                      </div>
                      <span className="portal-radio-indicator">
                        {isSelected && <CheckCircle2 size={15} />}
                      </span>
                    </div>

                    <span className="portal-desc">{portal.description}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Session Expired Notice */}
          {sessionExpiredMsg && (
            <div
              className="auth-warning"
              style={{
                padding: "12px 14px",
                borderRadius: "8px",
                background: "rgba(245, 158, 11, 0.12)",
                border: "1px solid rgba(245, 158, 11, 0.35)",
                color: "#f59e0b",
                fontSize: "0.88rem",
                fontWeight: 600,
                marginBottom: "14px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <AlertCircle size={18} />
              <span>{sessionExpiredMsg}</span>
            </div>
          )}

          {/* Standard Authentication Error */}
          {error && <div className="auth-error">{error}</div>}

          {/* Professional Role / Portal Access Denied Notice */}
          {portalError && (
            <div
              className="portal-access-notice"
              role="alert"
              aria-live="polite"
            >
              <div className="portal-access-header">
                <AlertCircle size={20} className="portal-access-icon" />
                <div className="portal-access-titles">
                  <h4>{portalError.headline}</h4>
                  <p className="portal-access-msg">{portalError.message}</p>
                  {portalError.secondary_message && (
                    <p className="portal-access-submsg">
                      {portalError.secondary_message}
                    </p>
                  )}
                </div>
              </div>

              <div className="portal-access-actions">
                {portalError.canContinueAsAthlete ? (
                  <button
                    type="button"
                    className="portal-btn-primary"
                    onClick={() =>
                      handleContinueToAuthorizedPortal(portalError.defaultRoute)
                    }
                  >
                    Continue as Athlete
                    <ArrowRight size={16} />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="portal-btn-primary"
                    onClick={() =>
                      handleContinueToAuthorizedPortal(portalError.defaultRoute)
                    }
                  >
                    Continue to Dashboard
                    <ArrowRight size={16} />
                  </button>
                )}

                {portalError.requestRoleUrl && (
                  <Link
                    to={portalError.requestRoleUrl}
                    className="portal-btn-secondary"
                  >
                    Request {portalError.targetRoleLabel} Role
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* Single Unified Credentials Form */}
          <form className="auth-form" onSubmit={handleSubmit}>
            {/* Email */}
            <div className="form-group">
              <label htmlFor="email">Email address</label>

              <div className="input-wrapper">
                <Mail size={19} />
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-group">
              <div className="password-label-row">
                <label htmlFor="password">Password</label>

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
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-submit"
              disabled={loading || googleLoading}
            >
              {loading ? (
                "Signing in..."
              ) : (
                <>
                  Sign in to{" "}
                  {PORTAL_OPTIONS.find((p) => p.id === selectedPortal)?.label ||
                    "SportRisk"}
                  <ArrowRight size={19} />
                </>
              )}
            </button>
          </form>

          {/* Google Divider & Container */}
          <div className="auth-divider">
            <span>or</span>
          </div>

          <div
            className="google-button-container"
            aria-label="Continue with Google"
          >
            <GoogleLogin
              onSuccess={handleGoogleCredential}
              onError={() => setError("Google Sign In was not successful. Please ensure origin is authorized in Google Cloud Console.")}
              theme="outline"
              size="large"
              width="100%"
              text="continue_with"
              shape="rectangular"
            />
          </div>

          <p className="auth-footer">
            Don't have an account? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
