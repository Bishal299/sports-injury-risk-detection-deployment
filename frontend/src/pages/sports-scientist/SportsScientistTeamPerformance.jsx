import React, { useEffect, useMemo, useState } from "react";
import { BarChart3, LineChart, UsersRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getSportsScientistBiomechanicalAnalytics } from "../../services/api";
import "../../styles/coach.css";


const dateRangeOptions = [
  { value: "all", label: "All Time" },
  { value: "7", label: "Last 7 Days" },
  { value: "30", label: "Last 30 Days" },
  { value: "90", label: "Last 3 Months" },
  { value: "custom", label: "Custom Range" },
];

const metricOptions = [
  { key: "movement_quality", label: "Movement Quality" },
  { key: "biomechanical_efficiency", label: "Biomechanical Efficiency" },
  { key: "risk_score", label: "Overall Risk" },
  { key: "symmetry.overall_symmetry", label: "Symmetry" },
  { key: "breakdown.knee_valgus", label: "Knee Risk" },
  { key: "breakdown.hip_stability", label: "Hip Risk" },
  { key: "breakdown.trunk_lean", label: "Trunk Risk" },
  { key: "breakdown.landing_mechanics", label: "Landing Risk" },
  { key: "breakdown.dynamic_balance", label: "Balance Risk" },
];

const biomechanicalCategories = [
  { key: "breakdown.knee_valgus", label: "Knee" },
  { key: "breakdown.hip_stability", label: "Hip" },
  { key: "breakdown.trunk_lean", label: "Trunk" },
  { key: "breakdown.landing_mechanics", label: "Landing" },
  { key: "breakdown.dynamic_balance", label: "Balance" },
  { key: "breakdown.joint_alignment", label: "Alignment" },
  { key: "breakdown.posture", label: "Posture" },
];

const riskBands = ["LOW", "MODERATE", "HIGH", "CRITICAL"];


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
    return "Data unavailable";
  }
  const numeric = Number(value);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}

function riskClass(value) {
  return String(value || "not-available").toLowerCase().replace(/\s+/g, "-");
}

function average(values) {
  const numeric = values
    .map((value) => Number(value))
    .filter((value) => !Number.isNaN(value));
  if (!numeric.length) return null;
  return numeric.reduce((sum, value) => sum + value, 0) / numeric.length;
}

function dateKey(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString().slice(0, 10);
}

function getMetricValue(analysis, key) {
  if (!analysis) return null;
  if (key === "biomechanical_efficiency") {
    return typeof analysis.biomechanical_efficiency === "object"
      ? analysis.biomechanical_efficiency?.final
      : analysis.biomechanical_efficiency;
  }
  if (key.startsWith("symmetry.")) return analysis.symmetry?.[key.replace("symmetry.", "")];
  if (key.startsWith("breakdown.")) {
    const target = analysis.biomechanical_breakdown?.find((item) => item.key === key.replace("breakdown.", ""));
    return target?.risk_value;
  }
  return analysis[key] ?? analysis.summary?.[key] ?? null;
}

function latestByAthlete(analyses) {
  const latest = new Map();
  analyses.forEach((analysis) => {
    const current = latest.get(analysis.athlete_id);
    const currentTime = current ? new Date(current.analysis_date || 0).getTime() : -1;
    const nextTime = new Date(analysis.analysis_date || 0).getTime();
    if (!current || nextTime >= currentTime) latest.set(analysis.athlete_id, analysis);
  });
  return Array.from(latest.values());
}


function SportsScientistTeamPerformance() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    sport: "all",
    group: "all",
    position: "all",
    dateRange: "all",
    startDate: "",
    endDate: "",
    metric: "movement_quality",
  });
  const [selectedAthletes, setSelectedAthletes] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function loadTeamPerformance() {
      setLoading(true);
      setError("");
      try {
        const response = await getSportsScientistBiomechanicalAnalytics();
        if (!cancelled) setData(response);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load team performance trends.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadTeamPerformance();
    return () => {
      cancelled = true;
    };
  }, []);

  const athletes = Array.isArray(data?.athletes) ? data.athletes : [];
  const analyses = Array.isArray(data?.analyses) ? data.analyses : [];
  const sports = Array.isArray(data?.sports) ? data.sports : [];
  const positions = useMemo(
    () => Array.from(new Set(athletes.map((athlete) => athlete.position).filter(Boolean))).sort(),
    [athletes]
  );

  const filteredAnalyses = useMemo(() => {
    const now = new Date();
    return analyses.filter((analysis) => {
      const analysisDate = analysis.analysis_date ? new Date(analysis.analysis_date) : null;
      const sportMatch = filters.sport === "all" || analysis.sport === filters.sport;
      const groupMatch = filters.group === "all" || analysis.athlete_id === filters.group;
      const positionMatch = filters.position === "all" || analysis.position === filters.position;
      let dateMatch = true;

      if (filters.dateRange !== "all" && analysisDate) {
        if (filters.dateRange === "custom") {
          const start = filters.startDate ? new Date(filters.startDate) : null;
          const end = filters.endDate ? new Date(filters.endDate) : null;
          dateMatch = (!start || analysisDate >= start) && (!end || analysisDate <= end);
        } else {
          const cutoff = new Date(now);
          cutoff.setDate(cutoff.getDate() - Number(filters.dateRange));
          dateMatch = analysisDate >= cutoff;
        }
      }

      return sportMatch && groupMatch && positionMatch && dateMatch;
    });
  }, [analyses, filters]);

  const athleteRows = useMemo(() => {
    return athletes
      .map((athlete) => {
        const athleteAnalyses = filteredAnalyses
          .filter((analysis) => analysis.athlete_id === athlete.athlete_id)
          .sort((a, b) => new Date(a.analysis_date || 0) - new Date(b.analysis_date || 0));
        const latest = athleteAnalyses[athleteAnalyses.length - 1] || null;
        const previous = athleteAnalyses[athleteAnalyses.length - 2] || null;
        const currentQuality = latest?.movement_quality;
        const previousQuality = previous?.movement_quality;
        const trend = currentQuality !== null && currentQuality !== undefined && previousQuality !== null && previousQuality !== undefined
          ? Number(currentQuality) - Number(previousQuality)
          : null;

        return {
          athlete,
          analyses: athleteAnalyses,
          latest,
          movementQuality: average(athleteAnalyses.map((analysis) => analysis.movement_quality)),
          efficiency: average(athleteAnalyses.map((analysis) => getMetricValue(analysis, "biomechanical_efficiency"))),
          riskScore: average(athleteAnalyses.map((analysis) => analysis.risk_score)),
          trend,
        };
      })
      .filter((row) => row.analyses.length > 0);
  }, [athletes, filteredAnalyses]);

  const summaryCards = useMemo(() => ([
    { label: "Athletes Analyzed", value: new Set(filteredAnalyses.map((analysis) => analysis.athlete_id)).size, icon: UsersRound },
    { label: "Analyses Completed", value: filteredAnalyses.length, icon: BarChart3 },
    { label: "Average Movement Quality", value: formatValue(average(filteredAnalyses.map((analysis) => analysis.movement_quality))), icon: LineChart },
    { label: "Average Biomechanical Efficiency", value: formatValue(average(filteredAnalyses.map((analysis) => getMetricValue(analysis, "biomechanical_efficiency")))), icon: LineChart },
    { label: "Average Risk Score", value: formatValue(average(filteredAnalyses.map((analysis) => analysis.risk_score))), icon: BarChart3 },
  ]), [filteredAnalyses]);

  const trendPoints = useMemo(() => {
    const grouped = new Map();
    filteredAnalyses.forEach((analysis) => {
      const key = dateKey(analysis.analysis_date);
      const value = getMetricValue(analysis, filters.metric);
      if (!key || value === null || value === undefined) return;
      const existing = grouped.get(key) || [];
      existing.push(value);
      grouped.set(key, existing);
    });
    return Array.from(grouped.entries())
      .map(([date, values]) => ({ date, value: average(values), count: values.length }))
      .filter((point) => point.value !== null)
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [filteredAnalyses, filters.metric]);

  const riskDistribution = useMemo(() => {
    const latest = latestByAthlete(filteredAnalyses);
    const counts = Object.fromEntries(riskBands.map((band) => [band, 0]));
    latest.forEach((analysis) => {
      if (counts[analysis.risk_category] !== undefined) counts[analysis.risk_category] += 1;
    });
    const total = latest.length;
    return riskBands.map((band) => ({
      category: band,
      count: counts[band],
      percentage: total ? (counts[band] / total) * 100 : 0,
    }));
  }, [filteredAnalyses]);

  const categoryAverages = useMemo(() => (
    biomechanicalCategories.map((category) => {
      const values = filteredAnalyses.map((analysis) => getMetricValue(analysis, category.key));
      const value = average(values);
      return {
        ...category,
        value,
        count: values.filter((item) => item !== null && item !== undefined).length,
      };
    })
  ), [filteredAnalyses]);

  const comparisonRows = useMemo(() => {
    return selectedAthletes
      .map((athleteId) => {
        const row = athleteRows.find((item) => item.athlete.athlete_id === athleteId);
        if (!row) return null;
        const value = average(row.analyses.map((analysis) => getMetricValue(analysis, filters.metric)));
        return { ...row, comparisonValue: value };
      })
      .filter(Boolean);
  }, [athleteRows, filters.metric, selectedAthletes]);

  const maxTrend = Math.max(...trendPoints.map((point) => Number(point.value) || 0), 1);
  const maxCategory = Math.max(...categoryAverages.map((category) => Number(category.value) || 0), 1);
  const activeMetricLabel = metricOptions.find((option) => option.key === filters.metric)?.label || "Metric";

  function toggleComparisonAthlete(athleteId) {
    setSelectedAthletes((current) => (
      current.includes(athleteId)
        ? current.filter((id) => id !== athleteId)
        : [...current, athleteId]
    ));
  }

  function openAthleteAnalytics(row) {
    navigate("/sports-scientist/biomechanical-analytics", {
      state: {
        athleteId: row.athlete.athlete_id,
        analysisId: row.latest?.analysis_id || "",
      },
    });
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">SPORTS SCIENTIST</p>
          <h1>Team Performance Trends</h1>
          <p>Analyze performance and biomechanical trends across your monitored athletes.</p>
        </div>
        <LineChart size={28} />
      </section>

      {loading && <section className="coach-empty-card">Loading team performance trends...</section>}
      {error && <section className="coach-error-card">{error}</section>}

      {!loading && !error && athletes.length === 0 && (
        <section className="coach-empty-card">
          <h2>No accessible athletes are available for analysis.</h2>
          <p>Active athlete connections will appear here once access is granted.</p>
        </section>
      )}

      {!loading && !error && athletes.length > 0 && (
        <>
          <section className="coach-filter-card scientist-filter-card team-filter-card">
            <select value={filters.sport} onChange={(event) => setFilters({ ...filters, sport: event.target.value })}>
              <option value="all">All Sports</option>
              {sports.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
            </select>
            <select value={filters.group} onChange={(event) => setFilters({ ...filters, group: event.target.value })}>
              <option value="all">All Athletes</option>
              {athletes.map((athlete) => <option key={athlete.athlete_id} value={athlete.athlete_id}>{athlete.name}</option>)}
            </select>
            {positions.length > 0 && (
              <select value={filters.position} onChange={(event) => setFilters({ ...filters, position: event.target.value })}>
                <option value="all">All Positions</option>
                {positions.map((position) => <option key={position} value={position}>{position}</option>)}
              </select>
            )}
            <select value={filters.dateRange} onChange={(event) => setFilters({ ...filters, dateRange: event.target.value })}>
              {dateRangeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select value={filters.metric} onChange={(event) => setFilters({ ...filters, metric: event.target.value })}>
              {metricOptions.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}
            </select>
            {filters.dateRange === "custom" && (
              <>
                <input type="date" value={filters.startDate} onChange={(event) => setFilters({ ...filters, startDate: event.target.value })} />
                <input type="date" value={filters.endDate} onChange={(event) => setFilters({ ...filters, endDate: event.target.value })} />
              </>
            )}
          </section>

          <section className="coach-stats-grid team-stats-grid">
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

          {filteredAnalyses.length === 0 && (
            <section className="coach-empty-card">
              <h2>No completed analyses match these filters.</h2>
              <p>Completed movement analyses will appear here when available for the selected team view.</p>
            </section>
          )}

          {filteredAnalyses.length > 0 && (
            <>
              <section className="coach-dashboard-grid">
                <article className="coach-panel-card">
                  <div className="coach-section-heading">
                    <div><h2>Main Trend Chart</h2><p>Aggregate {activeMetricLabel.toLowerCase()} across completed analyses.</p></div>
                  </div>
                  {trendPoints.length < 2 ? (
                    <div className="coach-quiet-state">Not enough historical data to display a trend.</div>
                  ) : (
                    <div className="scientist-trend-chart team-trend-chart" aria-label={`${activeMetricLabel} team trend`}>
                      {trendPoints.map((point) => (
                        <div className="scientist-trend-point" key={point.date}>
                          <div style={{ height: `${Math.max(8, (Number(point.value) / maxTrend) * 100)}%` }} title={`${formatValue(point.value)} from ${point.count} analysis value${point.count === 1 ? "" : "s"}`} />
                          <span>{formatDate(point.date)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </article>

                <article className="coach-panel-card">
                  <div className="coach-section-heading">
                    <div><h2>Team Risk Distribution</h2><p>Current risk bands from latest filtered analyses per athlete.</p></div>
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
                          <strong>{item.count} - {item.percentage.toFixed(1)}%</strong>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Biomechanical Category Trends</h2><p>Aggregate available category risk values from stored analysis outputs.</p></div>
                </div>
                {categoryAverages.every((category) => category.count === 0) ? (
                  <div className="coach-quiet-state">No biomechanical category data available for these filters.</div>
                ) : (
                  <div className="team-category-grid">
                    {categoryAverages.map((category) => (
                      <div className="team-category-row" key={category.key}>
                        <span>{category.label}</span>
                        <div className="scientist-bar-track">
                          <div className="scientist-bar-fill" style={{ width: `${category.value === null ? 0 : Math.max(4, (Number(category.value) / maxCategory) * 100)}%` }} />
                        </div>
                        <strong>{formatValue(category.value)}</strong>
                        <small>{category.count ? `${category.count} value${category.count === 1 ? "" : "s"}` : "No data"}</small>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Comparison</h2><p>Select athletes for neutral side-by-side metric comparison.</p></div>
                </div>
                <div className="team-comparison-picker">
                  {athleteRows.map((row) => (
                    <label key={row.athlete.athlete_id}>
                      <input
                        type="checkbox"
                        checked={selectedAthletes.includes(row.athlete.athlete_id)}
                        onChange={() => toggleComparisonAthlete(row.athlete.athlete_id)}
                      />
                      <span>{row.athlete.name}</span>
                    </label>
                  ))}
                </div>
                {comparisonRows.length < 2 ? (
                  <div className="coach-quiet-state">Select at least two athletes with completed analyses to compare.</div>
                ) : (
                  <div className="scientist-breakdown-table" role="table" aria-label="Athlete comparison">
                    <div className="team-comparison-row head" role="row">
                      <span>Athlete</span><span>Sport</span><span>Position</span><span>{activeMetricLabel}</span><span>Analyses</span>
                    </div>
                    {comparisonRows.map((row) => (
                      <div className="team-comparison-row" key={row.athlete.athlete_id} role="row">
                        <span>{row.athlete.name}</span>
                        <span>{row.athlete.sport || "Sport not set"}</span>
                        <span>{row.athlete.position || "Position not set"}</span>
                        <span>{formatValue(row.comparisonValue)}</span>
                        <span>{row.analyses.length}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>Athlete Performance Table</h2><p>Filtered athlete-level aggregates from completed analyses.</p></div>
                </div>
                {athleteRows.length === 0 ? (
                  <div className="coach-quiet-state">No athlete performance rows are available for these filters.</div>
                ) : (
                  <div className="coach-table-card">
                    <div className="team-performance-table team-performance-head">
                      <span>Athlete</span><span>Sport</span><span>Analyses</span><span>Movement Quality</span><span>Efficiency</span><span>Risk</span><span>Trend</span>
                    </div>
                    {athleteRows.map((row) => (
                      <article
                        className="team-performance-table scientist-clickable-row"
                        key={row.athlete.athlete_id}
                        onClick={() => openAthleteAnalytics(row)}
                      >
                        <div className="coach-athlete-cell athlete">
                          <div className="coach-icon-box"><BarChart3 size={18} /></div>
                          <div><strong>{row.athlete.name}</strong><small>{row.athlete.position || "Position not set"}</small></div>
                        </div>
                        <span className="coach-muted-cell">{row.athlete.sport || "Sport not set"}</span>
                        <span className="coach-muted-cell">{row.analyses.length}</span>
                        <span className="coach-muted-cell">{formatValue(row.movementQuality)}</span>
                        <span className="coach-muted-cell">{formatValue(row.efficiency)}</span>
                        <span className={`coach-risk-text ${riskClass(row.latest?.risk_category)}`}>{formatValue(row.riskScore)}</span>
                        <span className="coach-muted-cell">{row.trend === null || Number.isNaN(row.trend) ? "Data unavailable" : `${row.trend > 0 ? "+" : ""}${row.trend.toFixed(1)}`}</span>
                      </article>
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


export default SportsScientistTeamPerformance;
