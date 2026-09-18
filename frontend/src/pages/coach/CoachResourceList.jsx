import React, { useEffect, useMemo, useState } from "react";
import { BarChart3, Download, FileText, ListChecks, Search, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  createCoachAthleteTask,
  downloadCoachAthleteReport,
  getCoachAthleteDetail,
  getCoachConnectedAthletes,
} from "../../services/api";
import "../../styles/coach.css";


function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}


function riskClass(category) {
  return (category || "not-available").toLowerCase().replace(/\s+/g, "-");
}

function formatStatus(value) {
  if (!value) {
    return "Not Available";
  }

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") {
    return "Not Available";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return String(value);
  }

  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1);
}


function CoachResourceList({ type }) {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [athleteFilter, setAthleteFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [dateSort, setDateSort] = useState("newest");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const [recommendationTarget, setRecommendationTarget] = useState(null);
  const [recommendationForm, setRecommendationForm] = useState({
    title: "",
    description: "",
    priority: "MEDIUM",
    due_date: "",
  });
  const [recommendationSaving, setRecommendationSaving] = useState(false);
  const [recommendationMessage, setRecommendationMessage] = useState("");
  const [recommendationError, setRecommendationError] = useState("");

  const config = {
    videos: {
      eyebrow: "VIDEOS",
      title: "Videos",
      description: "Real data from athletes with active Coach relationships.",
      icon: Video,
      empty: "No connected athlete videos are available.",
    },
    analyses: {
      eyebrow: "ANALYSES",
      title: "Analyses",
      description: "Review completed movement and injury-risk analyses from your connected athletes.",
      icon: BarChart3,
      empty: "No connected athlete analyses are available.",
    },
    reports: {
      eyebrow: "REPORTS",
      title: "Reports",
      description: "Real data from athletes with active Coach relationships.",
      icon: FileText,
      empty: "No connected athlete reports are available.",
    },
  }[type];

  useEffect(() => {
    let cancelled = false;

    async function loadResources() {
      setLoading(true);
      setError("");

      try {
        const athletes = await getCoachConnectedAthletes();
        const details = await Promise.all(
          athletes.map(async (athlete) => {
            const detail = await getCoachAthleteDetail(athlete.athlete_id);
            return { athlete, detail };
          })
        );

        if (cancelled) {
          return;
        }

        const nextRows = details.flatMap(({ athlete, detail }) => {
          if (type === "videos") {
            return (detail.videos || []).map((video) => ({
              id: video.video_id,
              athlete_id: athlete.athlete_id,
              athlete_name: athlete.name,
              activity: video.activity || "Untitled Activity",
              date: video.uploaded_at,
              status: video.analysis_status || video.processing_status || "Pending",
              risk_category: video.risk_category,
              latest_analysis_id: video.latest_analysis_id,
              video_id: video.video_id,
            }));
          }

          if (type === "analyses") {
            const analyses = Array.isArray(detail.analyses) ? detail.analyses : [];
            return analyses
              .filter((analysis) => String(analysis.status || "").toLowerCase() === "completed")
              .map((analysis) => ({
              id: analysis.analysis_id,
              athlete_id: athlete.athlete_id,
              athlete_name: athlete.name,
              sport: athlete.sport,
              activity: analysis.video_activity || "Movement Analysis",
              date: analysis.completed_at || analysis.analysis_date,
              status: analysis.status,
              risk_category: analysis.risk_category,
              score: analysis.composite_risk_score ?? analysis.overall_risk_score,
              movement_quality: analysis.movement_quality,
              analysis_id: analysis.analysis_id,
              video_id: analysis.video_id,
            }));
          }

          const analyses = (detail.analyses || []).filter(
            (analysis) => analysis.pdf_report_available
          );

          return analyses.map((analysis) => ({
            id: analysis.analysis_id,
            athlete_id: athlete.athlete_id,
            athlete_name: athlete.name,
            activity: analysis.video_activity || "Movement Analysis",
            date: analysis.completed_at || analysis.analysis_date,
            status: analysis.status,
            risk_category: analysis.risk_category,
            score: analysis.composite_risk_score ?? analysis.overall_risk_score,
            analysis_id: analysis.analysis_id,
            video_id: analysis.video_id,
            pdf_report_available: analysis.pdf_report_available,
          }));
        });

        nextRows.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
        setRows(nextRows);
      } catch (error) {
        if (!cancelled) {
          setError(error.message || `Failed to load Coach ${config.title.toLowerCase()}.`);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadResources();

    return () => {
      cancelled = true;
    };
  }, [config.title, type]);

  const athleteOptions = useMemo(() => {
    const athletes = new Map();
    rows.forEach((row) => {
      athletes.set(row.athlete_id, row.athlete_name);
    });
    return Array.from(athletes.entries()).map(([id, name]) => ({ id, name }));
  }, [rows]);

  const riskOptions = useMemo(() => {
    return Array.from(new Set(rows.map((row) => row.risk_category).filter(Boolean))).sort();
  }, [rows]);

  const visibleRows = useMemo(() => {
    const value = search.trim().toLowerCase();

    return rows
      .filter((row) => {
        const matchesSearch = !value
          || row.athlete_name.toLowerCase().includes(value)
          || (row.sport || "").toLowerCase().includes(value)
          || row.activity.toLowerCase().includes(value)
          || (row.risk_category || "").toLowerCase().includes(value);
        const matchesAthlete = athleteFilter === "all" || row.athlete_id === athleteFilter;
        const matchesRisk = riskFilter === "all" || row.risk_category === riskFilter;
        return matchesSearch && matchesAthlete && matchesRisk;
      })
      .sort((a, b) => {
        const left = new Date(a.date || 0).getTime();
        const right = new Date(b.date || 0).getTime();
        return dateSort === "oldest" ? left - right : right - left;
      });
  }, [athleteFilter, dateSort, riskFilter, rows, search]);

  async function handleDownload(row, fileType) {
    setDownloadError("");
    try {
      await downloadCoachAthleteReport(row.athlete_id, row.video_id, fileType);
    } catch (error) {
      setDownloadError(error.message || "Report download failed.");
    }
  }

  function openRecommendation(row) {
    setRecommendationTarget(row);
    setRecommendationForm({
      title: "",
      description: "",
      priority: "MEDIUM",
      due_date: "",
    });
    setRecommendationMessage("");
    setRecommendationError("");
  }

  function closeRecommendation() {
    if (recommendationSaving) {
      return;
    }
    setRecommendationTarget(null);
    setRecommendationMessage("");
    setRecommendationError("");
  }

  async function handleSaveRecommendation(event) {
    event.preventDefault();
    if (!recommendationTarget || !recommendationForm.title.trim()) {
      return;
    }

    setRecommendationSaving(true);
    setRecommendationMessage("");
    setRecommendationError("");

    try {
      await createCoachAthleteTask(recommendationTarget.athlete_id, {
        title: recommendationForm.title.trim(),
        description: recommendationForm.description.trim() || null,
        priority: recommendationForm.priority,
        due_date: recommendationForm.due_date || null,
        status: "ASSIGNED",
        analysis_id: recommendationTarget.analysis_id,
        video_id: recommendationTarget.video_id,
      });
      setRecommendationMessage("Recommendation saved for this analysis.");
      setRecommendationForm({
        title: "",
        description: "",
        priority: "MEDIUM",
        due_date: "",
      });
    } catch (error) {
      setRecommendationError(error.message || "Failed to save recommendation.");
    } finally {
      setRecommendationSaving(false);
    }
  }

  const Icon = config.icon;

  return (
    <main className="coach-page">
        <section className="coach-page-header coach-page-header-row">
          <div>
            <p className="page-eyebrow">{config.eyebrow}</p>
            <h1>{config.title}</h1>
            <p>{config.description}</p>
          </div>
          <Icon size={28} />
        </section>

        <section className={`coach-table-toolbar ${type === "analyses" ? "coach-analysis-toolbar" : ""}`}>
          <label className="coach-search-field">
            <Search size={17} />
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={type === "analyses" ? "Search athlete, sport or analysis..." : `Search ${config.title.toLowerCase()}`}
            />
          </label>

          {type === "analyses" && (
            <>
              <select value={athleteFilter} onChange={(event) => setAthleteFilter(event.target.value)}>
                <option value="all">All Athletes</option>
                {athleteOptions.map((athlete) => (
                  <option key={athlete.id} value={athlete.id}>{athlete.name}</option>
                ))}
              </select>
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                <option value="all">Risk</option>
                {riskOptions.map((risk) => (
                  <option key={risk} value={risk}>{risk}</option>
                ))}
              </select>
              <select value={dateSort} onChange={(event) => setDateSort(event.target.value)}>
                <option value="newest">Date</option>
                <option value="oldest">Oldest First</option>
              </select>
            </>
          )}
        </section>

        {error && <section className="coach-error-card">{error}</section>}
        {downloadError && <section className="coach-error-card">{downloadError}</section>}
        {loading && <section className="coach-empty-card">Loading {config.title.toLowerCase()}...</section>}

        {!loading && !error && visibleRows.length === 0 && (
          <section className="coach-empty-card">{config.empty}</section>
        )}

        {!loading && !error && visibleRows.length > 0 && type === "analyses" && (
          <section className="coach-analysis-list">
            {visibleRows.map((row) => (
              <article className="coach-panel-card coach-analysis-summary-card" key={`${type}-${row.id}`}>
                <div className="coach-section-heading">
                  <div>
                    <h2>{row.athlete_name}</h2>
                    <p>{row.activity} · {formatDate(row.date)}</p>
                  </div>
                  <span className={`coach-risk-badge ${riskClass(row.risk_category)}`}>
                    {row.risk_category || "Not Available"}
                  </span>
                </div>

                <div className="coach-performance-grid coach-analysis-metrics">
                  <div className="coach-metric-card">
                    <span>Risk Score</span>
                    <strong>{formatScore(row.score)}</strong>
                  </div>
                  <div className="coach-metric-card">
                    <span>Movement Quality</span>
                    <strong>{formatScore(row.movement_quality)}</strong>
                  </div>
                  <div className="coach-metric-card">
                    <span>Status</span>
                    <strong>{formatStatus(row.status)}</strong>
                  </div>
                </div>

                <div className="coach-report-actions coach-analysis-actions">
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() => openRecommendation(row)}
                  >
                    <ListChecks size={15} />
                    Recommendations
                  </button>
                  <button
                    className="secondary-button compact"
                    type="button"
                    onClick={() => navigate(
                      `/coach/athletes/${row.athlete_id}/analysis/${row.video_id}?analysisId=${row.analysis_id}`
                    )}
                  >
                    View Analysis
                  </button>
                </div>
              </article>
            ))}
          </section>
        )}

        {recommendationTarget && (
          <div className="coach-modal-backdrop" role="presentation" onMouseDown={closeRecommendation}>
            <section
              className="coach-modal-card"
              role="dialog"
              aria-modal="true"
              aria-labelledby="coach-recommendation-title"
              onMouseDown={(event) => event.stopPropagation()}
            >
              <div className="coach-section-heading">
                <div>
                  <p className="page-eyebrow">{recommendationTarget.athlete_name}</p>
                  <h2 id="coach-recommendation-title">Recommendation</h2>
                  <p>{recommendationTarget.activity} · {formatDate(recommendationTarget.date)}</p>
                </div>
                <button className="secondary-button compact" type="button" onClick={closeRecommendation}>
                  Close
                </button>
              </div>

              {recommendationMessage && <div className="coach-success-card compact">{recommendationMessage}</div>}
              {recommendationError && <div className="coach-error-card compact">{recommendationError}</div>}

              <form className="coach-form-card coach-modal-form" onSubmit={handleSaveRecommendation}>
                <label className="coach-textarea-field">
                  <span>Recommendation</span>
                  <input
                    value={recommendationForm.title}
                    onChange={(event) => setRecommendationForm({ ...recommendationForm, title: event.target.value })}
                    placeholder="Knee stability exercises"
                  />
                </label>
                <label className="coach-textarea-field">
                  <span>Feedback / Instructions</span>
                  <textarea
                    rows="4"
                    value={recommendationForm.description}
                    onChange={(event) => setRecommendationForm({ ...recommendationForm, description: event.target.value })}
                    placeholder="Focus on controlled knee alignment during landing..."
                  />
                </label>
                <div className="coach-field-grid">
                  <label>
                    <span>Priority</span>
                    <select
                      value={recommendationForm.priority}
                      onChange={(event) => setRecommendationForm({ ...recommendationForm, priority: event.target.value })}
                    >
                      {["LOW", "MEDIUM", "HIGH"].map((priority) => (
                        <option key={priority} value={priority}>{formatStatus(priority)}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Target / Due Date</span>
                    <input
                      type="date"
                      value={recommendationForm.due_date}
                      onChange={(event) => setRecommendationForm({ ...recommendationForm, due_date: event.target.value })}
                    />
                  </label>
                </div>
                <div className="coach-form-actions">
                  <button
                    className="primary-button"
                    type="submit"
                    disabled={recommendationSaving || !recommendationForm.title.trim()}
                  >
                    {recommendationSaving ? "Saving..." : "Save Recommendation"}
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}

        {!loading && !error && visibleRows.length > 0 && type !== "analyses" && (
          <section className="coach-table-card">
            <div className="coach-athlete-table coach-athlete-table-head">
              <span>Athlete</span>
              <span>{type === "videos" ? "Video" : "Report"}</span>
              <span>Date</span>
              <span>Status</span>
              <span>Risk</span>
              <span>Action</span>
            </div>

            {visibleRows.map((row) => (
              <article className="coach-athlete-table" key={`${type}-${row.id}`}>
                <div className="coach-athlete-cell athlete">
                  <div className="coach-icon-box">
                    <Icon size={19} />
                  </div>
                  <div>
                    <strong>{row.athlete_name}</strong>
                  </div>
                </div>
                <span className="coach-muted-cell">{row.activity}</span>
                <span className="coach-muted-cell">{formatDate(row.date)}</span>
                <span className="coach-connected-badge active">{row.status}</span>
                <span className={`coach-risk-text ${riskClass(row.risk_category)}`}>
                  {row.risk_category || "Not Available"}
                </span>
                <div className="coach-report-actions">
                  {type === "videos" && (
                    <button
                      className="secondary-button compact"
                      type="button"
                      onClick={() => navigate(`/coach/athletes/${row.athlete_id}/videos`)}
                    >
                      View Video
                    </button>
                  )}

                  {type === "reports" && (
                    <>
                      <button
                        className="secondary-button compact"
                        type="button"
                        disabled={!row.pdf_report_available}
                        onClick={() => handleDownload(row, "pdf")}
                      >
                        <Download size={15} />
                        PDF
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </section>
        )}
    </main>
  );
}


export default CoachResourceList;
