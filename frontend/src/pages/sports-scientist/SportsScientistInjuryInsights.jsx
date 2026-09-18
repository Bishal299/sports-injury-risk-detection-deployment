import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BarChart3, ShieldCheck, TrendingUp } from "lucide-react";

import { getSportsScientistInjuryInsights } from "../../services/api";
import "../../styles/coach.css";


const riskOptions = ["", "LOW", "MODERATE", "HIGH", "CRITICAL"];
const factorOptions = [
  { value: "", label: "All Injury Factors" },
  { value: "knee_valgus", label: "Knee/Valgus" },
  { value: "hip", label: "Hip" },
  { value: "trunk", label: "Trunk" },
  { value: "landing", label: "Landing" },
  { value: "balance", label: "Balance" },
  { value: "alignment", label: "Alignment" },
  { value: "posture", label: "Posture" },
  { value: "movement_asymmetry", label: "Movement Asymmetry" },
  { value: "previous_injury_history", label: "Previous Injury History" },
  { value: "training_load", label: "Training Load" },
];


function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatValue(value, fallback = "No data") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return fallback;
  }
  const numeric = Number(value);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}

function riskClass(value) {
  return String(value || "not-available").toLowerCase().replace(/\s+/g, "-");
}

function compactFactors(values) {
  return Array.isArray(values) && values.length ? values.join(", ") : "No stored factors";
}


function SportsScientistInjuryInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    sport: "",
    athlete_id: "",
    start_date: "",
    end_date: "",
    risk_level: "",
    injury_factor: "",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadInsights() {
      setLoading(true);
      setError("");
      try {
        const response = await getSportsScientistInjuryInsights(filters);
        if (!cancelled) setData(response);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load injury-risk insights.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadInsights();
    return () => {
      cancelled = true;
    };
  }, [filters]);

  const athletes = Array.isArray(data?.athletes) ? data.athletes : [];
  const sports = Array.isArray(data?.sports) ? data.sports : [];
  const distribution = Array.isArray(data?.risk_distribution) ? data.risk_distribution : [];
  const riskTrend = Array.isArray(data?.risk_trend) ? data.risk_trend : [];
  const sportAverages = Array.isArray(data?.average_risk_by_sport) ? data.average_risk_by_sport : [];
  const factorAnalysis = Array.isArray(data?.factor_analysis) ? data.factor_analysis : [];
  const athleteRows = Array.isArray(data?.athlete_table) ? data.athlete_table : [];
  const observedPatterns = Array.isArray(data?.observed_patterns) ? data.observed_patterns : [];
  const summary = data?.summary || {};
  const maxTrend = Math.max(...riskTrend.map((point) => Number(point.average_risk_score) || 0), 1);

  const summaryCards = useMemo(() => ([
    { label: "Athletes Analyzed", value: summary.athletes_analyzed ?? 0, icon: ShieldCheck },
    { label: "High/Critical Risk Analyses", value: summary.high_critical_risk_analyses ?? 0, icon: AlertTriangle },
    { label: "Average Risk Score", value: formatValue(summary.average_risk_score), icon: BarChart3 },
    { label: "Previous-Injury Cases", value: summary.previous_injury_cases ?? 0, icon: ShieldCheck },
    { label: "Most Frequent Risk Factor", value: summary.most_frequent_risk_factor || "No data", icon: TrendingUp },
  ]), [summary]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">SPORTS SCIENTIST</p>
          <h1>Injury Prediction Insights</h1>
          <p>Analytics view of stored injury-risk factors and observed biomechanical patterns across authorized athletes.</p>
        </div>
        <BarChart3 size={28} />
      </section>

      <section className="coach-filter-card scientist-filter-card injury-insights-filter-card">
        <select value={filters.sport} onChange={(event) => updateFilter("sport", event.target.value)}>
          <option value="">All Sports</option>
          {sports.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
        </select>
        <select value={filters.athlete_id} onChange={(event) => updateFilter("athlete_id", event.target.value)}>
          <option value="">All Athletes</option>
          {athletes.map((athlete) => <option key={athlete.athlete_id} value={athlete.athlete_id}>{athlete.name}</option>)}
        </select>
        <input type="date" value={filters.start_date} onChange={(event) => updateFilter("start_date", event.target.value)} aria-label="Start date" />
        <input type="date" value={filters.end_date} onChange={(event) => updateFilter("end_date", event.target.value)} aria-label="End date" />
        <select value={filters.risk_level} onChange={(event) => updateFilter("risk_level", event.target.value)}>
          {riskOptions.map((risk) => <option key={risk || "all"} value={risk}>{risk || "All Risk Levels"}</option>)}
        </select>
        <select value={filters.injury_factor} onChange={(event) => updateFilter("injury_factor", event.target.value)}>
          {factorOptions.map((factor) => <option key={factor.value || "all"} value={factor.value}>{factor.label}</option>)}
        </select>
      </section>

      {loading && <section className="coach-empty-card">Loading injury-risk insights...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && athletes.length === 0 && (
        <section className="coach-empty-card">
          <h2>No accessible athletes are available for analysis.</h2>
          <p>Active Sports Scientist athlete connections will appear here once access is granted.</p>
        </section>
      )}

      {!loading && !error && athletes.length > 0 && (
        <>
          <section className="coach-stats-grid injury-insights-stats-grid">
            {summaryCards.map((card) => {
              const Icon = card.icon;
              return (
                <article className="coach-stat-card" key={card.label}>
                  <div className="coach-icon-box"><Icon size={21} /></div>
                  <div><span>{card.label}</span><strong>{card.value}</strong></div>
                </article>
              );
            })}
          </section>

          {(summary.analyses ?? 0) === 0 && (
            <section className="coach-empty-card">
              <h2>No completed analyses match these filters.</h2>
              <p>Only real completed analysis results from authorized athletes are included.</p>
            </section>
          )}

          {(summary.analyses ?? 0) > 0 && (
            <>
              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading">
                    <div><h2>Risk Overview</h2><p>Latest filtered analysis per athlete using existing risk bands.</p></div>
                  </div>
                  {distribution.every((item) => item.count === 0) ? (
                    <div className="coach-quiet-state">No risk distribution data available.</div>
                  ) : (
                    <div className="scientist-bar-list">
                      {distribution.map((item) => (
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
                    <div><h2>Risk Trend</h2><p>Average stored risk score over time.</p></div>
                  </div>
                  {riskTrend.length < 2 ? (
                    <div className="coach-quiet-state">Not enough dated analyses to display a trend.</div>
                  ) : (
                    <div className="scientist-trend-chart" aria-label="Average risk trend">
                      {riskTrend.map((point) => (
                        <div className="scientist-trend-point" key={point.date}>
                          <div style={{ height: `${Math.max(8, (Number(point.average_risk_score) / maxTrend) * 100)}%` }} title={`${formatValue(point.average_risk_score)} from ${point.analyses} analyses`} />
                          <span>{formatDate(point.date)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Average Risk by Sport</h2><p>Shown only where sufficient completed analysis data exists.</p></div>
                </div>
                {sportAverages.length === 0 ? (
                  <div className="coach-quiet-state">No sport/group has enough data for an average.</div>
                ) : (
                  <div className="team-category-grid">
                    {sportAverages.map((item) => (
                      <div className="team-category-row" key={item.group}>
                        <span>{item.group}</span>
                        <div className="scientist-bar-track">
                          <div className="scientist-bar-fill" style={{ width: `${Math.max(4, Number(item.average_risk_score) || 0)}%` }} />
                        </div>
                        <strong>{formatValue(item.average_risk_score)}</strong>
                        <small>{item.analyses} analyses</small>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Risk Factor Analysis</h2><p>Frequency and average stored risk contribution by existing factor.</p></div>
                </div>
                <div className="injury-factor-grid">
                  {factorAnalysis.map((factor) => (
                    <article className="coach-metric-card injury-factor-card" key={factor.key}>
                      <span>{factor.label}</span>
                      <strong>{factor.frequency}</strong>
                      <small>Average risk: {formatValue(factor.average_risk)}</small>
                      <small>Latest: {formatDate(factor.latest_at)}</small>
                      <small>{factor.trend?.length >= 2 ? `${factor.trend.length} trend points` : "Trend not available"}</small>
                    </article>
                  ))}
                </div>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Athlete Risk Table</h2><p>Authorized athletes with completed analyses only.</p></div>
                </div>
                {athleteRows.length === 0 ? (
                  <div className="coach-quiet-state">No athlete rows are available for these filters.</div>
                ) : (
                  <div className="coach-table-card">
                    <div className="injury-risk-table injury-risk-table-head">
                      <span>Athlete</span><span>Sport</span><span>Risk</span><span>Movement Quality</span><span>Main Risk Factors</span><span>Previous Injury</span><span>Latest Analysis</span>
                    </div>
                    {athleteRows.map((row) => (
                      <article className="injury-risk-table" key={row.athlete_id}>
                        <div className="coach-athlete-cell athlete">
                          <div className="coach-icon-box"><BarChart3 size={18} /></div>
                          <div><strong>{row.athlete_name}</strong></div>
                        </div>
                        <span className="coach-muted-cell">{row.sport || "Sport not set"}</span>
                        <span className={`coach-risk-text ${riskClass(row.risk_category)}`}>{row.risk_category} · {formatValue(row.risk_score)}</span>
                        <span className="coach-muted-cell">{formatValue(row.movement_quality)}</span>
                        <span className="coach-muted-cell">{compactFactors(row.main_risk_factors)}</span>
                        <span className="coach-muted-cell">{row.previous_injury ? "Recorded" : "None recorded"}</span>
                        <span className="coach-muted-cell">{formatDate(row.latest_analysis)}</span>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Observed Pattern Insights</h2><p>Objective patterns from stored analyses, not diagnoses or guaranteed injury predictions.</p></div>
                </div>
                {observedPatterns.length === 0 ? (
                  <div className="coach-quiet-state">No repeated observed patterns are available for these filters.</div>
                ) : (
                  <div className="coach-alert-list">
                    {observedPatterns.map((pattern, index) => (
                      <div className="coach-alert-row" key={`${pattern.title}-${pattern.athlete_id || index}`}>
                        <span className="coach-risk-dot moderate" />
                        <div>
                          <strong>{pattern.title}</strong>
                          <p>{pattern.pattern_type} · {pattern.description} Supporting analyses: {pattern.supporting_analyses}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </>
      )}
    </main>
  );
}


export default SportsScientistInjuryInsights;
