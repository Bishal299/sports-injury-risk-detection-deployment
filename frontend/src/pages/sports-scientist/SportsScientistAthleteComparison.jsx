import React, { useEffect, useMemo, useState } from "react";
import { BarChart3, GitCompare, LineChart } from "lucide-react";

import { getSportsScientistAthleteComparison } from "../../services/api";
import "../../styles/coach.css";


const dateRangeOptions = [
  { value: "all", label: "All Time" },
  { value: "7", label: "Last 7 Days" },
  { value: "30", label: "Last 30 Days" },
  { value: "90", label: "Last 3 Months" },
  { value: "custom", label: "Custom Range" },
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
  if (value === null || value === undefined || Number.isNaN(Number(value))) return fallback;
  const numeric = Number(value);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}

function dateFromRange(range) {
  if (range === "all" || range === "custom") return "";
  const date = new Date();
  date.setDate(date.getDate() - Number(range));
  return date.toISOString().slice(0, 10);
}


function SportsScientistAthleteComparison() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    sport: "",
    position: "",
    dateRange: "all",
    start_date: "",
    end_date: "",
  });
  const [selectedAthletes, setSelectedAthletes] = useState([]);
  const [selectedAnalyses, setSelectedAnalyses] = useState({});

  const requestFilters = useMemo(() => {
    const startDate = filters.dateRange === "custom" ? filters.start_date : dateFromRange(filters.dateRange);
    const params = {
      sport: filters.sport,
      position: filters.position,
      start_date: startDate,
      end_date: filters.dateRange === "custom" ? filters.end_date : "",
    };
    if (selectedAthletes.length >= 2) {
      selectedAthletes.forEach((athleteId) => {
        params.athlete_ids = [...(params.athlete_ids || []), athleteId];
      });
      Object.values(selectedAnalyses).forEach((analysisId) => {
        if (analysisId) params.analysis_ids = [...(params.analysis_ids || []), analysisId];
      });
    }
    return params;
  }, [filters, selectedAnalyses, selectedAthletes]);

  useEffect(() => {
    let cancelled = false;

    async function loadComparison() {
      setLoading(true);
      setError("");
      try {
        const response = await getSportsScientistAthleteComparison(requestFilters);
        if (!cancelled) setData(response);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load athlete comparison.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadComparison();
    return () => {
      cancelled = true;
    };
  }, [requestFilters]);

  const athletes = Array.isArray(data?.athletes) ? data.athletes : [];
  const sports = Array.isArray(data?.sports) ? data.sports : [];
  const positions = Array.isArray(data?.positions) ? data.positions : [];
  const selectedAthleteDetails = Array.isArray(data?.selected_athletes) ? data.selected_athletes : [];
  const metricRows = Array.isArray(data?.metric_rows) ? data.metric_rows : [];
  const history = Array.isArray(data?.history) ? data.history : [];
  const observations = Array.isArray(data?.observations) ? data.observations : [];

  const maxHistory = Math.max(...history.map((point) => Number(point.average_risk_score) || 0), 1);
  const visualRows = metricRows.filter((row) => (
    ["movement_quality", "symmetry", "overall_risk", "biomechanical_efficiency"].includes(row.key)
  ));

  function updateFilter(name, value) {
    setSelectedAthletes([]);
    setSelectedAnalyses({});
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function toggleAthlete(athleteId) {
    setSelectedAthletes((current) => {
      if (current.includes(athleteId)) {
        const next = current.filter((id) => id !== athleteId);
        setSelectedAnalyses((analysisState) => {
          const copy = { ...analysisState };
          delete copy[athleteId];
          return copy;
        });
        return next;
      }
      if (current.length >= 5) return current;
      return [...current, athleteId];
    });
  }

  function updateAnalysis(athleteId, analysisId) {
    setSelectedAnalyses((current) => ({ ...current, [athleteId]: analysisId }));
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">SPORTS SCIENTIST</p>
          <h1>Athlete Comparison</h1>
          <p>Compare stored biomechanical and performance measurements across authorized athletes.</p>
        </div>
        <GitCompare size={28} />
      </section>

      <section className="coach-filter-card athlete-comparison-filter-card">
        <select value={filters.sport} onChange={(event) => updateFilter("sport", event.target.value)}>
          <option value="">All Sports</option>
          {sports.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
        </select>
        {positions.length > 0 && (
          <select value={filters.position} onChange={(event) => updateFilter("position", event.target.value)}>
            <option value="">All Positions</option>
            {positions.map((position) => <option key={position} value={position}>{position}</option>)}
          </select>
        )}
        <select value={filters.dateRange} onChange={(event) => updateFilter("dateRange", event.target.value)}>
          {dateRangeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        {filters.dateRange === "custom" && (
          <>
            <input type="date" value={filters.start_date} onChange={(event) => updateFilter("start_date", event.target.value)} aria-label="Start date" />
            <input type="date" value={filters.end_date} onChange={(event) => updateFilter("end_date", event.target.value)} aria-label="End date" />
          </>
        )}
      </section>

      {loading && <section className="coach-empty-card">Loading athlete comparison...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && athletes.length === 0 && (
        <section className="coach-empty-card">
          <h2>No comparable analyses are available.</h2>
          <p>Authorized athletes with completed analyses will appear here.</p>
        </section>
      )}

      {!loading && !error && athletes.length > 0 && (
        <>
          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div><h2>Athlete Selection</h2><p>Select 2 to 5 authorized athletes with completed analyses.</p></div>
              <span className="coach-connected-badge active">{selectedAthletes.length}/5 selected</span>
            </div>
            <div className="athlete-comparison-picker">
              {athletes.map((athlete) => (
                <button
                  className={selectedAthletes.includes(athlete.athlete_id) ? "active" : ""}
                  key={athlete.athlete_id}
                  type="button"
                  onClick={() => toggleAthlete(athlete.athlete_id)}
                  disabled={!selectedAthletes.includes(athlete.athlete_id) && selectedAthletes.length >= 5}
                >
                  <strong>{athlete.name}</strong>
                  <span>{athlete.sport || "Sport not set"} · {athlete.position || "Position not set"}</span>
                  <small>{athlete.analyses?.length || 0} analyses</small>
                </button>
              ))}
            </div>
            {selectedAthletes.length > 0 && selectedAthletes.length < 2 && (
              <div className="coach-quiet-state compact-state">Select at least one more athlete to compare.</div>
            )}
          </section>

          {selectedAthleteDetails.length >= 2 && (
            <>
              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Analysis History</h2><p>Compare latest analyses or choose a specific completed analysis per athlete.</p></div>
                </div>
                <div className="analysis-selection-grid">
                  {selectedAthleteDetails.map((athlete) => (
                    <label key={athlete.athlete_id}>
                      <span>{athlete.name}</span>
                      <select value={selectedAnalyses[athlete.athlete_id] || ""} onChange={(event) => updateAnalysis(athlete.athlete_id, event.target.value)}>
                        <option value="">Latest matching analysis</option>
                        {athlete.analyses.map((analysis) => (
                          <option key={analysis.analysis_id} value={analysis.analysis_id}>
                            {analysis.label} · {analysis.risk_category} · {formatValue(analysis.risk_score)}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Metric Comparison</h2><p>Available real values from the selected completed analyses.</p></div>
                </div>
                <div className="coach-table-card comparison-metric-card">
                  <div className="comparison-metric-row comparison-metric-head" style={{ gridTemplateColumns: `minmax(170px, 0.9fr) repeat(${selectedAthleteDetails.length}, minmax(120px, 1fr))` }}>
                    <span>Metric</span>
                    {selectedAthleteDetails.map((athlete) => <span key={athlete.athlete_id}>{athlete.name}</span>)}
                  </div>
                  {metricRows.map((row) => (
                    <div className="comparison-metric-row" key={row.key} style={{ gridTemplateColumns: `minmax(170px, 0.9fr) repeat(${selectedAthleteDetails.length}, minmax(120px, 1fr))` }}>
                      <strong>{row.label}</strong>
                      {selectedAthleteDetails.map((athlete) => {
                        const value = row.values.find((item) => item.athlete_id === athlete.athlete_id);
                        return <span key={athlete.athlete_id}>{formatValue(value?.value)}</span>;
                      })}
                    </div>
                  ))}
                </div>
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Visual Comparison</h2><p>Neutral bar view of core metrics with available values.</p></div><BarChart3 size={20} /></div>
                  {visualRows.length === 0 ? (
                    <div className="coach-quiet-state">No visual comparison values are available.</div>
                  ) : (
                    <div className="visual-comparison-list">
                      {visualRows.map((row) => (
                        <div className="visual-comparison-group" key={row.key}>
                          <strong>{row.label}</strong>
                          {row.values.map((item) => (
                            <div className="visual-comparison-row" key={`${row.key}-${item.athlete_id}`}>
                              <span>{item.athlete_name}</span>
                              <div className="scientist-bar-track">
                                <div className="scientist-bar-fill" style={{ width: `${Math.max(0, Math.min(100, Number(item.value) || 0))}%` }} />
                              </div>
                              <small>{formatValue(item.value)}</small>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  )}
                </article>

                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Historical Comparison</h2><p>Average stored risk across selected athletes over time.</p></div><LineChart size={20} /></div>
                  {history.length < 2 ? (
                    <div className="coach-quiet-state">Not enough historical data to display a trend.</div>
                  ) : (
                    <div className="scientist-trend-chart" aria-label="Selected athlete risk history">
                      {history.map((point) => (
                        <div className="scientist-trend-point" key={point.date}>
                          <div style={{ height: `${Math.max(8, (Number(point.average_risk_score) / maxHistory) * 100)}%` }} title={`${formatValue(point.average_risk_score)} from ${point.analyses} analyses`} />
                          <span>{formatDate(point.date)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Key Observations</h2><p>Data-based observations only; no ranking, diagnosis, or unsupported conclusions.</p></div>
                </div>
                {observations.length === 0 ? (
                  <div className="coach-quiet-state">No notable data-based differences or repeated patterns are available for this selection.</div>
                ) : (
                  <div className="coach-alert-list">
                    {observations.map((observation, index) => (
                      <div className="coach-alert-row" key={`${observation.title}-${index}`}>
                        <span className="coach-risk-dot moderate" />
                        <div>
                          <strong>{observation.title}</strong>
                          <p>{observation.observation_type} · {observation.description} Supporting analyses: {observation.supporting_analyses}</p>
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


export default SportsScientistAthleteComparison;
