import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  FileClock,
  HeartPulse,
  ShieldCheck,
  Upload,
  Video,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import RecentActivity from "../../components/athlete-dashboard/RecentActivity";
import {
  getAthleteCoachRequests,
  getAthleteConnectedCoaches,
  getAthleteConnectedPhysiotherapists,
  getAthleteConnectedSportsScientists,
  getAthletePhysiotherapistRequests,
  getAthleteSportsScientistRequests,
  getAnalysisHistory,
  getAthleteProfile,
  getCurrentUser,
  getInjuryHistory,
  getAnalysisById,
  getMyVideos,
  revokeCoachAccess,
  revokePhysiotherapistAccess,
  revokeSportsScientistAccess,
} from "../../services/api";

import "../../styles/dashboard.css";


const PROFILE_COMPLETION_FIELDS = [
  { key: "sport", label: "Sport" },
  { key: "position", label: "Position" },
  { key: "age", label: "Age" },
  { key: "height", label: "Height" },
  { key: "weight", label: "Weight" },
  { key: "training_load", label: "Training Load" },
  { key: "flexibility", label: "Flexibility" },
  { key: "strength", label: "Strength" },
  { key: "balance", label: "Balance" },
  { key: "endurance", label: "Endurance" },
];


const completedStatuses = new Set(["analyzed", "completed"]);
const pendingStatuses = new Set(["uploaded", "pending", "processing"]);
const failedStatuses = new Set(["failed", "error"]);


function hasValue(value) {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === "string") {
    return value.trim().length > 0;
  }

  return true;
}


function getGreeting(name) {
  const hour = new Date().getHours();

  if (hour >= 4 && hour < 12) {
    return `Good Morning, ${name}`;
  }

  if (hour >= 12 && hour < 17) {
    return `Good Afternoon, ${name}`;
  }

  return `Good Evening, ${name}`;
}


function normalizeStatus(status) {
  const value = String(status || "uploaded").toLowerCase();

  if (completedStatuses.has(value)) {
    return "Completed";
  }

  if (failedStatuses.has(value)) {
    return "Failed";
  }

  return "Pending";
}


function getVideoStatus(video, completedVideoIds) {
  if (completedVideoIds.has(String(video.video_id))) {
    return "Completed";
  }

  return normalizeStatus(video.processing_status);
}


function calculateProfileCompletion(profile) {
  const completedFields = PROFILE_COMPLETION_FIELDS.filter((field) =>
    hasValue(profile?.[field.key])
  );

  const missingLabels = PROFILE_COMPLETION_FIELDS
    .filter((field) => !hasValue(profile?.[field.key]))
    .map((field) => field.label);

  return {
    completed: completedFields.length,
    total: PROFILE_COMPLETION_FIELDS.length,
    percent: Math.round(
      (completedFields.length / PROFILE_COMPLETION_FIELDS.length) * 100
    ),
    missingLabels,
  };
}


function parseDate(value) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}


function formatDate(value) {
  const parsed = parseDate(value);

  if (!parsed) {
    return "Recently";
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatChartDate(value) {
  const parsed = parseDate(value);

  if (!parsed) {
    return "";
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}


function formatDateTime(value) {
  const parsed = parseDate(value);

  if (!parsed) {
    return "Recently";
  }

  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function getAnalysisDate(analysis) {
  return analysis?.completed_at || analysis?.analysis_date || analysis?.created_at;
}

function getRiskScore(analysis) {
  if (!analysis) return null;
  const value = analysis.composite_risk_score ?? analysis.overall_risk_score;
  return value === null || value === undefined || Number.isNaN(Number(value)) ? null : Number(value);
}

function getPath(source, path) {
  return path.split(".").reduce((current, part) => {
    if (current === null || current === undefined) return undefined;
    return current[part];
  }, source);
}

function firstExisting(source, paths) {
  for (const path of paths) {
    const value = getPath(source, path);
    if (value !== null && value !== undefined && value !== "") {
      return value;
    }
  }
  return null;
}

function getBreakdownValue(analysis, key) {
  const target = analysis?.biomechanical_breakdown?.find((item) => item.key === key);
  return target?.average_risk ?? target?.risk ?? target?.score ?? target?.value ?? null;
}

function getAnalysisMetric(analysis, paths) {
  const value = firstExisting(analysis, paths);
  if (value !== null) {
    return value;
  }

  const breakdownPath = paths.find((path) => path.startsWith("breakdown."));
  if (breakdownPath) {
    return getBreakdownValue(analysis, breakdownPath.replace("breakdown.", ""));
  }

  return null;
}

function formatMetric(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "No data";
  const numeric = Number(value);
  return `${Number.isInteger(numeric) ? numeric : numeric.toFixed(1)}${suffix}`;
}

function riskLabel(analysis) {
  const explicit = analysis?.risk_category;
  if (explicit) return String(explicit).replaceAll("_", " ");
  return "No data";
}

function riskClass(value) {
  return String(value || "not-available").toLowerCase().replace(/\s+/g, "-");
}

function riskColor(value) {
  return "#2f6df6";
}

function percentFromValue(value, max = 100) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 0;
  return Math.max(0, Math.min(100, (Number(value) / max) * 100));
}

function StatCard({ stat }) {
  const Icon = stat.icon;
  return (
    <article className={`athlete-stat-card polished ${stat.tone || ""}`}>
      <div className="athlete-stat-icon"><Icon size={21} /></div>
      <div>
        <span>{stat.label}</span>
        <strong>{stat.value}</strong>
        <small>{stat.meta || "-"}</small>
      </div>
    </article>
  );
}

function RecentAnalysisOverview({ analysis, latestVideo }) {
  if (!analysis) {
    return (
      <section className="athlete-dashboard-card analysis-overview-card">
        <div className="athlete-card-header">
          <div><h2>Recent Analysis Overview</h2><p>No completed analysis is available yet.</p></div>
        </div>
        <div className="athlete-empty-mini">
          <BarChart3 size={24} />
          <h2>Upload and analyze a video</h2>
          <p>Your latest biomechanical metrics will appear here once an analysis completes.</p>
        </div>
      </section>
    );
  }

  const score = getRiskScore(analysis);
  const label = riskLabel(analysis);
  const kneeValgus = getAnalysisMetric(analysis, ["knee_valgus", "summary_metrics.knee_valgus.score", "summary_metrics.knee_valgus.risk_score", "breakdown.knee_valgus"]);
  const hipStability = getAnalysisMetric(analysis, ["hip_stability", "summary_metrics.hip_stability.score", "summary_metrics.hip_stability.stability_score", "breakdown.hip_stability"]);
  const trunkLean = getAnalysisMetric(analysis, ["trunk_lean", "summary_metrics.trunk_lean.score", "summary_metrics.trunk_lean.trunk_control_score", "breakdown.trunk_lean"]);
  const symmetry = getAnalysisMetric(analysis, ["symmetry_score", "summary_metrics.symmetry.overall_symmetry_score", "summary_metrics.symmetry.score", "symmetry.overall_symmetry"]);
  const landing = getAnalysisMetric(analysis, ["landing_score", "force_score", "summary_metrics.landing.score", "summary_metrics.landing.landing_score", "summary_metrics.landing_mechanics.score", "breakdown.landing_mechanics"]);

  const toControlScore = (riskValue) => {
    if (riskValue === null || riskValue === undefined || Number.isNaN(Number(riskValue))) {
      return null;
    }
    const numeric = Number(riskValue);
    return Math.max(0, Math.min(100, 100 - numeric));
  };

  const kneeControl = toControlScore(kneeValgus);
  const hipControl = toControlScore(hipStability);
  const postureControl = toControlScore(trunkLean);

  const getMetricTone = (controlValue, baseTone) => {
    if (controlValue === null || controlValue === undefined || Number.isNaN(Number(controlValue))) {
      return baseTone;
    }
    const val = Number(controlValue);
    if (val < 50) return "danger";
    return baseTone;
  };

  const metrics = [
    { label: "Knee Control", value: kneeControl, display: formatMetric(kneeControl, "/100"), width: percentFromValue(kneeControl), tone: getMetricTone(kneeControl, "primary") },
    { label: "Hip Control", value: hipControl, display: formatMetric(hipControl, "/100"), width: percentFromValue(hipControl), tone: getMetricTone(hipControl, "success") },
    { label: "Posture Control", value: postureControl, display: formatMetric(postureControl, "/100"), width: percentFromValue(postureControl), tone: getMetricTone(postureControl, "cyan") },
    { label: "Movement Symmetry", value: symmetry, display: formatMetric(symmetry, "%"), width: percentFromValue(symmetry), tone: getMetricTone(symmetry, "indigo") },
    { label: "Landing Control", value: landing, display: formatMetric(landing, "/100"), width: percentFromValue(landing), tone: getMetricTone(landing, "purple") },
  ];

  return (
    <section className="athlete-dashboard-card analysis-overview-card">
      <div className="athlete-card-header">
        <div>
          <h2>Recent Analysis Overview</h2>
          <p>Key movement and performance indicators from your latest analysis.</p>
        </div>
        <span className="athlete-soft-select">{analysis.video?.activity || latestVideo?.activity || "Latest Analysis"}</span>
      </div>

      <div className="analysis-overview-body">
        <div className="risk-donut-wrap">
          <div
            className={`risk-score-donut ${riskClass(label)}`}
            style={{
              "--score": Math.max(0, Math.min(100, score ?? 0)),
              "--risk-color": riskColor(label),
            }}
          >
            <strong>{score === null ? "-" : Math.round(score)}</strong>
            <span>/100</span>
          </div>
          <p>Overall Risk Score</p>
          <span className={`analysis-risk-pill ${riskClass(label)}`}>{label}</span>
        </div>

        <div className="analysis-metric-list">
          {metrics.map((metric) => (
            <div className="analysis-metric-row" key={metric.label}>
              <div><span>{metric.label}</span><strong>{metric.display}</strong></div>
              <div className="analysis-metric-track"><i className={metric.tone} style={{ width: `${Math.max(metric.width, metric.value === null || metric.value === undefined ? 0 : 6)}%` }} /></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PerformanceTrends({ analyses }) {
  const points = [...analyses]
    .filter((analysis) => normalizeStatus(analysis.status) === "Completed" && getAnalysisDate(analysis))
    .sort((a, b) => (parseDate(getAnalysisDate(a))?.getTime() || 0) - (parseDate(getAnalysisDate(b))?.getTime() || 0))
    .slice(-7);

  if (points.length === 0) {
    return (
      <section className="athlete-dashboard-card trends-card">
        <div className="athlete-card-header"><div><h2>Performance Trends</h2><p>No completed analyses to chart yet.</p></div></div>
        <div className="activity-empty">Trend data appears after completed analyses.</div>
      </section>
    );
  }

  const series = [
    { key: "movement_quality", label: "Movement Quality", color: "#3b82f6" },
    { key: "biomechanical_efficiency", label: "Biomechanical Efficiency", color: "#34d399", value: (analysis) => getAnalysisMetric(analysis, ["biomechanical_efficiency.final", "biomechanical_efficiency", "biomechanical_score"]) },
    { key: "risk", label: "Risk Score", color: "#fb923c", value: getRiskScore },
  ];
  const width = 620;
  const height = 220;
  const pad = { left: 38, right: 18, top: 18, bottom: 34 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;

  function getPoint(definition, analysis, index) {
      const raw = definition.value ? definition.value(analysis) : analysis[definition.key];
      const value = raw === null || raw === undefined || Number.isNaN(Number(raw)) ? null : Number(raw);
      const x = points.length > 1 ? pad.left + (index / (points.length - 1)) * plotWidth : pad.left + plotWidth / 2;
      const y = value === null ? null : pad.top + plotHeight - (Math.max(0, Math.min(120, value)) / 120) * plotHeight;
      return { x, y, value };
  }

  function pointPath(definition) {
    return points
      .map((analysis, index) => getPoint(definition, analysis, index))
      .filter((point) => point.y !== null)
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
      .join(" ");
  }

  return (
    <section className="athlete-dashboard-card trends-card">
      <div className="athlete-card-header">
        <div><h2>Performance Trends</h2><p>Your completed analysis metrics over time.</p></div>
        <span className="athlete-soft-select">Latest {points.length}</span>
      </div>
      <div className="athlete-trend-layout">
        <svg className="athlete-trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Athlete performance trend chart">
          {[0, 30, 60, 90, 120].map((tick) => {
            const y = pad.top + plotHeight - (tick / 120) * plotHeight;
            return (
              <g key={tick}>
                <line x1={pad.left} x2={pad.left + plotWidth} y1={y} y2={y} />
                <text x={pad.left - 8} y={y + 4}>{tick}</text>
              </g>
            );
          })}
          {series.map((definition) => {
            const path = pointPath(definition);
            return (
              <g key={definition.key}>
                {path && <path d={path} style={{ stroke: definition.color }} />}
                {points.map((analysis, index) => {
                  const point = getPoint(definition, analysis, index);
                  if (point.y === null) return null;
                  return <circle key={`${definition.key}-${analysis.analysis_id || index}`} cx={point.x} cy={point.y} r="4" style={{ fill: definition.color }} />;
                })}
              </g>
            );
          })}
          {points.map((analysis, index) => {
            const x = points.length > 1 ? pad.left + (index / (points.length - 1)) * plotWidth : pad.left + plotWidth / 2;
            return <text className="x-label" key={analysis.analysis_id || index} x={x} y={height - 10}>{formatChartDate(getAnalysisDate(analysis))}</text>;
          })}
        </svg>
        <div className="athlete-trend-legend">
          {series.map((definition) => <span key={definition.key}><i style={{ background: definition.color }} />{definition.label}</span>)}
        </div>
      </div>
    </section>
  );
}

function QuickActionPanel({ onNavigate }) {
  const actions = [
    { label: "Upload Video", path: "/video-upload", icon: Upload, tone: "primary" },
    { label: "View Analysis", path: "/analysis-history", icon: BarChart3, tone: "purple" },
    { label: "My Work", path: "/my-work", icon: ClipboardList, tone: "success" },
  ];
  return (
    <section className="athlete-dashboard-card quick-panel-card">
      <div className="athlete-card-header"><div><h2>Quick Actions</h2><p>Jump back into the most common actions.</p></div></div>
      <div className="athlete-polished-actions">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button className={`athlete-polished-action ${action.tone}`} key={action.path} type="button" onClick={() => onNavigate(action.path)}>
              <span><Icon size={20} /></span>
              <strong>{action.label}</strong>
              <ChevronRight size={18} />
            </button>
          );
        })}
      </div>
      <div className="athlete-motivation-card">
        <div className="runner-mark"><BarChart3 size={30} /></div>
        <div><strong>Stay consistent</strong><p>Small improvements lead to better movement insights.</p></div>
        <button type="button" onClick={() => onNavigate("/analysis-history")}>View All Analyses</button>
      </div>
    </section>
  );
}

function getLatestCompletedAnalysis(analyses) {
  return [...analyses]
    .filter((analysis) => normalizeStatus(analysis.status) === "Completed")
    .sort((a, b) => {
      const dateA = parseDate(getAnalysisDate(a))?.getTime() || 0;
      const dateB = parseDate(getAnalysisDate(b))?.getTime() || 0;
      return dateB - dateA;
    })[0] || null;
}

function isWithinLastDays(value, days) {
  const parsed = parseDate(value);
  if (!parsed) {
    return false;
  }

  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  return parsed.getTime() >= cutoff;
}

function getProfessionalName(item, fallback) {
  return item.coach_name || item.professional_name || item.physiotherapist_name || fallback;
}

function getProfessionalEmail(item) {
  return item.coach_email || item.professional_email || item.physiotherapist_email || null;
}

function getProfessionalSpecialization(item) {
  return item.coaching_specialization || item.specialization || null;
}

function ProfessionalsPreview({ coaches, physiotherapists, scientists, onSelect }) {
  const rows = [
    ...coaches.map((item) => ({ ...item, name: getProfessionalName(item, "Coach"), role: "Coach", type: "coach", date: item.accepted_at || item.created_at, id: item.relationship_id })),
    ...physiotherapists.map((item) => ({ ...item, name: getProfessionalName(item, "Physiotherapist"), role: "Physiotherapist", type: "physiotherapist", date: item.accepted_at || item.created_at, id: item.relationship_id })),
    ...scientists.map((item) => ({ ...item, name: getProfessionalName(item, "Sports Scientist"), role: "Sports Scientist", type: "sports-scientist", date: item.accepted_at || item.created_at, id: item.relationship_id })),
  ].slice(0, 3);

  return (
    <section className="athlete-dashboard-card professionals-preview-card">
      <div className="athlete-card-header"><div><h2>Your Connected Professionals</h2><p>Manage coaches, physiotherapists and sports scientists.</p></div></div>
      {rows.length === 0 ? (
        <div className="activity-empty"><ShieldCheck size={18} />No active professional connections yet.</div>
      ) : (
        <div className="professional-preview-list">
          {rows.map((row) => (
            <button key={row.id} type="button" onClick={() => onSelect(row)}>
              <span>{row.role.charAt(0)}</span>
              <span><strong>{row.name}</strong><small>{row.role} - Connected {formatDate(row.date)}</small></span>
              <ChevronRight size={16} />
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function ProfessionalDetailsModal({ professional, error, revoking, onClose, onRevoke }) {
  if (!professional) {
    return null;
  }

  const details = [
    ["Name", professional.name],
    ["Role", professional.role],
    ["Email", getProfessionalEmail(professional)],
    ["Primary Sport", professional.primary_sport],
    ["Specialization", getProfessionalSpecialization(professional)],
    ["Organization", professional.organization],
    ["Experience", professional.years_of_experience !== null && professional.years_of_experience !== undefined ? `${professional.years_of_experience} years` : null],
    ["Status", professional.status],
    ["Connected", formatDate(professional.accepted_at || professional.date)],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");

  return (
    <div className="athlete-modal-backdrop" role="presentation" onClick={onClose}>
      <section className="athlete-professional-modal" role="dialog" aria-modal="true" aria-label="Professional details" onClick={(event) => event.stopPropagation()}>
        <div className="athlete-card-header">
          <div>
            <p className="page-eyebrow">CONNECTED PROFESSIONAL</p>
            <h2>{professional.name}</h2>
            <p>{professional.role}</p>
          </div>
          <button className="secondary-button compact" type="button" onClick={onClose}>Close</button>
        </div>

        <div className="professional-detail-grid">
          {details.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>

        {professional.professional_bio && (
          <div className="professional-detail-bio">
            <span>Professional Bio</span>
            <p>{professional.professional_bio}</p>
          </div>
        )}

        {error && <div className="coach-connection-error">{error}</div>}

        <div className="professional-modal-actions">
          <button className="danger-lite professional-revoke-button" type="button" onClick={onRevoke} disabled={revoking}>
            {revoking ? "Revoking..." : "Revoke Access"}
          </button>
        </div>
      </section>
    </div>
  );
}

function RecentRequestsPreview({ coachRequests, physiotherapistRequests, sportsScientistRequests }) {
  const requests = [
    ...coachRequests.map((item) => ({ title: "Coach Request", name: item.coach_name || item.professional_name || "Coach", status: item.status, date: item.requested_at || item.created_at, id: item.relationship_id })),
    ...physiotherapistRequests.map((item) => ({ title: "Physiotherapist Request", name: item.professional_name || item.physiotherapist_name || "Physiotherapist", status: item.status, date: item.requested_at || item.created_at, id: item.relationship_id })),
    ...sportsScientistRequests.map((item) => ({ title: "Sports Scientist Request", name: item.professional_name || "Sports Scientist", status: item.status, date: item.requested_at || item.created_at, id: item.relationship_id })),
  ]
    .sort((a, b) => (parseDate(b.date)?.getTime() || 0) - (parseDate(a.date)?.getTime() || 0))
    .slice(0, 4);

  return (
    <section className="athlete-dashboard-card requests-preview-card">
      <div className="athlete-card-header"><div><h2>Recent Requests</h2><p>Incoming professional access requests.</p></div></div>
      {requests.length === 0 ? (
        <div className="activity-empty"><ShieldCheck size={18} />No pending professional requests.</div>
      ) : (
        <div className="request-preview-list">
          {requests.map((request) => (
            <div key={request.id}>
              <span><ShieldCheck size={17} /></span>
              <p><strong>{request.title}</strong><small>{request.name} - {formatDate(request.date)} - {request.status}</small></p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}


function buildRecentActivity({ videos, analyses, injuries }) {
  const events = [];

  videos.forEach((video) => {
    if (!video.uploaded_at) {
      return;
    }

    events.push({
      id: `video-${video.video_id}`,
      title: "Video uploaded",
      detail: video.activity || "Untitled Activity",
      date: video.uploaded_at,
      icon: Upload,
    });
  });

  analyses.forEach((analysis) => {
    const date = analysis.completed_at || analysis.analysis_date;

    if (!date) {
      return;
    }

    events.push({
      id: `analysis-${analysis.analysis_id}`,
      title: "Analysis completed",
      detail: analysis.video?.activity || "Movement analysis",
      date,
      icon: CheckCircle2,
    });
  });

  injuries.forEach((injury) => {
    const updatedAt = injury.updated_at || injury.created_at;

    if (!updatedAt) {
      return;
    }

    const wasUpdated =
      injury.created_at &&
      injury.updated_at &&
      new Date(injury.updated_at).getTime() !==
        new Date(injury.created_at).getTime();

    events.push({
      id: `injury-${injury.injury_id}-${updatedAt}`,
      title: wasUpdated ? "Injury record updated" : "Injury record added",
      detail: `${injury.injury_type || "Injury"} - ${injury.body_part || "Body part"}`,
      date: updatedAt,
      icon: HeartPulse,
    });
  });

  return events
    .sort((a, b) => {
      const dateA = parseDate(a.date)?.getTime() || 0;
      const dateB = parseDate(b.date)?.getTime() || 0;
      return dateB - dateA;
    });
}


function Dashboard() {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState({
    user: null,
    profile: null,
    videos: [],
    analyses: [],
    injuries: [],
    coachRequests: [],
    connectedCoaches: [],
    physiotherapistRequests: [],
    connectedPhysiotherapists: [],
    sportsScientistRequests: [],
    connectedSportsScientists: [],
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [selectedProfessional, setSelectedProfessional] = useState(null);
  const [professionalActionError, setProfessionalActionError] = useState("");
  const [revokingProfessional, setRevokingProfessional] = useState(false);

  const loadDashboard = useCallback(async ({ background = false } = {}) => {
    if (background) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const [
        user,
        profile,
        videos,
        analyses,
        coachRequests,
        connectedCoaches,
        physiotherapistRequests,
        connectedPhysiotherapists,
        sportsScientistRequests,
        connectedSportsScientists,
      ] = await Promise.all([
        getCurrentUser(),
        getAthleteProfile(),
        getMyVideos(),
        getAnalysisHistory(),
        getAthleteCoachRequests(),
        getAthleteConnectedCoaches(),
        getAthletePhysiotherapistRequests(),
        getAthleteConnectedPhysiotherapists(),
        getAthleteSportsScientistRequests(),
        getAthleteConnectedSportsScientists(),
      ]);

      const injuries = profile?.athlete_id
        ? await getInjuryHistory(profile.athlete_id)
        : [];
      let normalizedAnalyses = Array.isArray(analyses) ? analyses : [];

      const latestAnalysisSummary = [...normalizedAnalyses]
        .filter((analysis) => normalizeStatus(analysis.status) === "Completed")
        .sort((a, b) => {
          const dateA = parseDate(getAnalysisDate(a))?.getTime() || 0;
          const dateB = parseDate(getAnalysisDate(b))?.getTime() || 0;
          return dateB - dateA;
        })[0] || null;

      if (latestAnalysisSummary?.analysis_id) {
        try {
          const fullLatestAnalysis = await getAnalysisById(latestAnalysisSummary.analysis_id);
          normalizedAnalyses = normalizedAnalyses.map((analysis) =>
            analysis.analysis_id === latestAnalysisSummary.analysis_id
              ? {
                  ...analysis,
                  ...fullLatestAnalysis,
                  video: analysis.video || fullLatestAnalysis.video,
                }
              : analysis
          );
        } catch (error) {
          console.warn("Failed to load full latest analysis for dashboard metrics", error);
        }
      }

      setDashboardData({
        user,
        profile,
        videos: Array.isArray(videos) ? videos : [],
        analyses: normalizedAnalyses,
        injuries: Array.isArray(injuries) ? injuries : [],
        coachRequests: Array.isArray(coachRequests) ? coachRequests : [],
        connectedCoaches: Array.isArray(connectedCoaches) ? connectedCoaches : [],
        physiotherapistRequests: Array.isArray(physiotherapistRequests) ? physiotherapistRequests : [],
        connectedPhysiotherapists: Array.isArray(connectedPhysiotherapists) ? connectedPhysiotherapists : [],
        sportsScientistRequests: Array.isArray(sportsScientistRequests) ? sportsScientistRequests : [],
        connectedSportsScientists: Array.isArray(connectedSportsScientists) ? connectedSportsScientists : [],
      });
    } catch (error) {
      setError(error.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleSelectProfessional = useCallback((professional) => {
    setSelectedProfessional(professional);
    setProfessionalActionError("");
  }, []);

  const handleRevokeProfessional = useCallback(async () => {
    if (!selectedProfessional?.relationship_id) {
      return;
    }

    const confirmed = window.confirm(`Revoke ${selectedProfessional.name}'s access to your athlete data?`);
    if (!confirmed) {
      return;
    }

    setRevokingProfessional(true);
    setProfessionalActionError("");

    try {
      if (selectedProfessional.type === "coach") {
        await revokeCoachAccess(selectedProfessional.relationship_id);
      } else if (selectedProfessional.type === "physiotherapist") {
        await revokePhysiotherapistAccess(selectedProfessional.relationship_id);
      } else if (selectedProfessional.type === "sports-scientist") {
        await revokeSportsScientistAccess(selectedProfessional.relationship_id);
      }

      setSelectedProfessional(null);
      await loadDashboard({ background: true });
    } catch (error) {
      setProfessionalActionError(error.message || "Failed to revoke professional access.");
    } finally {
      setRevokingProfessional(false);
    }
  }, [loadDashboard, selectedProfessional]);

  useEffect(() => {
    loadDashboard();

    const refreshOnFocus = () => {
      if (document.visibilityState === "visible") {
        loadDashboard({ background: true });
      }
    };

    window.addEventListener("focus", refreshOnFocus);
    document.addEventListener("visibilitychange", refreshOnFocus);
    window.addEventListener("videos-updated", refreshOnFocus);
    window.addEventListener("analysis-history-updated", refreshOnFocus);
    window.addEventListener("coach-connections-updated", refreshOnFocus);
    window.addEventListener("professional-connections-updated", refreshOnFocus);
    const refreshInterval = window.setInterval(() => {
      loadDashboard({ background: true });
    }, 60000);

    return () => {
      window.removeEventListener("focus", refreshOnFocus);
      document.removeEventListener("visibilitychange", refreshOnFocus);
      window.removeEventListener("videos-updated", refreshOnFocus);
      window.removeEventListener("analysis-history-updated", refreshOnFocus);
      window.removeEventListener("coach-connections-updated", refreshOnFocus);
      window.removeEventListener("professional-connections-updated", refreshOnFocus);
      window.clearInterval(refreshInterval);
    };
  }, [loadDashboard]);

  const computed = useMemo(() => {
    const completedVideoIds = new Set(
      dashboardData.analyses
        .filter((analysis) => normalizeStatus(analysis.status) === "Completed")
        .map((analysis) => String(analysis.video_id))
    );

    const videosWithStatus = dashboardData.videos.map((video) => ({
      ...video,
      dashboardStatus: getVideoStatus(video, completedVideoIds),
    }));

    const latestVideo = [...videosWithStatus].sort((a, b) => {
      const dateA = parseDate(a.uploaded_at)?.getTime() || 0;
      const dateB = parseDate(b.uploaded_at)?.getTime() || 0;
      return dateB - dateA;
    })[0] || null;

    const analyzedCount = videosWithStatus.filter(
      (video) => video.dashboardStatus === "Completed"
    ).length;

    const pendingCount = videosWithStatus.filter(
      (video) => video.dashboardStatus === "Pending"
    ).length;
    const latestAnalysis = getLatestCompletedAnalysis(dashboardData.analyses);
    const videosThisWeek = dashboardData.videos.filter((video) =>
      isWithinLastDays(video.uploaded_at, 7)
    ).length;
    const analysesThisWeek = dashboardData.analyses.filter((analysis) =>
      normalizeStatus(analysis.status) === "Completed" &&
      isWithinLastDays(getAnalysisDate(analysis), 7)
    ).length;
    const injuriesThisWeek = dashboardData.injuries.filter((injury) =>
      isWithinLastDays(injury.created_at || injury.updated_at, 7)
    ).length;

    return {
      latestVideo,
      latestVideoStatus: latestVideo?.dashboardStatus || "Pending",
      latestAnalysis,
      stats: [
        {
          label: "Total Videos",
          value: dashboardData.videos.length,
          icon: Video,
          meta: videosThisWeek ? `${videosThisWeek} this week` : "-",
          tone: "primary",
        },
        {
          label: "Analyzed",
          value: analyzedCount,
          icon: CheckCircle2,
          meta: analysesThisWeek ? `${analysesThisWeek} this week` : "-",
          tone: "success",
        },
        {
          label: "Pending",
          value: pendingCount,
          icon: FileClock,
          meta: pendingCount ? "Awaiting analysis" : "-",
          tone: "warning",
        },
        {
          label: "Injuries",
          value: dashboardData.injuries.length,
          icon: HeartPulse,
          meta: injuriesThisWeek ? `${injuriesThisWeek} this week` : "-",
          tone: "danger",
        },
      ],
      activities: buildRecentActivity({
        videos: dashboardData.videos,
        analyses: dashboardData.analyses,
        injuries: dashboardData.injuries,
      }),
    };
  }, [dashboardData]);

  if (loading) {
    return (
      <DashboardLayout>
        <main className="athlete-dashboard">
          <div className="dashboard-skeleton header-skeleton" />
          <div className="athlete-stats-grid">
            {[0, 1, 2, 3].map((item) => (
              <div className="dashboard-skeleton stat-skeleton" key={item} />
            ))}
          </div>
          <div className="dashboard-content-grid">
            <div className="dashboard-skeleton panel-skeleton" />
            <div className="dashboard-skeleton panel-skeleton" />
          </div>
        </main>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <main className="athlete-dashboard">
          <section className="dashboard-error-state">
            <AlertCircle size={28} />
            <h1>Unable to load dashboard</h1>
            <p>{error}</p>
            <button
              className="athlete-action-button"
              onClick={() => loadDashboard()}
              type="button"
            >
              Try Again
            </button>
          </section>
        </main>
      </DashboardLayout>
    );
  }

  const athleteName =
    dashboardData.user?.name ||
    dashboardData.profile?.sport ||
    "Athlete";

  return (
    <DashboardLayout>
      <main className="athlete-dashboard">
        <section className="athlete-dashboard-header">
          <div>
            <p className="page-eyebrow">ATHLETE DASHBOARD</p>
            <h1>{getGreeting(athleteName)}</h1>
            <p>Monitor your sports activity and injury analysis.</p>
          </div>
          {refreshing && <span className="dashboard-refreshing">Updating...</span>}
        </section>

        <section className="athlete-stats-grid">
          {computed.stats.map((stat) => (
            <StatCard key={stat.label} stat={stat} />
          ))}
        </section>

        <div className="athlete-main-grid">
          <RecentAnalysisOverview
            analysis={computed.latestAnalysis}
            latestVideo={computed.latestVideo}
          />
          <QuickActionPanel onNavigate={navigate} />
          <PerformanceTrends analyses={dashboardData.analyses} />
          <RecentActivity
            activities={computed.activities}
            formatDateTime={formatDateTime}
            onShowMore={() => navigate("/analysis-history")}
          />
        </div>

        <div className="athlete-bottom-grid">
          <ProfessionalsPreview
            coaches={dashboardData.connectedCoaches}
            physiotherapists={dashboardData.connectedPhysiotherapists}
            scientists={dashboardData.connectedSportsScientists}
            onSelect={handleSelectProfessional}
          />
          <RecentRequestsPreview
            coachRequests={dashboardData.coachRequests}
            physiotherapistRequests={dashboardData.physiotherapistRequests}
            sportsScientistRequests={dashboardData.sportsScientistRequests}
          />
        </div>

        <ProfessionalDetailsModal
          professional={selectedProfessional}
          error={professionalActionError}
          revoking={revokingProfessional}
          onClose={() => setSelectedProfessional(null)}
          onRevoke={handleRevokeProfessional}
        />
      </main>
    </DashboardLayout>
  );
}

export default Dashboard;
