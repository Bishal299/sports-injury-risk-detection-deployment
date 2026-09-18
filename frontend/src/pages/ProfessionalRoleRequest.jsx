import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BadgeCheck,
  BriefcaseBusiness,
  Clock3,
  ShieldCheck,
  Stethoscope,
  XCircle,
} from "lucide-react";

import DashboardLayout from "../layouts/DashboardLayout";
import {
  getCurrentUser,
  getMyProfessionalRoleRequestStatus,
} from "../services/api";
import "../styles/professional-role.css";


const roleOptions = [
  {
    key: "COACH",
    label: "Coach",
    description: "Apply to connect with athletes after admin verification.",
    icon: BriefcaseBusiness,
    path: "/request-professional-role/coach",
    enabled: true,
  },
  {
    key: "PHYSIOTHERAPIST",
    label: "Physiotherapist",
    description: "Apply for verified rehabilitation and recovery access workflows.",
    icon: Stethoscope,
    path: "/request-professional-role/physiotherapist",
    enabled: true,
  },
  {
    key: "SPORTS_SCIENTIST",
    label: "Sports Scientist",
    description: "Apply for verified biomechanical analytics and sports-science research access.",
    icon: ShieldCheck,
    path: "/request-professional-role/sports-scientist",
    enabled: true,
  },
];

const approvedRoleRoutes = {
  COACH: {
    label: "Open Coach Environment",
    path: "/coach/dashboard",
  },
  PHYSIOTHERAPIST: {
    label: "Open Physiotherapist Environment",
    path: "/physio/dashboard",
  },
  SPORTS_SCIENTIST: {
    label: "Open Sports Scientist Environment",
    path: "/sports-scientist/dashboard",
  },
};


function statusIcon(status) {
  if (status === "APPROVED") {
    return BadgeCheck;
  }

  if (status === "REJECTED") {
    return XCircle;
  }

  return Clock3;
}


function formatRole(value) {
  return String(value || "").replaceAll("_", " ");
}


function approvedRoleLabel(value) {
  return `Verified ${formatRole(value).toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase())}`;
}


function formatDate(value) {
  if (!value) {
    return "Recently";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Recently";
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}


function ProfessionalRoleRequest() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [latestRequest, setLatestRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadRequestStatus() {
      setLoading(true);
      setError("");

      try {
        const [currentUser, requestStatus] = await Promise.all([
          getCurrentUser(),
          getMyProfessionalRoleRequestStatus(),
        ]);

        if (!cancelled) {
          setUser(currentUser);
          setLatestRequest(requestStatus);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message || "Failed to load professional role status.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadRequestStatus();

    const refreshUser = () => loadRequestStatus();
    window.addEventListener("user-role-updated", refreshUser);

    return () => {
      cancelled = true;
      window.removeEventListener("user-role-updated", refreshUser);
    };
  }, []);

  const StatusIcon = useMemo(
    () => statusIcon(latestRequest?.status),
    [latestRequest]
  );

  return (
    <DashboardLayout>
      <main className="professional-page">
        <section className="page-header">
          <p className="page-eyebrow">PROFESSIONAL ACCESS</p>
          <h1>Request Professional Role</h1>
          <p>Submit your professional profile for verification by an administrator.</p>
        </section>

        {loading && (
          <section className="professional-card">
            <div className="professional-skeleton wide" />
            <div className="professional-skeleton" />
          </section>
        )}

        {!loading && error && (
          <section className="professional-card professional-alert">
            <XCircle size={22} />
            <div>
              <h2>Unable to load status</h2>
              <p>{error}</p>
            </div>
          </section>
        )}

        {!loading && !error && latestRequest && (
          <section className={`professional-status-card ${latestRequest.status.toLowerCase()}`}>
            <div className="professional-status-icon">
              <StatusIcon size={24} />
            </div>

            <div>
              <span>Professional Role Request</span>
              <h2>Role: {formatRole(latestRequest.requested_role)}</h2>
              <p>Status: {latestRequest.status.replace("_", " ")}</p>
              <p>
                Submitted {formatDate(latestRequest.submitted_at)}
                {latestRequest.reviewed_at
                  ? `, reviewed ${formatDate(latestRequest.reviewed_at)}`
                  : ""}
              </p>

              {latestRequest.status === "PENDING" && (
                <p className="professional-muted">
                  Professional access remains locked until an administrator approves this request.
                </p>
              )}

              {latestRequest.status === "APPROVED" && (
                <>
                  <p className="professional-muted">
                    Approved: {approvedRoleLabel(latestRequest.requested_role)}.
                  </p>
                  {approvedRoleRoutes[latestRequest.requested_role] && (
                    <button
                      className="primary-button professional-inline-action"
                      onClick={() => navigate(approvedRoleRoutes[latestRequest.requested_role].path)}
                      type="button"
                    >
                      {approvedRoleRoutes[latestRequest.requested_role].label}
                    </button>
                  )}
                </>
              )}

              {latestRequest.status === "REJECTED" && latestRequest.rejection_reason && (
                <div className="professional-rejection">
                  <strong>Reason:</strong>
                  <p>{latestRequest.rejection_reason}</p>
                </div>
              )}
            </div>
          </section>
        )}

        {!loading && !error && (!latestRequest || latestRequest.status === "REJECTED") && (
          <section className="role-selection-grid">
            {roleOptions.map((role) => {
              const Icon = role.icon;

              return (
                <article className="role-option-card" key={role.key}>
                  <div className="role-option-icon">
                    <Icon size={24} />
                  </div>

                  <div>
                    <h2>{role.label}</h2>
                    <p>{role.description}</p>
                  </div>

                  <button
                    className={role.enabled ? "primary-button" : "secondary-button"}
                    disabled={!role.enabled}
                    onClick={() => role.enabled && navigate(role.path)}
                    type="button"
                  >
                    {role.enabled ? "Apply" : "Coming Soon"}
                  </button>
                </article>
              );
            })}
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}


export default ProfessionalRoleRequest;
