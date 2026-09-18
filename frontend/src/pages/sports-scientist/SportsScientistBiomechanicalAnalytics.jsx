import React, { useEffect, useMemo, useState } from "react";
import { BarChart3, Microscope } from "lucide-react";
import { useLocation } from "react-router-dom";

import { getSportsScientistBiomechanicalAnalytics } from "../../services/api";
import "../../styles/coach.css";


const riskOptions = ["All", "LOW", "MODERATE", "HIGH", "CRITICAL"];
const dateRangeOptions = [
  { value: "all", label: "All Time" },
  { value: "7", label: "Last 7 Days" },
  { value: "30", label: "Last 30 Days" },
  { value: "90", label: "Last 3 Months" },
  { value: "custom", label: "Custom Range" },
];

const trendMetricOptions = [
  { key: "risk_score", label: "Overall Risk" },
  { key: "movement_quality", label: "Movement Quality" },
  { key: "biomechanical_efficiency", label: "Biomechanical Efficiency" },
  { key: "symmetry.overall_symmetry", label: "Symmetry" },
  { key: "breakdown.knee_valgus", label: "Knee Risk" },
  { key: "breakdown.hip_stability", label: "Hip Risk" },
  { key: "breakdown.trunk_lean", label: "Trunk Risk" },
  { key: "breakdown.landing_mechanics", label: "Landing Risk" },
  { key: "breakdown.dynamic_balance", label: "Balance Risk" },
];


function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatValue(value, unit = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Data unavailable";
  }
  const numeric = Number(value);
  const display = Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
  return `${display}${unit ? ` ${unit}` : ""}`;
}

function formatConfiguredWeight(value) {
  if (value === null || value === undefined || value === "") return "Data unavailable";
  return typeof value === "string" ? value : formatValue(value, "%");
}

function riskClass(value) {
  return String(value || "not-available").toLowerCase().replace(/\s+/g, "-");
}

function getNestedValue(analysis, key) {
  if (!analysis) return null;
  if (key === "biomechanical_efficiency") {
    return typeof analysis.biomechanical_efficiency === "object"
      ? analysis.biomechanical_efficiency?.final
      : analysis.biomechanical_efficiency;
  }
  if (key.startsWith("summary.")) return analysis.summary?.[key.replace("summary.", "")];
  if (key.startsWith("symmetry.")) return analysis.symmetry?.[key.replace("symmetry.", "")];
  if (key.startsWith("breakdown.")) {
    const target = analysis.biomechanical_breakdown?.find((item) => item.key === key.replace("breakdown.", ""));
    return target?.risk_value;
  }
  return analysis[key] ?? analysis.summary?.[key];
}

function getMetricValue(analysis, key) {
  if (!analysis) return null;
  const direct = getNestedValue(analysis, key);
  if (direct !== null && direct !== undefined) return direct;
  return analysis.metrics?.find((metric) => metric.key === key)?.value;
}

function metricChange(current, previous) {
  if (current === null || current === undefined || previous === null || previous === undefined) {
    return null;
  }
  const change = Number(current) - Number(previous);
  if (Number.isNaN(change)) return null;
  if (change > 0) return { value: change, direction: "Increased" };
  if (change < 0) return { value: change, direction: "Decreased" };
  return { value: 0, direction: "Unchanged" };
}


function SportsScientistBiomechanicalAnalytics() {
  const location = useLocation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    athlete: location.state?.athleteId || "all",
    sport: "all",
    dateRange: "all",
    startDate: "",
    endDate: "",
    risk: "All",
    analysisId: location.state?.analysisId || "",
  });
  const [trendMetric, setTrendMetric] = useState("risk_score");
  const [dateSort, setDateSort] = useState("desc");

  useEffect(() => {
    let cancelled = false;

    async function loadAnalytics() {
      setLoading(true);
      setError("");
      try {
        const response = await getSportsScientistBiomechanicalAnalytics();
        if (!cancelled) setData(response);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load biomechanical analytics.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAnalytics();
    return () => {
      cancelled = true;
    };
  }, []);

  const athletes = Array.isArray(data?.athletes) ? data.athletes : [];
  const analyses = Array.isArray(data?.analyses) ? data.analyses : [];
  const sports = Array.isArray(data?.sports) ? data.sports : [];

  const filteredAnalyses = useMemo(() => {
    const now = new Date();
    const filtered = analyses.filter((analysis) => {
      const analysisDate = analysis.analysis_date ? new Date(analysis.analysis_date) : null;
      const athleteMatch = filters.athlete === "all" || analysis.athlete_id === filters.athlete;
      const sportMatch = filters.sport === "all" || analysis.sport === filters.sport;
      const riskMatch = filters.risk === "All" || analysis.risk_category === filters.risk;
      let dateMatch = true;

      if (filters.dateRange !== "all" && analysisDate) {
        if (filters.dateRange === "custom") {
          const start = filters.startDate ? new Date(filters.startDate) : null;
          const end = filters.endDate ? new Date(filters.endDate) : null;
          dateMatch = (!start || analysisDate >= start) && (!end || analysisDate <= end);
        } else {
          const days = Number(filters.dateRange);
          const cutoff = new Date(now);
          cutoff.setDate(cutoff.getDate() - days);
          dateMatch = analysisDate >= cutoff;
        }
      }

      return athleteMatch && sportMatch && riskMatch && dateMatch;
    });
    return filtered.sort((a, b) => {
      const left = new Date(a.analysis_date || 0).getTime();
      const right = new Date(b.analysis_date || 0).getTime();
      return dateSort === "asc" ? left - right : right - left;
    });
  }, [analyses, filters, dateSort]);

  const selectedAnalysis = useMemo(() => {
    if (filters.analysisId) {
      return analyses.find((analysis) => analysis.analysis_id === filters.analysisId) || null;
    }
    return null;
  }, [analyses, filters.analysisId]);

  const athleteAnalyses = useMemo(() => {
    if (!selectedAnalysis) return [];
    return analyses
      .filter((analysis) => analysis.athlete_id === selectedAnalysis.athlete_id)
      .sort((a, b) => new Date(a.analysis_date || 0) - new Date(b.analysis_date || 0));
  }, [analyses, selectedAnalysis]);

  const previousAnalysis = useMemo(() => {
    if (!selectedAnalysis) return null;
    const selectedDate = new Date(selectedAnalysis.analysis_date || 0).getTime();
    return [...athleteAnalyses]
      .reverse()
      .find((analysis) => analysis.analysis_id !== selectedAnalysis.analysis_id && new Date(analysis.analysis_date || 0).getTime() < selectedDate) || null;
  }, [athleteAnalyses, selectedAnalysis]);

  const availableTrendMetrics = trendMetricOptions.filter((option) => (
    athleteAnalyses.some((analysis) => getMetricValue(analysis, option.key) !== null && getMetricValue(analysis, option.key) !== undefined)
  ));
  const activeTrendMetric = availableTrendMetrics.some((option) => option.key === trendMetric)
    ? trendMetric
    : availableTrendMetrics[0]?.key;
  const trendPoints = activeTrendMetric
    ? athleteAnalyses
      .map((analysis) => ({
        date: analysis.analysis_date,
        value: getMetricValue(analysis, activeTrendMetric),
      }))
      .filter((point) => point.value !== null && point.value !== undefined)
    : [];
  const maxTrend = Math.max(...trendPoints.map((point) => Number(point.value) || 0), 1);

  const comparisonRows = selectedAnalysis ? [
    { label: "Overall Risk", current: selectedAnalysis.risk_score, previous: previousAnalysis?.risk_score },
    { label: "Movement Quality", current: selectedAnalysis.movement_quality, previous: previousAnalysis?.movement_quality },
    { label: "Biomechanical Efficiency", current: getMetricValue(selectedAnalysis, "biomechanical_efficiency"), previous: getMetricValue(previousAnalysis, "biomechanical_efficiency") },
    { label: "Symmetry", current: selectedAnalysis.symmetry?.overall_symmetry, previous: previousAnalysis?.symmetry?.overall_symmetry },
    { label: "Knee Risk", current: getMetricValue(selectedAnalysis, "breakdown.knee_valgus"), previous: getMetricValue(previousAnalysis, "breakdown.knee_valgus") },
    { label: "Hip Risk", current: getMetricValue(selectedAnalysis, "breakdown.hip_stability"), previous: getMetricValue(previousAnalysis, "breakdown.hip_stability") },
    { label: "Trunk Risk", current: getMetricValue(selectedAnalysis, "breakdown.trunk_lean"), previous: getMetricValue(previousAnalysis, "breakdown.trunk_lean") },
    { label: "Landing Risk", current: getMetricValue(selectedAnalysis, "breakdown.landing_mechanics"), previous: getMetricValue(previousAnalysis, "breakdown.landing_mechanics") },
    { label: "Balance Risk", current: getMetricValue(selectedAnalysis, "breakdown.dynamic_balance"), previous: getMetricValue(previousAnalysis, "breakdown.dynamic_balance") },
  ] : [];

  const filteredSummary = [
    { label: "Filtered Analyses", value: filteredAnalyses.length },
    { label: "Accessible Athletes", value: new Set(filteredAnalyses.map((analysis) => analysis.athlete_id)).size },
    { label: "Sports", value: new Set(filteredAnalyses.map((analysis) => analysis.sport).filter(Boolean)).size },
    { label: "High/Critical", value: filteredAnalyses.filter((analysis) => ["HIGH", "CRITICAL"].includes(analysis.risk_category)).length },
  ];

  return (
    <main className="coach-page">
      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">SPORTS SCIENTIST</p>
          <h1>Biomechanical Analytics</h1>
          <p>Explore movement patterns, biomechanical metrics, and injury-risk factors across analyzed athletes.</p>
        </div>
        <Microscope size={28} />
      </section>

      {loading && <section className="coach-empty-card">Loading biomechanical analytics...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && athletes.length === 0 && (
        <section className="coach-empty-card">
          <h2>No accessible athletes are available for analysis.</h2>
          <p>Active athlete connections will appear here once access is granted.</p>
        </section>
      )}

      {!loading && !error && athletes.length > 0 && (
        <>
          <section className="coach-filter-card scientist-filter-card">
            <select value={filters.athlete} onChange={(event) => setFilters({ ...filters, athlete: event.target.value, analysisId: "" })}>
              <option value="all">All Athletes</option>
              {athletes.map((athlete) => <option key={athlete.athlete_id} value={athlete.athlete_id}>{athlete.name}</option>)}
            </select>
            <select value={filters.sport} onChange={(event) => setFilters({ ...filters, sport: event.target.value, analysisId: "" })}>
              <option value="all">All Sports</option>
              {sports.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
            </select>
            <select value={filters.dateRange} onChange={(event) => setFilters({ ...filters, dateRange: event.target.value, analysisId: "" })}>
              {dateRangeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select value={filters.risk} onChange={(event) => setFilters({ ...filters, risk: event.target.value, analysisId: "" })}>
              {riskOptions.map((risk) => <option key={risk} value={risk}>{risk === "All" ? "All Risk" : risk}</option>)}
            </select>
            <select
              value={filters.analysisId}
              onChange={(event) => setFilters({ ...filters, analysisId: event.target.value })}
              disabled={filters.athlete === "all"}
            >
              <option value="">{filters.athlete === "all" ? "Select athlete first" : "Select analysis"}</option>
              {filteredAnalyses.map((analysis) => (
                <option key={analysis.analysis_id} value={analysis.analysis_id}>
                  {analysis.athlete_name} · {analysis.video_activity || "Analysis"} · {formatDate(analysis.analysis_date)}
                </option>
              ))}
            </select>
            {filters.dateRange === "custom" && (
              <>
                <input type="date" value={filters.startDate} onChange={(event) => setFilters({ ...filters, startDate: event.target.value, analysisId: "" })} />
                <input type="date" value={filters.endDate} onChange={(event) => setFilters({ ...filters, endDate: event.target.value, analysisId: "" })} />
              </>
            )}
          </section>

          <section className="coach-stats-grid scientist-analytics-stats">
            {filteredSummary.map((item) => (
              <article className="coach-stat-card" key={item.label}>
                <div><span>{item.label}</span><strong>{item.value}</strong></div>
              </article>
            ))}
          </section>

          {filteredAnalyses.length === 0 && (
            <section className="coach-empty-card">
              <h2>{filters.athlete === "all" ? "No completed biomechanical analyses are available." : "No completed analyses found for this athlete."}</h2>
              <p>Completed athlete analyses will appear here once movement analysis results are available.</p>
            </section>
          )}

          {filteredAnalyses.length > 0 && !selectedAnalysis && (
            <section className="coach-empty-card">Select an analysis to view detailed biomechanical metrics.</section>
          )}

          {selectedAnalysis && (
            <>
              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div>
                    <h2>Analysis Summary</h2>
                    <p>{selectedAnalysis.athlete_name} · {selectedAnalysis.sport || "Sport not set"} · {formatDate(selectedAnalysis.analysis_date)} · Status: {selectedAnalysis.status}</p>
                  </div>
                  <span className={`coach-risk-badge ${riskClass(selectedAnalysis.risk_category)}`}>{selectedAnalysis.risk_category}</span>
                </div>
                <div className="coach-performance-grid scientist-summary-grid">
                  <div className="coach-metric-card"><span>Overall Risk Score</span><strong>{formatValue(selectedAnalysis.risk_score)}</strong></div>
                  <div className="coach-metric-card"><span>Movement Quality</span><strong>{formatValue(selectedAnalysis.movement_quality)}</strong></div>
                  <div className="coach-metric-card"><span>Biomechanical Efficiency</span><strong>{formatValue(getNestedValue(selectedAnalysis, "biomechanical_efficiency"))}</strong></div>
                  <div className="coach-metric-card"><span>Movement Symmetry</span><strong>{formatValue(selectedAnalysis.symmetry?.overall_symmetry)}</strong></div>
                </div>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Source Analysis</h2><p>Traceability for the displayed biomechanical metrics.</p></div></div>
                <div className="coach-performance-grid scientist-summary-grid">
                  <div className="coach-metric-card"><span>Athlete</span><strong>{selectedAnalysis.athlete_name}</strong></div>
                  <div className="coach-metric-card"><span>Video / Analysis</span><strong>{selectedAnalysis.source_analysis?.video_activity || selectedAnalysis.source_analysis?.video_id || selectedAnalysis.analysis_id}</strong></div>
                  <div className="coach-metric-card"><span>Analyzed</span><strong>{formatDate(selectedAnalysis.source_analysis?.analyzed_at || selectedAnalysis.analysis_date)}</strong></div>
                  <div className="coach-metric-card"><span>Algorithm Version</span><strong>{selectedAnalysis.source_analysis?.algorithm_version || "Data unavailable"}</strong></div>
                </div>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Biomechanical Metrics</h2><p>Only existing metrics from this completed analysis are shown.</p></div></div>
                {selectedAnalysis.metrics?.length ? (
                  <div className="coach-performance-grid scientist-metric-grid">
                    {selectedAnalysis.metrics.map((metric) => (
                      <div className="coach-metric-card" key={metric.key}>
                        <span>{metric.label}</span>
                        <strong>{formatValue(metric.value, metric.unit)}</strong>
                        <small>{metric.severity ? `Risk: ${metric.severity}` : "Risk: Data not available"}</small>
                        {metric.interpretation && <small>{metric.interpretation}</small>}
                        {previousAnalysis && (() => {
                          const change = metricChange(metric.value, getMetricValue(previousAnalysis, metric.key));
                          return change ? <small>{change.direction}: {change.value > 0 ? "+" : ""}{change.value.toFixed(1)} from previous analysis</small> : null;
                        })()}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="coach-quiet-state">Data not available for this metric.</div>
                )}
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Risk Factor Overview</h2><p>Configured weights and stored component scores from the selected analysis.</p></div></div>
                  <div className="scientist-breakdown-list">
                    {selectedAnalysis.risk_contributions.map((item) => (
                      <div className="scientist-breakdown-row" key={item.key}>
                        <span>{item.label}</span>
                        <strong>{formatValue(item.observed_contribution)}</strong>
                        <small>Configured Weight: {formatConfiguredWeight(item.configured_weight)}</small>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Biomechanical Risk Breakdown</h2><p>Uses configured project weights; observed risk appears only when stored.</p></div></div>
                  <div className="scientist-breakdown-table" role="table" aria-label="Biomechanical risk breakdown">
                    <div className="scientist-breakdown-table-row head" role="row">
                      <span>Category</span><span>Risk</span><span>Weight</span><span>Weighted Contribution</span>
                    </div>
                    {selectedAnalysis.biomechanical_breakdown.map((item) => (
                      <div className="scientist-breakdown-table-row" key={item.key} role="row">
                        <span>{item.label}</span>
                        <span>{formatValue(item.risk_value)}</span>
                        <span>{formatConfiguredWeight(item.configured_weight)}</span>
                        <span>{formatValue(item.weighted_contribution)}</span>
                      </div>
                    ))}
                  </div>
                </article>
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Movement Quality</h2><p>Stored backend movement quality value.</p></div></div>
                  <div className="scientist-quality-meter">
                    <strong>{formatValue(selectedAnalysis.movement_quality)}</strong>
                    <div><span style={{ width: `${Math.max(0, Math.min(100, Number(selectedAnalysis.movement_quality) || 0))}%` }} /></div>
                  </div>
                </article>

                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Biomechanical Efficiency</h2><p>Existing backend efficiency result.</p></div></div>
                  <div className="coach-metric-card">
                    <span>Final Biomechanical Efficiency</span>
                    <strong>{formatValue(selectedAnalysis.biomechanical_efficiency?.final ?? selectedAnalysis.biomechanical_efficiency)}</strong>
                    <small>{selectedAnalysis.biomechanical_efficiency?.component_note || "Component values are not stored separately for this analysis."}</small>
                  </div>
                </article>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Movement Symmetry</h2><p>Stored symmetry and asymmetry values where available.</p></div></div>
                {selectedAnalysis.symmetry?.overall_symmetry || selectedAnalysis.symmetry?.stride_asymmetry || selectedAnalysis.symmetry?.asymmetry_risk ? (
                  <div className="coach-performance-grid">
                    <div className="coach-metric-card"><span>Movement Symmetry</span><strong>{formatValue(selectedAnalysis.symmetry.overall_symmetry)}</strong></div>
                    <div className="coach-metric-card"><span>Stride Asymmetry</span><strong>{formatValue(selectedAnalysis.symmetry.stride_asymmetry, "%")}</strong></div>
                    <div className="coach-metric-card"><span>Asymmetry Risk</span><strong>{formatValue(selectedAnalysis.symmetry.asymmetry_risk)}</strong></div>
                    {selectedAnalysis.symmetry?.affected_metrics?.slice(0, 3).map((metric) => (
                      <div className="coach-metric-card" key={metric}><span>Affected Metric</span><strong>{metric}</strong></div>
                    ))}
                  </div>
                ) : (
                  <div className="coach-quiet-state">Symmetry data is not available for this analysis.</div>
                )}
              </section>

              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading"><div><h2>Historical Comparison</h2><p>Selected analysis compared with the previous completed analysis.</p></div></div>
                  {!previousAnalysis ? (
                    <div className="coach-quiet-state">No previous analysis available for comparison.</div>
                  ) : (
                    <div className="scientist-breakdown-table comparison" role="table" aria-label="Historical comparison">
                      <div className="scientist-breakdown-table-row head" role="row">
                        <span>Metric</span><span>Previous</span><span>Current</span><span>Change</span>
                      </div>
                      {comparisonRows.map((row) => {
                        const change = metricChange(row.current, row.previous);
                        return (
                          <div className="scientist-breakdown-table-row" key={row.label} role="row">
                            <span>{row.label}</span>
                            <span>{formatValue(row.previous)}</span>
                            <span>{formatValue(row.current)}</span>
                            <span>{change ? `${change.value > 0 ? "+" : ""}${change.value.toFixed(1)}` : "Data unavailable"}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </article>

                <article className="coach-panel-card">
                  <div className="coach-section-heading">
                    <div><h2>Biomechanical Trend</h2><p>Historical values for the selected athlete.</p></div>
                    <select value={activeTrendMetric || ""} onChange={(event) => setTrendMetric(event.target.value)}>
                      {availableTrendMetrics.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}
                    </select>
                  </div>
                  {trendPoints.length < 2 ? (
                    <div className="coach-quiet-state">Not enough historical analyses to display a trend.</div>
                  ) : (
                    <div className="scientist-trend-chart">
                      {trendPoints.map((point) => (
                        <div className="scientist-trend-point" key={`${point.date}-${point.value}`}>
                          <div style={{ height: `${Math.max(8, (Number(point.value) / maxTrend) * 100)}%` }} />
                          <span>{formatDate(point.date)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </section>

            </>
          )}

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div><h2>Analysis History</h2><p>Completed analyses matching the current filters.</p></div>
              <button className="secondary-button compact" type="button" onClick={() => setDateSort(dateSort === "desc" ? "asc" : "desc")}>
                Date {dateSort === "desc" ? "Newest" : "Oldest"}
              </button>
            </div>
            <div className="coach-table-card">
              <div className="coach-athlete-table coach-athlete-table-head">
                <span>Athlete</span><span>Sport</span><span>Date</span><span>Risk</span><span>Movement Quality</span><span>Biomechanical Efficiency</span>
              </div>
              {filteredAnalyses.map((analysis) => (
                <article
                  className="coach-athlete-table scientist-clickable-row"
                  key={analysis.analysis_id}
                  onClick={() => setFilters({ ...filters, analysisId: analysis.analysis_id })}
                >
                  <div className="coach-athlete-cell athlete"><div className="coach-icon-box"><BarChart3 size={18} /></div><div><strong>{analysis.athlete_name}</strong></div></div>
                  <span className="coach-muted-cell">{analysis.sport || "Sport not set"}</span>
                  <span className="coach-muted-cell">{formatDate(analysis.analysis_date)}</span>
                  <span className={`coach-risk-text ${riskClass(analysis.risk_category)}`}>{analysis.risk_category}</span>
                  <span className="coach-muted-cell">{formatValue(analysis.movement_quality)}</span>
                  <span className="coach-muted-cell">{formatValue(analysis.biomechanical_efficiency?.final ?? analysis.biomechanical_efficiency)}</span>
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}


export default SportsScientistBiomechanicalAnalytics;
