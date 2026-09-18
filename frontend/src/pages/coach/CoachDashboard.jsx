import React, { useEffect, useState, useMemo } from "react";
import {
  AlertTriangle,
  BarChart3,
  Search,
  UsersRound,
  Video,
  ArrowRight,
  CheckCircle2,
  Clock,
  Activity,
  Calendar,
  Check,
  X,
  TrendingUp,
  Layers,
  ListTodo,
  ExternalLink,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  getCoachDashboard,
  getCurrentUser,
  coachAcceptAthleteRequest,
  coachRejectAthleteRequest,
} from "../../services/api";
import "../../styles/coach.css";

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

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function formatChartDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

function CoachDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState("all");
  const [hoveredPoint, setHoveredPoint] = useState(null);

  async function loadDashboardData() {
    try {
      const [currentUser, dashboardData] = await Promise.all([
        getCurrentUser(),
        getCoachDashboard(),
      ]);
      setUser(currentUser);
      setDashboard(dashboardData);
    } catch (err) {
      setError(err.message || "Failed to load Coach dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function handleAcceptRequest(relationshipId, athleteName) {
    try {
      setActionLoadingId(relationshipId);
      await coachAcceptAthleteRequest(relationshipId);
      setFeedback({
        type: "success",
        message: `Successfully connected with ${athleteName || "athlete"}.`,
      });
      await loadDashboardData();
    } catch (err) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to accept connection request.",
      });
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleRejectRequest(relationshipId, athleteName) {
    try {
      setActionLoadingId(relationshipId);
      await coachRejectAthleteRequest(relationshipId);
      setFeedback({
        type: "info",
        message: `Declined request from ${athleteName || "athlete"}.`,
      });
      await loadDashboardData();
    } catch (err) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to decline request.",
      });
    } finally {
      setActionLoadingId(null);
    }
  }


  const stats = [
    {
      label: "Total Athletes",
      value: dashboard?.stats?.total_athletes ?? 0,
      icon: UsersRound,
    },
    {
      label: "Analyses",
      value: dashboard?.stats?.analyses ?? 0,
      icon: BarChart3,
    },
    {
      label: "Videos",
      value: dashboard?.stats?.videos ?? 0,
      icon: Video,
    },
    {
      label: "High Risk",
      value: dashboard?.stats?.high_risk ?? 0,
      icon: AlertTriangle,
    },
  ];

  const attention = Array.isArray(dashboard?.attention) ? dashboard.attention : [];
  const athletes = Array.isArray(dashboard?.athletes) ? dashboard.athletes : [];
  const recentAnalyses = Array.isArray(dashboard?.recent_analyses) ? dashboard.recent_analyses : [];
  const performanceTrends = Array.isArray(dashboard?.performance_trends) ? dashboard.performance_trends : [];
  const requestsSummary = dashboard?.requests_summary;
  const recentRequests = Array.isArray(requestsSummary?.recent_requests) ? requestsSummary.recent_requests : [];
  const tasksSummary = dashboard?.tasks_summary;

  // Chart calculations
  const chartWidth = 720;
  const chartHeight = 240;
  const pad = { left: 44, right: 28, top: 22, bottom: 38 };
  const plotWidth = chartWidth - pad.left - pad.right;
  const plotHeight = chartHeight - pad.top - pad.bottom;

  const metricConfigs = [
    {
      key: "movement_quality",
      label: "Movement Quality",
      color: "#10b981",
      unit: "/100",
    },
    {
      key: "biomechanical_score",
      label: "Biomechanical Efficiency",
      color: "#38bdf8",
      unit: "/100",
    },
    {
      key: "overall_risk_score",
      label: "Risk Score",
      color: "#f59e0b",
      unit: "/100",
    },
  ];

  const activeSeries = useMemo(() => {
    if (selectedMetric === "all") {
      return metricConfigs;
    }
    return metricConfigs.filter((m) => m.key === selectedMetric);
  }, [selectedMetric]);

  const validTrendPoints = useMemo(() => {
    return performanceTrends.filter((item) => item.date != null);
  }, [performanceTrends]);

  function getPointCoordinates(definition, item, index) {
    const rawVal = item[definition.key];
    const value = rawVal === null || rawVal === undefined || Number.isNaN(Number(rawVal))
      ? null
      : Number(rawVal);

    const x =
      validTrendPoints.length > 1
        ? pad.left + (index / (validTrendPoints.length - 1)) * plotWidth
        : pad.left + plotWidth / 2;

    const y =
      value === null
        ? null
        : pad.top + plotHeight - (Math.max(0, Math.min(100, value)) / 100) * plotHeight;

    return { x, y, value };
  }

  function generatePath(definition) {
    const coords = validTrendPoints
      .map((item, index) => getPointCoordinates(definition, item, index))
      .filter((pt) => pt.y !== null);

    if (coords.length === 0) return "";
    return coords.map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(" ");
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header">
        <p className="page-eyebrow">COACH COMMAND CENTER</p>
        <h1>{getGreeting(user?.name || "Coach")}</h1>
        <p>Monitor athlete readiness, biomechanical trajectories, and actionable requests.</p>
      </section>

      {feedback && (
        <div className={`coach-feedback-toast ${feedback.type}`}>
          <span>{feedback.message}</span>
          <button
            type="button"
            className="coach-toast-close"
            onClick={() => setFeedback(null)}
            aria-label="Dismiss message"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {loading && <div className="coach-empty-card">Loading Coach environment...</div>}
      {error && <div className="coach-error-card">{error}</div>}

      {!loading && !error && (
        <>
          {/* Top 4 Summary Cards */}
          <section className="coach-stats-grid">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <article className="coach-stat-card" key={stat.label}>
                  <div className="coach-icon-box">
                    <Icon size={21} />
                  </div>
                  <div>
                    <span>{stat.label}</span>
                    <strong>{stat.value}</strong>
                  </div>
                </article>
              );
            })}
          </section>

          {/* Row 1: Attention Required & My Athletes */}
          <section className="coach-dashboard-grid">
            {/* Attention Required Panel */}
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Attention Required</h2>
                  <p>Actionable alerts and current athlete signals.</p>
                </div>
              </div>

              {attention.length === 0 ? (
                <div className="coach-quiet-state">
                  <CheckCircle2 size={24} className="coach-quiet-icon" />
                  <div>
                    <strong>All athletes in good standing</strong>
                    <p>No high-priority alerts or unhandled connection requests right now.</p>
                  </div>
                </div>
              ) : (
                <div className="coach-alert-list">
                  {attention.slice(0, 4).map((alert, idx) => {
                    const isRequest = alert.type === "connection_request";
                    return (
                      <div
                        className="coach-alert-row"
                        key={`${alert.type}-${alert.athlete_id || idx}-${alert.created_at || idx}`}
                        onClick={() => {
                          if (isRequest) navigate("/coach/requests");
                          else if (alert.athlete_id) navigate(`/coach/athletes/${alert.athlete_id}`);
                        }}
                        role="button"
                        tabIndex={0}
                        style={{ cursor: "pointer" }}
                      >
                        <span
                          className={`coach-risk-dot ${
                            isRequest ? "pending" : alert.severity?.toLowerCase() || "moderate"
                          }`}
                        />
                        <div className="coach-alert-content">
                          <div className="coach-alert-title-row">
                            <strong>{alert.title}</strong>
                            {alert.athlete_name && (
                              <span className="coach-alert-athlete-tag">{alert.athlete_name}</span>
                            )}
                          </div>
                          <p>{alert.detail}</p>
                        </div>
                        <ArrowRight size={15} className="coach-alert-arrow" />
                      </div>
                    );
                  })}
                  {attention.length > 4 && (
                    <button
                      className="secondary-button compact coach-more-btn"
                      type="button"
                      onClick={() => navigate("/coach/athletes")}
                    >
                      Show More Alerts ({attention.length - 4} more) →
                    </button>
                  )}
                </div>
              )}
            </article>

            {/* My Athletes Compact Panel (2-3 items) */}
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>My Athletes</h2>
                  <p>Recently active connected roster.</p>
                </div>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => navigate("/coach/athletes")}
                >
                  View All ({dashboard?.stats?.total_athletes ?? athletes.length})
                </button>
              </div>

              {athletes.length === 0 ? (
                <div className="coach-empty-inline">
                  <p>No athletes connected to your roster yet.</p>
                  <button
                    className="primary-button"
                    type="button"
                    onClick={() => navigate("/coach/discover-athletes")}
                  >
                    <Search size={17} />
                    Discover Athletes
                  </button>
                </div>
              ) : (
                <div className="coach-mini-athlete-list">
                  {athletes.slice(0, 3).map((athlete) => (
                    <div
                      className="coach-mini-athlete"
                      key={athlete.athlete_id}
                      onClick={() => navigate(`/coach/athletes/${athlete.athlete_id}`)}
                      role="button"
                      tabIndex={0}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="coach-athlete-summary-text">
                        <strong>{athlete.name}</strong>
                        <span>
                          {athlete.sport || "Sport not set"}
                          {athlete.position ? ` · ${athlete.position}` : ""}
                        </span>
                      </div>
                      <span
                        className={`coach-risk-badge ${
                          athlete.risk_category?.toLowerCase().replace(/\s+/g, "-") || "low"
                        }`}
                      >
                        {athlete.risk_category === "Not Available"
                          ? "N/A"
                          : athlete.risk_category || "Low Risk"}
                      </span>
                    </div>
                  ))}
                  <div className="coach-section-footer-action">
                    <button
                      className="coach-subtle-link"
                      type="button"
                      onClick={() => navigate("/coach/athletes")}
                    >
                      <span>Manage Athlete Roster</span>
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </article>
          </section>

          {/* Row 2: Performance Trends (Full Width) */}
          <section className="coach-panel-card coach-trends-panel">
            <div className="coach-section-heading coach-trends-heading">
              <div>
                <h2>Performance Trends</h2>
                <p>Biomechanical trajectory and movement metrics over time across connected athletes.</p>
              </div>
              <div className="coach-metric-selector">
                <button
                  type="button"
                  className={`coach-metric-tab ${selectedMetric === "all" ? "active" : ""}`}
                  onClick={() => setSelectedMetric("all")}
                >
                  All Metrics
                </button>
                {metricConfigs.map((m) => (
                  <button
                    key={m.key}
                    type="button"
                    className={`coach-metric-tab ${selectedMetric === m.key ? "active" : ""}`}
                    onClick={() => setSelectedMetric(m.key)}
                  >
                    <span className="coach-metric-indicator" style={{ backgroundColor: m.color }} />
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {validTrendPoints.length === 0 ? (
              <div className="coach-chart-empty">
                <TrendingUp size={36} className="coach-chart-empty-icon" />
                <h3>No Trend Data Yet</h3>
                <p>
                  Completed athlete movement analyses will automatically chart biomechanical scores,
                  movement quality, and risk trajectories here.
                </p>
              </div>
            ) : (
              <div className="coach-chart-container">
                <div className="coach-svg-wrapper">
                  <svg
                    className="coach-trend-svg"
                    viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                    preserveAspectRatio="xMidYMid meet"
                    role="img"
                    aria-label="Coach performance trends chart"
                  >
                    {/* Gridlines and Y-axis Ticks */}
                    {[0, 25, 50, 75, 100].map((tick) => {
                      const y = pad.top + plotHeight - (tick / 100) * plotHeight;
                      return (
                        <g key={tick} className="coach-chart-grid-group">
                          <line
                            x1={pad.left}
                            x2={pad.left + plotWidth}
                            y1={y}
                            y2={y}
                            className="coach-chart-gridline"
                          />
                          <text x={pad.left - 10} y={y + 4} className="coach-chart-tick-text">
                            {tick}
                          </text>
                        </g>
                      );
                    })}

                    {/* Chart lines */}
                    {activeSeries.map((series) => {
                      const path = generatePath(series);
                      if (!path) return null;
                      return (
                        <g key={series.key} className="coach-chart-series-group">
                          <path
                            d={path}
                            className="coach-chart-line"
                            style={{ stroke: series.color }}
                            fill="none"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          {validTrendPoints.map((item, idx) => {
                            const pt = getPointCoordinates(series, item, idx);
                            if (pt.y === null) return null;
                            const isHovered =
                              hoveredPoint &&
                              hoveredPoint.index === idx &&
                              (hoveredPoint.seriesKey === series.key || selectedMetric === "all");

                            return (
                              <g key={`${series.key}-${idx}`}>
                                <circle
                                  cx={pt.x}
                                  cy={pt.y}
                                  r={isHovered ? 6 : 4}
                                  className="coach-chart-point"
                                  style={{
                                    fill: series.color,
                                    stroke: "var(--bg-secondary)",
                                    strokeWidth: isHovered ? 3 : 2,
                                  }}
                                  onMouseEnter={() =>
                                    setHoveredPoint({
                                      index: idx,
                                      seriesKey: series.key,
                                      item,
                                      x: pt.x,
                                      y: pt.y,
                                    })
                                  }
                                  onMouseLeave={() => setHoveredPoint(null)}
                                />
                              </g>
                            );
                          })}
                        </g>
                      );
                    })}

                    {/* X-axis labels */}
                    {validTrendPoints.map((item, idx) => {
                      // Only show up to 6 labels to avoid clutter
                      const step = Math.max(1, Math.floor(validTrendPoints.length / 6));
                      if (idx % step !== 0 && idx !== validTrendPoints.length - 1) return null;

                      const x =
                        validTrendPoints.length > 1
                          ? pad.left + (idx / (validTrendPoints.length - 1)) * plotWidth
                          : pad.left + plotWidth / 2;

                      return (
                        <text
                          key={idx}
                          x={x}
                          y={chartHeight - 12}
                          className="coach-chart-x-text"
                          textAnchor="middle"
                        >
                          {formatChartDate(item.date)}
                        </text>
                      );
                    })}
                  </svg>

                  {/* Tooltip Overlay */}
                  {hoveredPoint && (
                    <div
                      className="coach-chart-tooltip"
                      style={{
                        left: `${(hoveredPoint.x / chartWidth) * 100}%`,
                        top: `${(hoveredPoint.y / chartHeight) * 100}%`,
                      }}
                    >
                      <div className="coach-tooltip-header">
                        <strong>{hoveredPoint.item.athlete_name || "Athlete"}</strong>
                        <span>{formatDate(hoveredPoint.item.date)}</span>
                      </div>
                      <div className="coach-tooltip-activity">
                        {hoveredPoint.item.activity || "Movement Drill"}
                      </div>
                      <div className="coach-tooltip-metrics">
                        <div>
                          <span style={{ color: "#10b981" }}>MQ:</span>{" "}
                          <strong>{hoveredPoint.item.movement_quality ?? "—"}</strong>
                        </div>
                        <div>
                          <span style={{ color: "#38bdf8" }}>Bio:</span>{" "}
                          <strong>{hoveredPoint.item.biomechanical_score ?? "—"}</strong>
                        </div>
                        <div>
                          <span style={{ color: "#f59e0b" }}>Risk:</span>{" "}
                          <strong>{hoveredPoint.item.overall_risk_score ?? "—"}</strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Legend */}
                <div className="coach-chart-legend">
                  {activeSeries.map((series) => (
                    <span key={series.key} className="coach-legend-item">
                      <i style={{ backgroundColor: series.color }} />
                      {series.label}
                    </span>
                  ))}
                  <span className="coach-legend-note">
                    Showing latest {validTrendPoints.length} completed session
                    {validTrendPoints.length === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            )}
          </section>

          {/* Row 3: Recent Analyses & Athlete Requests */}
          <section className="coach-dashboard-grid">
            {/* Recent Analyses (Max 3) */}
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Recent Analyses</h2>
                  <p>Latest movement tests completed by your athletes.</p>
                </div>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => navigate("/coach/analyses")}
                >
                  Show More →
                </button>
              </div>

              {recentAnalyses.length === 0 ? (
                <div className="coach-quiet-state">
                  <Activity size={24} className="coach-quiet-icon" />
                  <div>
                    <strong>No completed analyses yet</strong>
                    <p>New movement analyses will appear here as athletes record sessions.</p>
                  </div>
                </div>
              ) : (
                <div className="coach-recent-analyses-list">
                  {recentAnalyses.slice(0, 3).map((analysis) => {
                    const riskBand = analysis.risk_category || "Low Risk";
                    const riskClass = riskBand.toLowerCase().replace(/\s+/g, "-");

                    return (
                      <div className="coach-analysis-card" key={analysis.analysis_id}>
                        <div className="coach-analysis-card-top">
                          <div>
                            <strong>{analysis.athlete_name}</strong>
                            <p className="coach-analysis-activity">
                              {analysis.activity || "Movement Assessment"}
                            </p>
                          </div>
                          <span className={`coach-risk-badge ${riskClass}`}>
                            {riskBand}
                          </span>
                        </div>

                        <div className="coach-analysis-card-bottom">
                          <div className="coach-analysis-metrics-summary">
                            <span>
                              <Calendar size={13} />
                              {formatDate(analysis.date)}
                            </span>
                            {analysis.movement_quality != null && (
                              <span className="coach-score-chip">
                                Quality: <strong>{analysis.movement_quality}</strong>
                              </span>
                            )}
                          </div>
                          <button
                            className="secondary-button compact coach-action-btn"
                            type="button"
                            onClick={() => {
                              if (analysis.video_id) {
                                navigate(
                                  `/coach/athletes/${analysis.athlete_id}/analysis/${analysis.video_id}`
                                );
                              } else {
                                navigate(`/coach/athletes/${analysis.athlete_id}`);
                              }
                            }}
                          >
                            <span>View Analysis</span>
                            <ExternalLink size={13} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                  {dashboard?.total_recent_analyses > 3 && (
                    <div className="coach-section-footer-action">
                      <button
                        className="coach-subtle-link"
                        type="button"
                        onClick={() => navigate("/coach/analyses")}
                      >
                        <span>View all {dashboard.total_recent_analyses} analyses</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </article>

            {/* Athlete Requests (Max 2) */}
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Athlete Requests</h2>
                  <p>Incoming and outgoing connection requests.</p>
                </div>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => navigate("/coach/requests")}
                >
                  Show More →
                </button>
              </div>

              {recentRequests.length === 0 ? (
                <div className="coach-quiet-state">
                  <UsersRound size={24} className="coach-quiet-icon" />
                  <div>
                    <strong>No requests pending</strong>
                    <p>Athlete connection requests and sent invitations will show here.</p>
                  </div>
                </div>
              ) : (
                <div className="coach-requests-list">
                  {recentRequests.slice(0, 2).map((req) => {
                    const isReceived = req.direction === "RECEIVED";
                    const isPending = req.status === "PENDING";
                    const isActioning = actionLoadingId === req.relationship_id;

                    return (
                      <div className="coach-request-card" key={req.relationship_id}>
                        <div className="coach-request-header">
                          <div>
                            <strong>{req.athlete_name}</strong>
                            <p className="coach-request-sport">
                              {req.athlete_sport || "Sport not specified"}
                            </p>
                          </div>
                          <div className="coach-request-badges">
                            <span
                              className={`coach-direction-badge ${
                                isReceived ? "received" : "sent"
                              }`}
                            >
                              {isReceived ? "Received" : "Sent"}
                            </span>
                            <span
                              className={`coach-connected-badge ${req.status.toLowerCase()}`}
                            >
                              {req.status}
                            </span>
                          </div>
                        </div>

                        <div className="coach-request-footer">
                          <span className="coach-request-date">
                            <Clock size={12} />
                            {formatDate(req.date)}
                          </span>

                          {/* Inline actions for received pending requests */}
                          {isReceived && isPending && (
                            <div className="coach-request-actions">
                              <button
                                className="coach-action-btn-accept"
                                type="button"
                                disabled={isActioning}
                                onClick={() =>
                                  handleAcceptRequest(req.relationship_id, req.athlete_name)
                                }
                              >
                                <Check size={14} />
                                <span>{isActioning ? "..." : "Accept"}</span>
                              </button>
                              <button
                                className="coach-action-btn-reject"
                                type="button"
                                disabled={isActioning}
                                onClick={() =>
                                  handleRejectRequest(req.relationship_id, req.athlete_name)
                                }
                              >
                                <X size={14} />
                                <span>{isActioning ? "..." : "Decline"}</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {requestsSummary?.total_requests > 2 && (
                    <div className="coach-section-footer-action">
                      <button
                        className="coach-subtle-link"
                        type="button"
                        onClick={() => navigate("/coach/requests")}
                      >
                        <span>View all {requestsSummary.total_requests} requests</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </article>
          </section>

          {/* Row 4: Athlete Work / Directives (Conditionally Shown if Tasks Exist) */}
          {tasksSummary && tasksSummary.total > 0 && (
            <section className="coach-panel-card coach-tasks-panel">
              <div className="coach-section-heading">
                <div>
                  <h2>Athlete Work & Directives</h2>
                  <p>Assigned training drills and rehabilitation tasks across your connected athletes.</p>
                </div>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => navigate("/coach/athletes")}
                >
                  View All Work →
                </button>
              </div>

              <div className="coach-tasks-overview">
                <div className="coach-task-chips">
                  <div className="coach-task-chip">
                    <span>Total Tasks</span>
                    <strong>{tasksSummary.total}</strong>
                  </div>
                  <div className="coach-task-chip assigned">
                    <span>Assigned</span>
                    <strong>{tasksSummary.assigned}</strong>
                  </div>
                  <div className="coach-task-chip in-progress">
                    <span>In Progress</span>
                    <strong>{tasksSummary.in_progress}</strong>
                  </div>
                  <div className="coach-task-chip completed">
                    <span>Completed</span>
                    <strong>{tasksSummary.completed}</strong>
                  </div>
                </div>

                {tasksSummary.recent_tasks && tasksSummary.recent_tasks.length > 0 && (
                  <div className="coach-task-recent-list">
                    {tasksSummary.recent_tasks.map((task) => (
                      <div className="coach-task-row" key={task.task_id}>
                        <div className="coach-task-info">
                          <ListTodo size={17} className="coach-task-icon" />
                          <div>
                            <strong>{task.title}</strong>
                            <p>
                              Athlete: <span>{task.athlete_name}</span>
                              {task.due_date ? ` · Due ${formatDate(task.due_date)}` : ""}
                            </p>
                          </div>
                        </div>
                        <div className="coach-task-meta">
                          <span
                            className={`coach-task-priority ${task.priority?.toLowerCase() || "medium"}`}
                          >
                            {task.priority || "Medium"}
                          </span>
                          <span
                            className={`coach-task-status ${task.status?.toLowerCase().replace(/\s+/g, "-")}`}
                          >
                            {task.status?.replace("_", " ")}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}

export default CoachDashboard;
