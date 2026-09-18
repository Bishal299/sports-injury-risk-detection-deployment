import React, { useEffect, useMemo, useState } from "react";
import { Download, FileText } from "lucide-react";

import {
  downloadSportsScientistResearchReport,
  getSportsScientistResearchReports,
} from "../../services/api";
import "../../styles/coach.css";


const riskOptions = ["", "LOW", "MODERATE", "HIGH", "CRITICAL"];

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function formatValue(value, fallback = "No data") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return fallback;
  const numeric = Number(value);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}


function SportsScientistResearchReports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [filters, setFilters] = useState({
    title: "",
    sport: "",
    athlete_ids: [],
    start_date: "",
    end_date: "",
    analysis_id: "",
    risk_level: "",
  });

  const requestFilters = useMemo(() => ({
    title: filters.title,
    sport: filters.sport,
    athlete_ids: filters.athlete_ids,
    start_date: filters.start_date,
    end_date: filters.end_date,
    analysis_id: filters.analysis_id,
    risk_level: filters.risk_level,
  }), [filters]);

  useEffect(() => {
    let cancelled = false;
    async function loadReports() {
      setLoading(true);
      setError("");
      try {
        const response = await getSportsScientistResearchReports(requestFilters);
        if (!cancelled) setData(response);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load research reports.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadReports();
    return () => {
      cancelled = true;
    };
  }, [requestFilters]);

  const athletes = Array.isArray(data?.athletes) ? data.athletes : [];
  const sports = Array.isArray(data?.sports) ? data.sports : [];
  const report = data?.report || {};
  const overview = report.overview || {};
  const risk = report.risk_analysis || {};
  const history = Array.isArray(data?.history) ? data.history : [];
  const selectedAthletes = athletes.filter((athlete) => filters.athlete_ids.includes(athlete.athlete_id));
  const selectedAnalysisOptions = selectedAthletes.flatMap((athlete) => athlete.analyses || []);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function toggleAthlete(athleteId) {
    setFilters((current) => {
      const selected = current.athlete_ids.includes(athleteId)
        ? current.athlete_ids.filter((id) => id !== athleteId)
        : [...current.athlete_ids, athleteId];
      return { ...current, athlete_ids: selected, analysis_id: "" };
    });
  }

  async function handleDownload() {
    setDownloading(true);
    setError("");
    try {
      await downloadSportsScientistResearchReport(requestFilters);
    } catch (error) {
      setError(error.message || "Failed to download research report.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">SPORTS SCIENTIST</p>
          <h1>Research Reports</h1>
          <p>Generate structured research reports from authorized completed analysis data.</p>
        </div>
        <FileText size={28} />
      </section>

      <section className="coach-filter-card research-report-filter-card">
        <input value={filters.title} onChange={(event) => updateFilter("title", event.target.value)} placeholder="Report title" />
        <select value={filters.sport} onChange={(event) => updateFilter("sport", event.target.value)}>
          <option value="">All Sports</option>
          {sports.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
        </select>
        <input type="date" value={filters.start_date} onChange={(event) => updateFilter("start_date", event.target.value)} aria-label="Start date" />
        <input type="date" value={filters.end_date} onChange={(event) => updateFilter("end_date", event.target.value)} aria-label="End date" />
        <select value={filters.risk_level} onChange={(event) => updateFilter("risk_level", event.target.value)}>
          {riskOptions.map((riskLevel) => <option key={riskLevel || "all"} value={riskLevel}>{riskLevel || "All Risk Levels"}</option>)}
        </select>
        <select value={filters.analysis_id} onChange={(event) => updateFilter("analysis_id", event.target.value)}>
          <option value="">All Matching Analyses</option>
          {selectedAnalysisOptions.map((analysis) => (
            <option key={analysis.analysis_id} value={analysis.analysis_id}>{analysis.label}</option>
          ))}
        </select>
      </section>

      {loading && <section className="coach-empty-card">Loading research report data...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && athletes.length === 0 && (
        <section className="coach-empty-card">
          <h2>No authorized analysis data is available.</h2>
          <p>Research reports require active athlete access and completed analyses.</p>
        </section>
      )}

      {!loading && !error && athletes.length > 0 && (
        <>
          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div><h2>Report Scope</h2><p>Select individual athletes, a group, sport, date range, analysis, and risk level.</p></div>
              <button className="secondary-button compact" type="button" onClick={handleDownload} disabled={downloading || !overview.analysis_count}>
                <Download size={15} />{downloading ? "Exporting..." : "Export PDF"}
              </button>
            </div>
            <div className="athlete-comparison-picker">
              {athletes.map((athlete) => (
                <button
                  className={filters.athlete_ids.includes(athlete.athlete_id) ? "active" : ""}
                  key={athlete.athlete_id}
                  type="button"
                  onClick={() => toggleAthlete(athlete.athlete_id)}
                >
                  <strong>{athlete.name}</strong>
                  <span>{athlete.sport || "Sport not set"} · {athlete.position || "Position not set"}</span>
                  <small>{athlete.analyses?.length || 0} analyses</small>
                </button>
              ))}
            </div>
          </section>

          {!overview.analysis_count ? (
            <section className="coach-empty-card">
              <h2>No completed analyses match this report scope.</h2>
              <p>Adjust filters or select athletes with completed analysis data.</p>
            </section>
          ) : (
            <>
              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Report Overview</h2><p>{report.title}</p></div></div>
                <div className="coach-performance-grid scientist-summary-grid">
                  <div className="coach-metric-card"><span>Scope</span><strong>{overview.scope}</strong></div>
                  <div className="coach-metric-card"><span>Date Range</span><strong>{overview.date_range}</strong></div>
                  <div className="coach-metric-card"><span>Athletes</span><strong>{overview.athlete_count}</strong></div>
                  <div className="coach-metric-card"><span>Analyses</span><strong>{overview.analysis_count}</strong></div>
                </div>
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Performance Summary</h2><p>Existing stored metrics only.</p></div></div>
                  <div className="scientist-breakdown-list">
                    {(report.performance_summary || []).map((item) => (
                      <div className="scientist-breakdown-row" key={item.key}>
                        <span>{item.label}</span><strong>{formatValue(item.average)}</strong><small>{item.count} values</small>
                      </div>
                    ))}
                  </div>
                </article>
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Biomechanical Analysis</h2><p>Available category risk values from completed analyses.</p></div></div>
                  <div className="scientist-breakdown-list">
                    {(report.biomechanical_analysis || []).map((item) => (
                      <div className="scientist-breakdown-row" key={item.key}>
                        <span>{item.label}</span><strong>{formatValue(item.average)}</strong><small>{item.count} values</small>
                      </div>
                    ))}
                  </div>
                </article>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Risk Analysis</h2><p>Risk distribution, history, training load availability, and recurring factors.</p></div></div>
                <div className="coach-dashboard-grid">
                  <div className="scientist-bar-list">
                    {(risk.distribution || []).map((item) => (
                      <div className="scientist-bar-row" key={item.category}>
                        <span>{item.category}</span>
                        <div className="scientist-bar-track"><div className="scientist-bar-fill" style={{ width: `${item.percentage || 0}%` }} /></div>
                        <strong>{item.count} · {item.percentage}%</strong>
                      </div>
                    ))}
                  </div>
                  <div className="scientist-breakdown-list">
                    <div className="scientist-breakdown-row"><span>Previous Injury History</span><strong>{risk.previous_injury_history_count || 0}</strong><small>athletes with records in scope</small></div>
                    <div className="scientist-breakdown-row"><span>Training Load</span><strong>{risk.training_load_values || 0}</strong><small>analysis values available</small></div>
                    {(risk.recurring_factors || []).slice(0, 4).map((item) => (
                      <div className="scientist-breakdown-row" key={item.label}><span>{item.label}</span><strong>{item.count}</strong><small>occurrences</small></div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Observed Patterns</h2><p>Objective patterns supported by underlying data only.</p></div></div>
                {(report.observed_patterns || []).length === 0 ? (
                  <div className="coach-quiet-state">No repeated observed patterns are available for this scope.</div>
                ) : (
                  <div className="coach-alert-list">
                    {report.observed_patterns.map((pattern, index) => (
                      <div className="coach-alert-row" key={`${pattern.title}-${index}`}>
                        <span className="coach-risk-dot moderate" />
                        <div><strong>{pattern.title}</strong><p>{pattern.description}</p></div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card"><div className="coach-section-heading"><div><h2>Analysis Methodology</h2></div></div><p className="research-report-copy">{report.methodology}</p></article>
                <article className="coach-panel-card"><div className="coach-section-heading"><div><h2>Limitations / Disclaimer</h2></div></div><p className="research-report-copy">{report.disclaimer}</p></article>
              </section>
            </>
          )}

          <section className="coach-panel-card">
            <div className="coach-section-heading"><div><h2>Report History</h2><p>Previously generated analysis PDF reports available in the existing report system.</p></div></div>
            {history.length === 0 ? (
              <div className="coach-quiet-state">No existing PDF report history is available.</div>
            ) : (
              <div className="coach-report-list">
                {history.map((item) => (
                  <article className="coach-report-row" key={item.report_id}>
                    <div><strong>{item.report_name}</strong><p>{item.scope} · Created by {item.created_by}</p></div>
                    <span>{formatDate(item.created_date)}</span>
                    <span className="coach-connected-badge active">{item.status}</span>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}


export default SportsScientistResearchReports;
