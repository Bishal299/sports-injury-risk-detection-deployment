import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, BarChart3, Download, FileText, GitCompareArrows, Play, Video } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import {
  downloadPhysiotherapistAthleteReport,
  getPhysiotherapistAthleteDetail,
  resolveApiAssetUrl,
} from "../../services/api";
import "../../styles/analysis.css";
import "../../styles/coach.css";

const keyMetricConfigs = [
  { label: "Knee Valgus", paths: ["knee_valgus", "summary_metrics.knee_valgus.score", "summary_metrics.knee_valgus.risk_score"] },
  { label: "Hip Stability", paths: ["hip_stability", "summary_metrics.hip_stability.score", "summary_metrics.hip_stability.stability_score"] },
  { label: "Trunk Lean", paths: ["trunk_lean", "summary_metrics.trunk_lean.score", "summary_metrics.trunk_lean.trunk_control_score"] },
  { label: "Landing Mechanics", paths: ["summary_metrics.landing.score", "summary_metrics.landing.landing_score", "summary_metrics.landing_mechanics.score", "movement_quality"] },
  { label: "Symmetry", paths: ["symmetry_score", "summary_metrics.symmetry.overall_symmetry_score", "summary_metrics.symmetry.score"] },
  { label: "Stride Asymmetry", paths: ["summary_metrics.stride.stride_asymmetry_pct", "summary_metrics.stride.asymmetry_score", "asymmetry_score"] },
  { label: "Balance", paths: ["summary_metrics.balance.score", "summary_metrics.balance.balance_score"] },
];

const detailSections = [
  { title: "Force Estimation", paths: ["summary_metrics.force", "summary_metrics.force_estimation"] },
  { title: "Joint Angle Details", paths: ["summary_metrics.joint_angles"] },
  { title: "Data Quality", paths: ["summary_metrics.feature_quality", "summary_metrics.data_quality"] },
  {
    title: "Other Detailed Biomechanical Information",
    paths: [
      "summary_metrics.posture",
      "summary_metrics.alignment",
      "summary_metrics.stride",
      "summary_metrics.balance",
      "summary_metrics.knee_valgus",
      "summary_metrics.hip_stability",
      "summary_metrics.trunk_lean",
      "summary_metrics.landing",
    ],
  },
];

const importantComparisonMetrics = new Set([
  "knee_valgus",
  "hip_stability",
  "trunk_lean",
  "landing_mechanics",
  "stride",
  "symmetry",
  "movement_quality",
]);

const jointAngleFields = new Set([
  "current_angle",
  "min_angle",
  "max_angle",
  "avg_angle",
  "rom",
]);

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatLabel(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replaceAll(".", " ")
    .toLowerCase()
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
    if (value !== null && value !== undefined && value !== "") return value;
  }
  return null;
}

function isScalar(value) {
  return typeof value === "number" || typeof value === "string" || typeof value === "boolean";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not Available";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function flattenScalars(value, prefix = "") {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];

  return Object.entries(value).flatMap(([key, entry]) => {
    const nextKey = prefix ? `${prefix}.${key}` : key;
    if (isScalar(entry)) return [{ key: nextKey, label: formatLabel(nextKey), value: entry }];
    if (entry && typeof entry === "object" && !Array.isArray(entry)) return flattenScalars(entry, nextKey);
    return [];
  });
}

function getAnalysisScore(analysis) {
  if (!analysis) return null;
  return analysis.composite_risk_score ?? analysis.overall_risk_score ?? null;
}

function getSelectedVideo(videos, analysis) {
  if (!analysis) return null;
  return videos.find((video) => video.video_id === analysis.video_id) || null;
}

function buildKeyMetrics(analysis) {
  return keyMetricConfigs.map((metric) => ({
    ...metric,
    value: firstExisting(analysis, metric.paths),
  }));
}

function uniqueDetailRows(paths, analysis) {
  const seen = new Set();
  return paths.flatMap((path) => flattenScalars(getPath(analysis, path))).filter((row) => {
    const key = `${row.label}:${row.value}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildJointAngleRows(analysis) {
  const summary = getPath(analysis, "summary_metrics.joint_angles.summary");
  if (!summary || typeof summary !== "object") return [];

  return Object.entries(summary).flatMap(([jointName, jointValues]) => {
    if (!jointValues || typeof jointValues !== "object" || Array.isArray(jointValues)) return [];

    return Object.entries(jointValues)
      .filter(([field, value]) => jointAngleFields.has(field) && value !== null && value !== undefined && value !== "")
      .map(([field, value]) => ({
        key: `${jointName}.${field}`,
        label: `${formatLabel(jointName)} ${formatLabel(field)}`,
        value: typeof value === "number" ? `${formatValue(value)}°` : value,
      }));
  });
}

function getDetailRows(section, analysis) {
  if (section.title === "Joint Angle Details") {
    return buildJointAngleRows(analysis);
  }

  return uniqueDetailRows(section.paths, analysis);
}

function PhysiotherapistMovementAnalytics() {
  const { athleteId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reportError, setReportError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadAnalytics() {
      setLoading(true);
      setError("");
      try {
        const data = await getPhysiotherapistAthleteDetail(athleteId);
        if (cancelled) return;

        const analyses = Array.isArray(data.analyses) ? data.analyses : [];
        setDetail(data);
        setSelectedAnalysisId(analyses[0]?.analysis_id || "");
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load movement analytics.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAnalytics();
    return () => {
      cancelled = true;
    };
  }, [athleteId]);

  const analyses = Array.isArray(detail?.analyses) ? detail.analyses : [];
  const videos = Array.isArray(detail?.videos) ? detail.videos : [];
  const selectedAnalysis = analyses.find((analysis) => analysis.analysis_id === selectedAnalysisId) || analyses[0] || null;
  const selectedVideo = getSelectedVideo(videos, selectedAnalysis);
  const keyMetrics = useMemo(() => buildKeyMetrics(selectedAnalysis), [selectedAnalysis]);
  const comparison = detail?.movement_comparison?.comparison || {};
  const comparisonRows = Object.entries(comparison).filter(([metric]) => importantComparisonMetrics.has(metric));
  const comparisonStatus = detail?.movement_comparison?.comparison_status || "No Analysis";
  const riskScore = getAnalysisScore(selectedAnalysis);
  const videoUrl = resolveApiAssetUrl(selectedVideo?.video_url);

  async function handleDownloadReport() {
    if (!selectedAnalysis?.video_id) return;
    setDownloading(true);
    setReportError("");
    try {
      await downloadPhysiotherapistAthleteReport(athleteId, selectedAnalysis.video_id, "pdf");
    } catch (error) {
      setReportError(error.message || "Failed to download report.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <main className="coach-page">
      <button className="coach-back-button" type="button" onClick={() => navigate("/physiotherapist/movement-analytics")}>
        <ArrowLeft size={18} />
        Back to Movement Analytics
      </button>

      <section className="coach-page-header coach-page-header-row">
        <div>
          <p className="page-eyebrow">MOVEMENT ANALYTICS</p>
          <h1>{detail?.profile?.name || "Athlete Analytics"}</h1>
          <p>{detail?.profile?.sport || "Sport not set"}</p>
        </div>
        <BarChart3 size={28} />
      </section>

      {error && <section className="coach-error-card">{error}</section>}
      {loading && <section className="coach-empty-card">Loading movement analytics...</section>}

      {!loading && !error && analyses.length === 0 && (
        <section className="coach-empty-card">
          <h2>No movement analytics available.</h2>
          <p>This connected athlete does not have stored analysis results yet.</p>
        </section>
      )}

      {!loading && !error && selectedAnalysis && (
        <>
          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Video / Selected Analysis</h2>
                <p>Existing uploaded video and stored analysis record.</p>
              </div>
            </div>
            <div className="coach-field-grid">
              <label>
                <span>Analysis / Video</span>
                <select value={selectedAnalysis.analysis_id} onChange={(event) => setSelectedAnalysisId(event.target.value)}>
                  {analyses.map((analysis) => (
                    <option key={analysis.analysis_id} value={analysis.analysis_id}>
                      {(analysis.video_activity || "Movement Analysis")} - {formatDate(analysis.completed_at || analysis.analysis_date)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {videoUrl ? (
              <div className="video-card-container" style={{ marginTop: "14px" }}>
                <div className="video-card-header">
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Video size={18} color="var(--accent)" />
                    <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                      {selectedVideo?.activity || selectedAnalysis.video_activity || "Selected Video"}
                    </span>
                  </div>
                </div>
                <div className="video-player-wrapper">
                  <video controls playsInline preload="metadata" src={videoUrl} />
                </div>
              </div>
            ) : (
              <div className="coach-quiet-state">Video playback is not available for this record.</div>
            )}
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Analysis Summary</h2>
                <p>Primary stored analysis values.</p>
              </div>
            </div>
            <div className="coach-performance-grid">
              <div className="coach-metric-card"><span>Analysis / Video</span><strong>{selectedVideo?.activity || selectedAnalysis.video_activity || "Not Available"}</strong></div>
              <div className="coach-metric-card"><span>Date</span><strong>{formatDate(selectedAnalysis.completed_at || selectedAnalysis.analysis_date)}</strong></div>
              <div className="coach-metric-card"><span>Status</span><strong>{formatLabel(selectedAnalysis.status)}</strong></div>
              <div className="coach-metric-card"><span>Risk Score</span><strong>{formatValue(riskScore)}</strong></div>
              <div className="coach-metric-card"><span>Risk Category</span><strong>{selectedAnalysis.risk_category || "Not Available"}</strong></div>
              <div className="coach-metric-card"><span>Movement Quality</span><strong>{formatValue(selectedAnalysis.movement_quality)}</strong></div>
            </div>
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Key Movement Metrics</h2>
                <p>Curated biomechanical values from the stored result.</p>
              </div>
            </div>
            <div className="coach-performance-grid">
              {keyMetrics.map((metric) => (
                <div className="coach-metric-card" key={metric.label}>
                  <span>{metric.label}</span>
                  <strong>{formatValue(metric.value)}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Initial -&gt; Latest Movement Comparison</h2>
                <p>Mathematical change between compatible stored analyses.</p>
              </div>
              <GitCompareArrows size={22} />
            </div>
            {comparisonRows.length === 0 ? (
              <div className="coach-quiet-state">{comparisonStatus || "No Previous Assessment"}</div>
            ) : (
              <section className="coach-table-card">
                <div className="coach-athlete-table coach-athlete-table-head"><span>Metric</span><span>Initial</span><span>Latest</span><span>Change</span><span></span><span></span></div>
                {comparisonRows.map(([metric, values]) => (
                  <article className="coach-athlete-table" key={metric}>
                    <strong>{formatLabel(metric)}</strong>
                    <span>{formatValue(values.initial)}</span>
                    <span>{formatValue(values.latest)}</span>
                    <span>{formatValue(values.change)}</span>
                    <span></span>
                    <span></span>
                  </article>
                ))}
              </section>
            )}
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Additional Analysis</h2>
                <p>Technical details are collapsed by default.</p>
              </div>
            </div>
            {detailSections.map((section) => {
              const rows = getDetailRows(section, selectedAnalysis);
              if (rows.length === 0) return null;
              return (
                <details className="coach-form-card" key={section.title}>
                  <summary>{section.title}</summary>
                  <div className="coach-performance-grid" style={{ marginTop: "12px" }}>
                    {rows.map((row) => (
                      <div className="coach-metric-card" key={`${section.title}-${row.key}`}>
                        <span>{row.label}</span>
                        <strong>{formatValue(row.value)}</strong>
                      </div>
                    ))}
                  </div>
                </details>
              );
            })}
          </section>

          <section className="coach-panel-card">
            <div className="coach-section-heading">
              <div>
                <h2>Full Analysis Report</h2>
                <p>Open the detailed analysis workspace or download the existing report.</p>
              </div>
              <FileText size={22} />
            </div>
            {reportError && <section className="coach-error-card">{reportError}</section>}
            <div className="coach-report-actions">
              <button
                className="secondary-button compact"
                type="button"
                onClick={() => navigate(`/physiotherapist/athletes/${athleteId}/videos/${selectedAnalysis.video_id}/analysis?analysisId=${selectedAnalysis.analysis_id}`)}
              >
                <Play size={15} />
                Open Full Analysis
              </button>
              <button
                className="secondary-button compact"
                type="button"
                onClick={handleDownloadReport}
                disabled={downloading || !selectedAnalysis.pdf_report_available}
                title={selectedAnalysis.pdf_report_available ? "Download existing PDF report" : "PDF report is not available for this analysis"}
              >
                <Download size={15} />
                {downloading ? "Downloading..." : "PDF Report"}
              </button>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

export default PhysiotherapistMovementAnalytics;
