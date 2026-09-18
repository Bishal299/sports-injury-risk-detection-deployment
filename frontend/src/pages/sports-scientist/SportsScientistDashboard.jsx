import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  FileText,
  GitCompare,
  LineChart,
  Microscope,
  TrendingUp,
  UsersRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getSportsScientistDashboard } from "../../services/api";
import "../../styles/coach.css";


function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "No data";
  }
  const numeric = Number(value);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}

function riskClass(value) {
  return String(value || "not-available").toLowerCase().replace(/\s+/g, "-");
}


function SportsScientistDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const data = await getSportsScientistDashboard();
        if (!cancelled) setDashboard(data);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load Sports Scientist dashboard.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = [
    { label: "Athletes Monitored", value: dashboard?.stats?.athletes_monitored ?? 0, icon: UsersRound },
    { label: "Analyses Completed", value: dashboard?.stats?.analyses_completed ?? 0, icon: BarChart3 },
    { label: "High/Critical Risk", value: dashboard?.stats?.high_critical_risk ?? 0, icon: AlertTriangle },
    { label: "Sports Covered", value: dashboard?.stats?.sports_covered ?? 0, icon: Activity },
  ];
  const riskDistribution = Array.isArray(dashboard?.risk_distribution) ? dashboard.risk_distribution : [];
  const metrics = Array.isArray(dashboard?.biomechanical_overview) ? dashboard.biomechanical_overview : [];
  const trend = Array.isArray(dashboard?.performance_trend) ? dashboard.performance_trend : [];
  const findings = Array.isArray(dashboard?.findings) ? dashboard.findings : [];
  const recentAnalyses = Array.isArray(dashboard?.recent_analyses) ? dashboard.recent_analyses : [];
  const visibleFindings = findings.slice(0, 5);
  const visibleRecentAnalyses = recentAnalyses.slice(0, 5);

  const maxTrend = Math.max(...trend.map((point) => Number(point.value) || 0), 1);
  const quickNav = [
    { title: "Biomechanical Analytics", path: "/sports-scientist/biomechanical-analytics", icon: Microscope },
    { title: "Team Performance", path: "/sports-scientist/team-performance", icon: LineChart },
    { title: "Injury Prediction Insights", path: "/sports-scientist/injury-insights", icon: TrendingUp },
    { title: "Athlete Comparison", path: "/sports-scientist/athlete-comparison", icon: GitCompare },
    { title: "Research Reports", path: "/sports-scientist/research-reports", icon: FileText },
  ];

  return (
    <main className="coach-page">
      <section className="coach-page-header">
        <p className="page-eyebrow">SPORTS SCIENTIST</p>
        <h1>Sports Scientist Dashboard</h1>
        <p>Monitor biomechanics, performance trends, and injury-risk insights across your athletes.</p>
      </section>

      {loading && <section className="coach-empty-card">Loading Sports Scientist dashboard...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && (
        <>
          <section className="coach-stats-grid">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <article className="coach-stat-card" key={stat.label}>
                  <div className="coach-icon-box"><Icon size={21} /></div>
                  <div><span>{stat.label}</span><strong>{stat.value}</strong></div>
                </article>
              );
            })}
          </section>

          <section className="coach-dashboard-grid">
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div><h2>Risk Distribution</h2><p>Current risk bands from latest accessible analyses.</p></div>
              </div>
              {riskDistribution.every((item) => item.count === 0) ? (
                <div className="coach-quiet-state">No risk distribution data available.</div>
              ) : (
                <div className="scientist-bar-list">
                  {riskDistribution.map((item) => (
                    <div className="scientist-bar-row" key={item.category}>
                      <span>{item.category}</span>
                      <div className="scientist-bar-track">
                        <div className={`scientist-bar-fill ${riskClass(item.category)}`} style={{ width: `${item.percentage}%` }} />
                      </div>
                      <strong>{item.count} · {item.percentage}%</strong>
                    </div>
                  ))}
                </div>
              )}
            </article>

            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div><h2>Performance Trend Preview</h2><p>Movement Quality over time from completed analyses.</p></div>
              </div>
              {trend.length === 0 ? (
                <div className="coach-quiet-state">No trend data available.</div>
              ) : (
                <div className="scientist-trend-chart" aria-label="Movement quality trend">
                  {trend.map((point) => (
                    <div className="scientist-trend-point" key={`${point.date}-${point.value}`}>
                      <div style={{ height: `${Math.max(8, (Number(point.value) / maxTrend) * 100)}%` }} />
                      <span>{formatDate(point.date)}</span>
                    </div>
                  ))}
                </div>
              )}
            </article>
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div><h2>Biomechanical Overview</h2><p>Aggregate values from existing completed analysis metrics.</p></div>
            </div>
            {metrics.every((metric) => metric.count === 0) ? (
              <div className="coach-quiet-state">No biomechanical metrics available.</div>
            ) : (
              <div className="coach-performance-grid scientist-metric-grid">
                {metrics.map((metric) => (
                  <div className="coach-metric-card" key={metric.key}>
                    <span>{metric.label}</span>
                    <strong>{formatValue(metric.average)}</strong>
                    <small>{metric.count ? `${metric.count} analysis value${metric.count === 1 ? "" : "s"}` : "No data available"}</small>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="coach-dashboard-grid">
            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div><h2>Top/Recent Biomechanical Findings</h2><p>Observed patterns from stored risk-factor outputs.</p></div>
              </div>
              {findings.length === 0 ? (
                <div className="coach-quiet-state">No biomechanical findings available.</div>
              ) : (
                <div className="coach-alert-list">
                  {visibleFindings.map((finding) => (
                    <div className="coach-alert-row" key={finding.label}>
                      <span className="coach-risk-dot moderate" />
                      <div>
                        <strong>{finding.label}</strong>
                        <p>{finding.finding_type} · {finding.count} occurrence{finding.count === 1 ? "" : "s"}</p>
                      </div>
                    </div>
                  ))}
                  {findings.length > visibleFindings.length && (
                    <button className="secondary-button compact" type="button" onClick={() => navigate("/sports-scientist/biomechanical-analytics")}>
                      Show More
                    </button>
                  )}
                </div>
              )}
            </article>

            <article className="coach-panel-card">
              <div className="coach-section-heading">
                <div><h2>Quick Navigation</h2><p>Research and analytics modules for the next steps.</p></div>
              </div>
              <div className="scientist-quick-grid">
                {quickNav.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button className="secondary-button scientist-quick-button" key={item.path} type="button" onClick={() => navigate(item.path)}>
                      <Icon size={17} />
                      <span>{item.title}</span>
                    </button>
                  );
                })}
              </div>
            </article>
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div><h2>Recent Analyses</h2><p>Completed analyses available through active Sports Scientist relationships.</p></div>
            </div>
            {recentAnalyses.length === 0 ? (
              <div className="coach-quiet-state">No completed analyses available.</div>
            ) : (
              <div className="coach-table-card">
                <div className="coach-athlete-table coach-athlete-table-head">
                  <span>Athlete</span><span>Sport</span><span>Analysis Date</span><span>Risk</span><span>Movement Quality</span><span>Status</span>
                </div>
                {visibleRecentAnalyses.map((analysis) => (
                  <article className="coach-athlete-table" key={analysis.analysis_id}>
                    <div className="coach-athlete-cell athlete">
                      <div className="coach-icon-box"><BarChart3 size={18} /></div>
                      <div><strong>{analysis.athlete_name}</strong></div>
                    </div>
                    <span className="coach-muted-cell">{analysis.sport || "Sport not set"}</span>
                    <span className="coach-muted-cell">{formatDate(analysis.analysis_date)}</span>
                    <span className={`coach-risk-text ${riskClass(analysis.risk_category)}`}>{analysis.risk_category}</span>
                    <span className="coach-muted-cell">{formatValue(analysis.movement_quality)}</span>
                    <span className="coach-connected-badge active">{analysis.status}</span>
                  </article>
                ))}
                {recentAnalyses.length > visibleRecentAnalyses.length && (
                  <div className="coach-table-footer">
                    <button className="secondary-button compact" type="button" onClick={() => navigate("/sports-scientist/biomechanical-analytics")}>
                      Show More
                    </button>
                  </div>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}


export default SportsScientistDashboard;
