import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import {
  downloadCoachAthleteReport,
  downloadPhysiotherapistAthleteReport,
  getVideoDetails,
  getCoachAthleteAnalysis,
  getCoachAthleteDetail,
  getPhysiotherapistAthleteDetail,
  getPhysiotherapistAthleteVideoAnalysis,
  triggerMovementAnalysis,
  getMovementAnalysisStatus,
  getMovementAnalysisResult,
  getAnalysisById,
  downloadReportFile
} from "../../services/api";

import {
  Activity,
  ArrowLeft,
  RefreshCw,
  Play,
  Pause,
  Maximize,
  Download,
  FileText,
  Table as TableIcon,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldAlert,
  Scale,
  Compass,
  Zap,
  TrendingUp,
  Award
} from "lucide-react";

import "../../styles/analysis.css";


function SvgTimeSeriesChart({ data, timeline, label, unit = "°", color = "#2563eb", minVal = null, maxVal = null, threshold = null }) {
  const [hoverIndex, setHoverIndex] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="svg-chart-container" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>Insufficient time-series data</p>
      </div>
    );
  }

  const validVals = data.filter(v => v !== null && !isNaN(v));
  if (validVals.length === 0) {
    return (
      <div className="svg-chart-container" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>No valid points recorded</p>
      </div>
    );
  }

  const dataMin = minVal !== null ? minVal : Math.min(...validVals);
  const dataMax = maxVal !== null ? maxVal : Math.max(...validVals);
  const padding = Math.max(2, (dataMax - dataMin) * 0.15);
  const yMin = Math.max(0, dataMin - padding);
  const yMax = dataMax + padding;
  const yRange = yMax - yMin || 1;

  const width = 600;
  const height = 200;
  const margin = { top: 20, right: 30, bottom: 25, left: 45 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const points = data.map((val, idx) => {
    if (val === null || isNaN(val)) return null;
    const x = margin.left + (idx / (data.length - 1 || 1)) * innerW;
    const y = margin.top + innerH - ((val - yMin) / yRange) * innerH;
    return { x, y, val, time: timeline ? timeline[idx] : (idx * 0.033).toFixed(2) };
  });

  // Construct SVG path
  let pathD = "";
  let areaD = "";
  let firstPoint = null;
  let lastPoint = null;

  points.forEach((p) => {
    if (p) {
      if (!pathD) {
        pathD = `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
        areaD = `M ${p.x.toFixed(1)} ${margin.top + innerH} L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
        firstPoint = p;
      } else {
        pathD += ` L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
        areaD += ` L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
      }
      lastPoint = p;
    }
  });

  if (lastPoint && firstPoint) {
    areaD += ` L ${lastPoint.x.toFixed(1)} ${margin.top + innerH} Z`;
  }

  const yTicks = [yMin, yMin + yRange * 0.33, yMin + yRange * 0.66, yMax];

  return (
    <div className="svg-chart-container" style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${width} ${height}`} className="svg-chart" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`grad-${label.replace(/\s+/g, '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Gridlines & Y labels */}
        {yTicks.map((tick, i) => {
          const yPos = margin.top + innerH - ((tick - yMin) / yRange) * innerH;
          return (
            <g key={i}>
              <line x1={margin.left} y1={yPos} x2={width - margin.right} y2={yPos} className="chart-axis-line" />
              <text x={margin.left - 8} y={yPos + 3} textAnchor="end" className="chart-axis-label">
                {tick.toFixed(0)}{unit}
              </text>
            </g>
          );
        })}

        {/* Threshold Line if present */}
        {threshold !== null && (
          <line
            x1={margin.left}
            y1={margin.top + innerH - ((threshold - yMin) / yRange) * innerH}
            x2={width - margin.right}
            y2={margin.top + innerH - ((threshold - yMin) / yRange) * innerH}
            stroke="#ef4444"
            strokeWidth="1.5"
            strokeDasharray="6 3"
          />
        )}

        {/* Area fill & curve path */}
        {areaD && <path d={areaD} fill={`url(#grad-${label.replace(/\s+/g, '')})`} />}
        {pathD && <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />}

        {/* Hover overlay points */}
        {points.map((p, idx) => {
          if (!p) return null;
          return (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r={hoverIndex === idx ? 5 : 2.5}
              fill={hoverIndex === idx ? "#fff" : color}
              stroke={color}
              strokeWidth={hoverIndex === idx ? 2 : 1}
              style={{ cursor: "pointer", transition: "r 0.15s ease" }}
              onMouseEnter={() => setHoverIndex(idx)}
              onMouseLeave={() => setHoverIndex(null)}
            />
          );
        })}
      </svg>

      {/* Floating Hover Tooltip */}
      {hoverIndex !== null && points[hoverIndex] && (
        <div
          style={{
            position: "absolute",
            left: `${(points[hoverIndex].x / width) * 100}%`,
            top: `${(points[hoverIndex].y / height) * 100}%`,
            transform: "translate(-50%, -120%)",
            background: "rgba(15, 23, 42, 0.9)",
            color: "#fff",
            padding: "4px 8px",
            borderRadius: "6px",
            fontSize: "0.75rem",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
            zIndex: 10
          }}
        >
          <strong>{points[hoverIndex].val.toFixed(1)}{unit}</strong> at {points[hoverIndex].time}s
        </div>
      )}
    </div>
  );
}


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const formatMediaUrl = (url) => {
  if (!url) return "";
  const clean = url.replace(/\\/g, "/");
  if (clean.startsWith("http://") || clean.startsWith("https://")) {
    return clean;
  }
  const normalizedPath = clean.startsWith("/") ? clean : `/${clean}`;
  return `${API_BASE_URL}${normalizedPath}`;
};


function Analysis({ viewer = "athlete" }) {
  const { videoId, athleteId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const analysisId = searchParams.get("analysisId");
  const isCoachView = viewer === "coach";
  const isPhysiotherapistView = viewer === "physiotherapist";
  const isProfessionalView = isCoachView || isPhysiotherapistView;

  const [video, setVideo] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("loading"); // loading, processing, completed, failed
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Preparing video...");
  const [error, setError] = useState("");

  const [activeTab, setActiveTab] = useState("overview");
  const [videoMode, setVideoMode] = useState("skeleton"); // skeleton, original, split
  const [selectedSide, setSelectedSide] = useState("right");
  const [selectedJoint, setSelectedJoint] = useState("knee");
  const [downloadingFile, setDownloadingFile] = useState(null);

  const videoRef = useRef(null);
  const splitOrigRef = useRef(null);
  const splitSkelRef = useRef(null);
  const syncingSplitVideosRef = useRef(false);

  // 1. Initial Load & Polling Logic
  useEffect(() => {
    let intervalId = null;

    const initAnalysis = async () => {
      try {
        setError("");
        if (isProfessionalView) {
          const detail = isPhysiotherapistView
            ? await getPhysiotherapistAthleteDetail(athleteId)
            : await getCoachAthleteDetail(athleteId);
          const vidData = detail.videos?.find((item) => item.video_id === videoId);

          if (!vidData) {
            throw new Error("Video not found or access unauthorized");
          }

          setVideo({
            ...vidData,
            athlete: {
              user: {
                name: detail.profile?.name || "Athlete",
              },
            },
          });

          const targetAnalysisId = analysisId || vidData.latest_analysis_id;
          if (!targetAnalysisId) {
            throw new Error("Analysis has not been generated for this video yet.");
          }

          const professionalResult = isPhysiotherapistView
            ? await getPhysiotherapistAthleteVideoAnalysis(athleteId, videoId, targetAnalysisId)
            : await getCoachAthleteAnalysis(athleteId, targetAnalysisId);
          setAnalysis(professionalResult);
          setStatus(professionalResult.status === "completed" ? "completed" : professionalResult.status || "completed");
          setProgress(professionalResult.status === "completed" ? 100 : 0);
          setStage("Connected athlete analysis loaded");
          return;
        }

        const vidData = await getVideoDetails(videoId);
        setVideo(vidData);

        if (analysisId) {
          const historicalResult = await getAnalysisById(analysisId);
          setAnalysis(historicalResult);
          setStatus("completed");
          setProgress(100);
          setStage("Historical analysis loaded");
          return;
        }

        // Check if analysis already exists
        const stat = await getMovementAnalysisStatus(videoId);

        if (stat.status === "completed") {
          const fullResult = await getMovementAnalysisResult(videoId);
          setAnalysis(fullResult);
          setStatus("completed");
          setProgress(100);
          setStage("Analysis complete");
          window.dispatchEvent(new Event("analysis-history-updated"));
        } else if (stat.status === "processing") {
          setStatus("processing");
          setProgress(stat.progress || 15);
          setStage(stat.stage || "Processing video...");
          startPolling();
        } else {
          // Trigger analysis automatically if pending
          setStatus("processing");
          setProgress(10);
          setStage("Initializing analysis pipeline...");
          await triggerMovementAnalysis(videoId);
          startPolling();
        }
      } catch (err) {
        console.error("Init analysis error:", err);
        setError(err.message || "Failed to initialize analysis");
        setStatus("failed");
      }
    };

    const startPolling = () => {
      intervalId = setInterval(async () => {
        try {
          const stat = await getMovementAnalysisStatus(videoId);
          setProgress(stat.progress || 0);
          setStage(stat.stage || "Processing...");

          if (stat.status === "completed") {
            clearInterval(intervalId);
            const fullResult = await getMovementAnalysisResult(videoId);
            setAnalysis(fullResult);
            setStatus("completed");
            setProgress(100);
            setStage("Analysis complete");
            window.dispatchEvent(new Event("analysis-history-updated"));
          } else if (stat.status === "failed") {
            clearInterval(intervalId);
            setStatus("failed");
            setError(stat.error_message || "Video movement processing encountered an error.");
          }
        } catch (pollErr) {
          console.error("Polling error:", pollErr);
        }
      }, 1500);
    };

    initAnalysis();

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [videoId, analysisId, athleteId, isProfessionalView, isPhysiotherapistView]);

  // Re-trigger analysis handler
  const handleRerunAnalysis = async () => {
    if (isProfessionalView) {
      return;
    }

    try {
      setStatus("processing");
      setProgress(5);
      setStage("Re-initializing video pipeline...");
      setError("");
      if (analysisId) {
        navigate(`/analysis/${videoId}`, { replace: true });
      }
      await triggerMovementAnalysis(videoId);

      const interval = setInterval(async () => {
        const stat = await getMovementAnalysisStatus(videoId);
        setProgress(stat.progress || 0);
        setStage(stat.stage || "Processing...");
        if (stat.status === "completed") {
          clearInterval(interval);
          const fullResult = await getMovementAnalysisResult(videoId);
          setAnalysis(fullResult);
          setStatus("completed");
          setProgress(100);
          window.dispatchEvent(new Event("analysis-history-updated"));
        } else if (stat.status === "failed") {
          clearInterval(interval);
          setStatus("failed");
          setError(stat.error_message || "Processing failed");
        }
      }, 1500);
    } catch (err) {
      setError(err.message || "Failed to re-run analysis");
      setStatus("failed");
    }
  };

  const handleDownload = async (fileType) => {
    try {
      setDownloadingFile(fileType);
      if (isProfessionalView) {
        if (fileType !== "pdf") {
          throw new Error("This export is available only to the athlete account.");
        }
        if (isPhysiotherapistView) {
          await downloadPhysiotherapistAthleteReport(athleteId, videoId, fileType);
        } else {
          await downloadCoachAthleteReport(athleteId, videoId, fileType);
        }
      } else {
        await downloadReportFile(videoId, fileType);
      }
    } catch (err) {
      alert("Download failed: " + err.message);
    } finally {
      setDownloadingFile(null);
    }
  };

  // Sync split video players without making the two media elements fight each other.
  const getSplitPartner = (sourceVideo) => {
    if (sourceVideo === splitOrigRef.current) return splitSkelRef.current;
    if (sourceVideo === splitSkelRef.current) return splitOrigRef.current;
    return null;
  };

  const handleSplitPlay = (event) => {
    const partner = getSplitPartner(event.currentTarget);
    if (!partner || syncingSplitVideosRef.current) return;

    syncingSplitVideosRef.current = true;
    if (Math.abs(partner.currentTime - event.currentTarget.currentTime) > 0.25) {
      partner.currentTime = event.currentTarget.currentTime;
    }

    const playPromise = partner.play();
    if (playPromise?.catch) {
      playPromise.catch(() => {});
    }
    window.setTimeout(() => {
      syncingSplitVideosRef.current = false;
    }, 0);
  };

  const handleSplitPause = (event) => {
    const partner = getSplitPartner(event.currentTarget);
    if (!partner || syncingSplitVideosRef.current) return;

    syncingSplitVideosRef.current = true;
    partner.pause();
    window.setTimeout(() => {
      syncingSplitVideosRef.current = false;
    }, 0);
  };

  const handleSplitTimeSync = (event) => {
    const partner = getSplitPartner(event.currentTarget);
    if (!partner || syncingSplitVideosRef.current) return;

    const drift = Math.abs(partner.currentTime - event.currentTarget.currentTime);
    if (drift > 0.3) {
      syncingSplitVideosRef.current = true;
      partner.currentTime = event.currentTarget.currentTime;
      window.setTimeout(() => {
        syncingSplitVideosRef.current = false;
      }, 0);
    }
  };

  // Extract metrics shorthand
  const summary = analysis?.summary_metrics || {};
  const riskAssessment = analysis?.risk_assessment || summary?.risk_assessment || {};
  const valgus = summary.knee_valgus || {};
  const hip = summary.hip_stability || {};
  const trunk = summary.trunk_lean || {};
  const landing = summary.landing || {};
  const stride = summary.stride || {};
  const balance = summary.balance || {};
  const posture = summary.posture || {};
  const symmetry = summary.symmetry || {};
  const joints = summary.joint_angles || {};
  const force = summary.force || summary.force_estimation || {};
  const alignment = summary.alignment || {};
  const recommendations = riskAssessment.recommendations || analysis?.recommendations || [];

  const injuryRiskScore = analysis?.overall_risk_score !== null && analysis?.overall_risk_score !== undefined
    ? Number(analysis.overall_risk_score)
    : (riskAssessment.injury_risk_score !== null && riskAssessment.injury_risk_score !== undefined
      ? Number(riskAssessment.injury_risk_score)
      : null);

  const rawRiskLevel = analysis?.risk_level && analysis.risk_level !== "Phase 1: Feature Extraction Only"
    ? analysis.risk_level
    : (riskAssessment.risk_category || analysis?.risk_category || "Not Available");

  const riskClass = String(rawRiskLevel).toLowerCase().replace(/\s+/g, '-');

  const movementQualityScore = riskAssessment.movement_quality_score !== null && riskAssessment.movement_quality_score !== undefined
    ? Number(riskAssessment.movement_quality_score)
    : (analysis?.movement_quality !== null && analysis?.movement_quality !== undefined ? Number(analysis.movement_quality) : null);
  const biomechanicalEfficiencyScore = riskAssessment.biomechanical_efficiency_score !== null && riskAssessment.biomechanical_efficiency_score !== undefined
    ? Number(riskAssessment.biomechanical_efficiency_score)
    : null;
  const athleteHealthScore = riskAssessment.overall_athlete_health_score !== null && riskAssessment.overall_athlete_health_score !== undefined
    ? Number(riskAssessment.overall_athlete_health_score)
    : null;
  const componentScores = riskAssessment.component_scores || {};
  const riskFactors = riskAssessment.risk_factors || [];

  // Robust formatted Video URLs
  const originalVideoUrl = formatMediaUrl(video?.video_url);
  const skeletonVideoUrl = formatMediaUrl(analysis?.skeleton_video_url) || originalVideoUrl;

  const formatScoreValue = (value) => (
    value !== null && value !== undefined && Number.isFinite(Number(value))
      ? Number(value).toFixed(0)
      : "Not available"
  );


  // Selected joint time series
  const jointKey = `${selectedSide}_${selectedJoint}`;
  const jointSeriesData = analysis?.time_series_data?.joints?.[jointKey] || [];
  const jointTimeline = analysis?.time_series_data?.timeline || [];
  const jointInfo = joints.summary?.[jointKey] || {};
  const LayoutComponent = isProfessionalView ? React.Fragment : DashboardLayout;
  const backPath = isPhysiotherapistView
    ? `/physiotherapist/athletes/${athleteId}/videos`
    : (isCoachView ? `/coach/athletes/${athleteId}` : "/my-videos");
  const firstCrumbPath = isPhysiotherapistView
    ? "/physiotherapist/dashboard"
    : (isCoachView ? "/coach/dashboard" : "/dashboard");
  const firstCrumbLabel = isPhysiotherapistView
    ? "Physiotherapist Dashboard"
    : (isCoachView ? "Coach Dashboard" : "Dashboard");
  const secondCrumbPath = isPhysiotherapistView
    ? `/physiotherapist/athletes/${athleteId}/videos`
    : (isCoachView ? `/coach/athletes/${athleteId}` : "/my-videos");
  const secondCrumbLabel = isPhysiotherapistView
    ? "Athlete Videos"
    : (isCoachView ? "Connected Athlete" : "My Videos");

  return (
    <LayoutComponent>
      <div className="analysis-page">
        {/* Breadcrumb Navigation */}
        <div className="analysis-breadcrumbs">
          <span onClick={() => navigate(firstCrumbPath)}>{firstCrumbLabel}</span>
          <span>/</span>
          <span onClick={() => navigate(secondCrumbPath)}>{secondCrumbLabel}</span>
          <span>/</span>
          <span className="crumb-active">Movement Analysis</span>
        </div>

        {/* Page Header */}
        <div className="analysis-header-row">
          <div className="analysis-title-group">
            <p className="page-eyebrow">AI MOVEMENT PIPELINE</p>
            <h1>Movement Analysis</h1>
            <div className="analysis-meta-chips">
              <div className="meta-chip">
                <strong>Athlete:</strong> {video?.athlete?.user?.name || "Athlete"}
              </div>
              <div className="meta-chip">
                <strong>Activity:</strong> {video?.activity || "Not available"}
              </div>
              {video?.duration && (
                <div className="meta-chip">
                  <strong>Duration:</strong> {Number(video.duration).toFixed(1)}s{video.fps ? ` (${video.fps} fps)` : ""}
                </div>
              )}
              {summary.feature_quality?.pose_detection_rate !== undefined && (
                <div className="meta-chip">
                  <strong>Skeleton Tracking:</strong> {summary.feature_quality.valid_pose_frames}/{summary.feature_quality.total_frames} frames ({summary.feature_quality.pose_detection_rate}%)
                </div>
              )}
              <div className={`status-badge ${status}`}>
                <span className="pulse-dot"></span>
                {status === "completed" ? (analysisId ? "Historical Record" : "Analysis Complete") : (status === "processing" ? "Processing Video" : status)}
              </div>
            </div>
          </div>

          <div className="analysis-header-actions">
            <button className="secondary-button" onClick={() => navigate(backPath)}>
              <ArrowLeft size={16} />
              <span>{isPhysiotherapistView ? "Back to Athlete Videos" : (isCoachView ? "Back to Athlete" : "Back to Videos")}</span>
            </button>
            {status === "completed" && !analysisId && !isProfessionalView && (
              <button className="secondary-button" onClick={handleRerunAnalysis}>
                <RefreshCw size={16} />
                <span>Re-run Analysis</span>
              </button>
            )}
          </div>
        </div>

        {/* Processing State Card */}
        {status === "processing" && (
          <div className="processing-card">
            <Activity size={36} color="var(--accent)" style={{ animation: "pulseAnimation 1.5s infinite" }} />
            <h3 style={{ margin: "14px 0 6px", fontSize: "1.3rem", color: "var(--text-primary)" }}>
              Analyzing Sports Movement
            </h3>
            <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              {stage}
            </p>

            <div className="processing-progress-bar">
              <div className="processing-progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--accent)" }}>
              {progress}% Complete
            </span>

            <div className="processing-stages-list">
              <div className={`processing-stage-item ${progress >= 15 ? 'completed' : (progress > 0 ? 'active' : '')}`}>
                ✓ Preparing Video
              </div>
              <div className={`processing-stage-item ${progress >= 35 ? 'completed' : (progress >= 15 ? 'active' : '')}`}>
                ✓ Pose Landmark Extraction
              </div>
              <div className={`processing-stage-item ${progress >= 60 ? 'completed' : (progress >= 35 ? 'active' : '')}`}>
                ✓ Joint Angles & Kinematics
              </div>
              <div className={`processing-stage-item ${progress >= 75 ? 'completed' : (progress >= 60 ? 'active' : '')}`}>
                ✓ Balance & Symmetry
              </div>
              <div className={`processing-stage-item ${progress >= 90 ? 'completed' : (progress >= 75 ? 'active' : '')}`}>
                ✓ Virtual Skeleton Rendering
              </div>
              <div className={`processing-stage-item ${progress >= 100 ? 'completed' : (progress >= 90 ? 'active' : '')}`}>
                ✓ Reports Generation
              </div>
            </div>
          </div>
        )}

        {/* Error / Failed State Card */}
        {status === "failed" && (
          <div className="processing-card" style={{ borderColor: "var(--danger)" }}>
            <AlertTriangle size={36} color="var(--danger)" />
            <h3 style={{ margin: "12px 0 6px", color: "var(--danger)" }}>Movement Analysis Encountered an Issue</h3>
            <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>{error}</p>
            {isProfessionalView ? (
              <button className="secondary-button" onClick={() => navigate(backPath)}>
                <ArrowLeft size={16} />
                Back to Athlete Videos
              </button>
            ) : (
              <button className="primary-button" onClick={handleRerunAnalysis}>
                <RefreshCw size={16} />
                Retry Analysis
              </button>
            )}
          </div>
        )}

        {/* Completed Main Dashboard */}
        {status === "completed" && analysis && (
          <>
            {/* Top Section: Dual Video Viewer & Executive Score Card */}
            <div className="analysis-top-grid">
              {/* Video Player */}
              <div className="video-card-container">
                <div className="video-card-header">
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Activity size={18} color="var(--accent)" />
                    <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                      Movement Playback
                    </span>
                  </div>

                  <div className="video-mode-toggles">
                    <button
                      className={`mode-toggle-btn ${videoMode === 'skeleton' ? 'active' : ''}`}
                      onClick={() => setVideoMode('skeleton')}
                    >
                      Skeleton
                    </button>
                    <button
                      className={`mode-toggle-btn ${videoMode === 'original' ? 'active' : ''}`}
                      onClick={() => setVideoMode('original')}
                    >
                      Original
                    </button>
                    <button
                      className={`mode-toggle-btn ${videoMode === 'split' ? 'active' : ''}`}
                      onClick={() => setVideoMode('split')}
                    >
                      Side by Side
                    </button>
                  </div>
                </div>

                <div className="video-player-wrapper">
                  {videoMode === 'split' ? (
                    <div className="split-video-wrapper">
                      <div className="split-video-pane">
                        <span className="split-pane-label">ORIGINAL</span>
                        <video
                          ref={splitOrigRef}
                          src={originalVideoUrl}
                          controls
                          playsInline
                          preload="metadata"
                          onPlay={handleSplitPlay}
                          onPause={handleSplitPause}
                          onTimeUpdate={handleSplitTimeSync}
                          onSeeking={handleSplitTimeSync}
                          style={{ width: "100%", height: "100%", objectFit: "contain" }}
                        />
                      </div>
                      <div className="split-video-pane">
                        <span className="split-pane-label">AI SKELETON</span>
                        <video
                          ref={splitSkelRef}
                          src={skeletonVideoUrl}
                          controls
                          playsInline
                          preload="metadata"
                          onPlay={handleSplitPlay}
                          onPause={handleSplitPause}
                          onTimeUpdate={handleSplitTimeSync}
                          onSeeking={handleSplitTimeSync}
                          style={{ width: "100%", height: "100%", objectFit: "contain" }}
                        />
                      </div>
                    </div>
                  ) : (
                    <>
                      <video
                        ref={videoRef}
                        src={videoMode === 'skeleton' ? skeletonVideoUrl : originalVideoUrl}
                        controls
                        playsInline
                        preload="metadata"
                        key={videoMode}
                      />
                      <div className="video-hud-overlay">
                        <span className="hud-badge">
                          {videoMode === 'skeleton' ? 'POSE LANDMARKS (33 JOINTS) ACTIVE' : 'HIGH-SPEED FOOTAGE'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Restored Executive Injury Risk Dashboard Card */}
              <div className="score-card-container">
                {/* 1. Hero Injury Risk Box */}
                <div className={`risk-hero-box ${riskClass}`}>
                  <span className="risk-hero-eyebrow">INJURY RISK DETECTION</span>
                  <div className={`risk-hero-number ${riskClass}`}>
                    {formatScoreValue(injuryRiskScore)} {injuryRiskScore !== null && injuryRiskScore !== undefined && <span style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-muted)" }}>/ 100</span>}
                  </div>
                  <div className={`risk-category-badge ${riskClass}`}>
                    <ShieldAlert size={14} />
                    <span>{rawRiskLevel.toUpperCase()}</span>
                  </div>
                </div>

                {/* 2. Tri-score Row: Movement Quality, Biomechanical Efficiency, Athlete Health */}
                <div className="subscores-trio-grid">
                  <div className="subscore-card">
                    <span className="subscore-label">Movement Quality</span>
                    <span className="subscore-val">{formatScoreValue(movementQualityScore)}{movementQualityScore !== null && movementQualityScore !== undefined && <small style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/100</small>}</span>
                  </div>
                  <div className="subscore-card">
                    <span className="subscore-label">Bio-Efficiency</span>
                    <span className="subscore-val">{formatScoreValue(biomechanicalEfficiencyScore)}{biomechanicalEfficiencyScore !== null && biomechanicalEfficiencyScore !== undefined && <small style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/100</small>}</span>
                  </div>
                  <div className="subscore-card">
                    <span className="subscore-label">Athlete Health</span>
                    <span className="subscore-val">{formatScoreValue(athleteHealthScore)}{athleteHealthScore !== null && athleteHealthScore !== undefined && <small style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/100</small>}</span>
                  </div>
                </div>

                {/* 3. Top Risk Factors */}
                <div className="risk-factors-container">
                  <div className="risk-factors-title">
                    <AlertTriangle size={14} color="#ea580c" />
                    <span>Top Identified Risk Factors</span>
                  </div>
                  {riskFactors && riskFactors.length > 0 ? (
                    riskFactors.slice(0, 3).map((rf, idx) => (
                      <div key={idx} className="risk-factor-item">
                        <div className="risk-factor-left">
                          <span className={`side-pill ${rf.side?.toLowerCase() || 'general'}`}>
                            {rf.side || 'General'}
                          </span>
                          <span style={{ fontWeight: 650, color: "var(--text-primary)" }}>
                            {rf.factor}
                          </span>
                        </div>
                        <span className={`sev-tag ${rf.severity?.toLowerCase() || 'moderate'}`}>
                          {rf.severity || 'Moderate'}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", fontStyle: "italic", padding: "4px 0" }}>
                      No critical or elevated risk factors identified.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Interactive Tabs Navigation */}
            <div className="analysis-tabs-bar">
              <button
                className={`tab-nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                <Award size={16} />
                <span>Overview</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'joints' ? 'active' : ''}`}
                onClick={() => setActiveTab('joints')}
              >
                <Activity size={16} />
                <span>Joint Analysis</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'symmetry' ? 'active' : ''}`}
                onClick={() => setActiveTab('symmetry')}
              >
                <Scale size={16} />
                <span>Movement Symmetry</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'posture' ? 'active' : ''}`}
                onClick={() => setActiveTab('posture')}
              >
                <Compass size={16} />
                <span>Posture & Balance</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'mechanics' ? 'active' : ''}`}
                onClick={() => setActiveTab('mechanics')}
              >
                <TrendingUp size={16} />
                <span>Movement Metrics</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'force' ? 'active' : ''}`}
                onClick={() => setActiveTab('force')}
              >
                <Zap size={16} />
                <span>Force Estimation</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
                onClick={() => setActiveTab('recommendations')}
              >
                <Award size={16} />
                <span>Targeted Drills ({recommendations.length})</span>
              </button>
              <button
                className={`tab-nav-btn ${activeTab === 'reports' ? 'active' : ''}`}
                onClick={() => setActiveTab('reports')}
              >
                <FileText size={16} />
                <span>{isProfessionalView ? "Reports" : "Reports & CSV"}</span>
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {activeTab === 'overview' && (
              <div className="tab-panel">
                <div className="overview-grid">
                  <div className="overview-card">
                    <div className="overview-card-top">
                      <span className="overview-card-title">Knee Valgus</span>
                      <span className={`table-status-badge ${valgus.max_deviation < 5 ? 'optimal' : (valgus.max_deviation < 12 ? 'mild' : 'moderate')}`}>
                        {valgus.overall_risk || 'Normal'}
                      </span>
                    </div>
                    <div className="overview-card-value">{valgus.max_deviation?.toFixed(1) || 0}°</div>
                    <p className="overview-card-desc">
                      Right: {valgus.right?.risk || "Normal"} ({valgus.right?.max_deviation?.toFixed(1)}°) | Left: {valgus.left?.risk || "Normal"} ({valgus.left?.max_deviation?.toFixed(1)}°)
                    </p>
                  </div>

                  <div className="overview-card">
                    <div className="overview-card-top">
                      <span className="overview-card-title">Hip Stability</span>
                      <span className={`table-status-badge ${hip.score >= 80 ? 'optimal' : 'mild'}`}>
                        {hip.score >= 80 ? 'Stable' : 'Moderate Tilt'}
                      </span>
                    </div>
                    <div className="overview-card-value">{hip.score?.toFixed(0) || 85} <small style={{ fontSize: "0.85rem" }}>/100</small></div>
                    <p className="overview-card-desc">
                      Average pelvic tilt {hip.avg_pelvic_tilt_deg?.toFixed(1)}° with {hip.pelvic_displacement_range?.toFixed(2)} displacement range.
                    </p>
                  </div>

                  <div className="overview-card">
                    <div className="overview-card-top">
                      <span className="overview-card-title">Landing Mechanics</span>
                      <span className={`table-status-badge ${landing.has_landing_data ? 'optimal' : 'mild'}`}>
                        {landing.has_landing_data ? `${landing.score}/100` : 'No Impact Event'}
                      </span>
                    </div>
                    <div className="overview-card-value">
                      {landing.has_landing_data ? `${landing.score}/100` : 'Insufficient visual data'}
                    </div>
                    <p className="overview-card-desc">
                      {landing.has_landing_data ? `Knee absorption: ${landing.submetrics?.knee_absorption}, Hip: ${landing.submetrics?.hip_absorption}` : 'Standard locomotion or upper body session.'}
                    </p>
                  </div>

                  <div className="overview-card">
                    <div className="overview-card-top">
                      <span className="overview-card-title">Stride Kinematics</span>
                      <span className="table-status-badge optimal">Normalized</span>
                    </div>
                    <div className="overview-card-value">{stride.normalized_stride_length?.toFixed(2) || '0.50'}</div>
                    <p className="overview-card-desc">
                      Stride asymmetry: {stride.stride_asymmetry_pct?.toFixed(1) || 0}% (Normalized to body height proxy).
                    </p>
                  </div>
                </div>

                {/* Biomechanical Feature Extraction Summary & Disclaimer */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <h3>Kinematic Feature Extraction Summary</h3>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      Derived from frame-by-frame 2D/3D pose estimation
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px", marginTop: "10px" }}>
                    <div className="mini-metric-box" style={{ padding: "16px" }}>
                      <strong style={{ fontSize: "0.92rem", color: "var(--text-primary)", display: "block", marginBottom: "4px" }}>Frontal Plane Alignment</strong>
                      <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                        Right knee valgus max deviation: {valgus.right?.max_deviation?.toFixed(1) || 0}° | Left knee valgus max deviation: {valgus.left?.max_deviation?.toFixed(1) || 0}°.
                      </p>
                    </div>
                    <div className="mini-metric-box" style={{ padding: "16px" }}>
                      <strong style={{ fontSize: "0.92rem", color: "var(--text-primary)", display: "block", marginBottom: "4px" }}>Pelvic & Lumbar Stability</strong>
                      <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                        Average pelvic tilt {hip.avg_pelvic_tilt_deg?.toFixed(1) || 0}° with {hip.pelvic_displacement_range?.toFixed(2) || 0} vertical displacement range.
                      </p>
                    </div>
                    <div className="mini-metric-box" style={{ padding: "16px" }}>
                      <strong style={{ fontSize: "0.92rem", color: "var(--text-primary)", display: "block", marginBottom: "4px" }}>Bilateral Symmetry</strong>
                      <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                        Kinematic symmetry rating of {symmetry.overall_symmetry_score || 90}% calculated across corresponding right and left joints.
                      </p>
                    </div>
                  </div>

                  {/* Medical Safety Disclaimer */}
                  <div className="disclaimer-box" style={{ marginTop: "18px" }}>
                    <strong>Biomechanical Note:</strong> This video-based movement analysis extracts kinematic features and estimated joint angles for performance review. It is not a clinical diagnostic tool and is not a replacement for medical evaluation or force-plate measurement.
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: JOINT ANALYSIS */}
            {activeTab === 'joints' && (
              <div className="tab-panel">
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Interactive Joint Angle & Range of Motion (ROM)</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Time-series 3D/2D joint angle timeline throughout recorded movement frames
                      </p>
                    </div>

                    <div className="chart-controls-bar">
                      {/* Side Selector */}
                      <div className="chart-btn-group">
                        <button
                          className={`chart-select-btn ${selectedSide === 'right' ? 'active' : ''}`}
                          onClick={() => setSelectedSide('right')}
                        >
                          Right Side
                        </button>
                        <button
                          className={`chart-select-btn ${selectedSide === 'left' ? 'active' : ''}`}
                          onClick={() => setSelectedSide('left')}
                        >
                          Left Side
                        </button>
                      </div>

                      {/* Joint Selector */}
                      <div className="chart-btn-group">
                        {['knee', 'hip', 'ankle', 'shoulder', 'elbow'].map((j) => (
                          <button
                            key={j}
                            className={`chart-select-btn ${selectedJoint === j ? 'active' : ''}`}
                            onClick={() => setSelectedJoint(j)}
                          >
                            {j.charAt(0).toUpperCase() + j.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Interactive Chart */}
                  <SvgTimeSeriesChart
                    data={jointSeriesData}
                    timeline={jointTimeline}
                    label={`${selectedSide}_${selectedJoint}`}
                    unit="°"
                    color={selectedSide === 'right' ? '#2563eb' : '#06b6d4'}
                  />

                  {/* Joint Summary Metrics */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "12px", marginTop: "18px" }}>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Current Angle</span>
                      <strong className="mini-metric-val">{jointInfo.current_angle || 0}°</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Minimum Angle</span>
                      <strong className="mini-metric-val">{jointInfo.min_angle || 0}°</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Maximum Angle</span>
                      <strong className="mini-metric-val">{jointInfo.max_angle || 0}°</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Average Angle</span>
                      <strong className="mini-metric-val">{jointInfo.avg_angle || 0}°</strong>
                    </div>
                    <div className="mini-metric-box" style={{ background: "rgba(37, 99, 235, 0.08)", borderColor: "var(--accent)" }}>
                      <span className="mini-metric-label" style={{ color: "var(--accent)" }}>Range of Motion</span>
                      <strong className="mini-metric-val" style={{ color: "var(--accent)" }}>{jointInfo.rom || 0}°</strong>
                    </div>
                  </div>
                </div>

                {/* ROM Comparison Cards */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <h3>Range of Motion (ROM) Bilateral Comparison</h3>
                  </div>

                  <div className="rom-cards-grid">
                    {['knee', 'hip', 'ankle', 'shoulder', 'elbow'].map((j) => {
                      const rKey = `right_${j}`;
                      const lKey = `left_${j}`;
                      const rRom = joints.summary?.[rKey]?.rom || 0;
                      const lRom = joints.summary?.[lKey]?.rom || 0;

                      return (
                        <div key={j} className="rom-card">
                          <div className="rom-card-header">
                            <span>{j.toUpperCase()} ROM</span>
                            <span style={{ color: "var(--text-muted)" }}>R vs L</span>
                          </div>
                          <div className="rom-card-val">
                            <span style={{ color: "var(--accent)" }}>{rRom.toFixed(1)}°</span>
                            <span style={{ margin: "0 6px", color: "var(--text-muted)" }}>/</span>
                            <span style={{ color: "#06b6d4" }}>{lRom.toFixed(1)}°</span>
                          </div>
                          <div className="rom-sub-row">
                            <span>Right: {joints.summary?.[rKey]?.min_angle}° - {joints.summary?.[rKey]?.max_angle}°</span>
                            <span>Left: {joints.summary?.[lKey]?.min_angle}° - {joints.summary?.[lKey]?.max_angle}°</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: MOVEMENT SYMMETRY */}
            {activeTab === 'symmetry' && (
              <div className="tab-panel">
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Bilateral Movement Symmetry ({symmetry.overall_symmetry_score || 90}%)</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Transparent measurement breakdown comparing right vs left side kinematics
                      </p>
                    </div>
                    <span className="table-status-badge optimal">
                      {symmetry.overall_symmetry_score >= 85 ? 'High Symmetry' : 'Asymmetry Detected'}
                    </span>
                  </div>

                  <div className="data-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Measurement Component</th>
                          <th>Right Side Value</th>
                          <th>Left Side Value</th>
                          <th>Symmetry Score</th>
                          <th>Weight</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {symmetry.factors?.map((f, idx) => (
                          <tr key={idx}>
                            <td><strong>{f.metric}</strong></td>
                            <td>{f.right_value}</td>
                            <td>{f.left_value}</td>
                            <td><strong>{f.symmetry_score}%</strong></td>
                            <td>{f.weight}</td>
                            <td>
                              <span className={`table-status-badge ${f.symmetry_score >= 85 ? 'optimal' : (f.symmetry_score >= 70 ? 'mild' : 'moderate')}`}>
                                {f.symmetry_score >= 85 ? 'Optimal' : (f.symmetry_score >= 70 ? 'Minor Deviation' : 'Elevated Asymmetry')}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: POSTURE & BALANCE */}
            {activeTab === 'posture' && (
              <div className="tab-panel">
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Posture Assessment ({posture.score || 90}/100)</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Kinetic chain alignment verification across head, spine, shoulders, hips, and knees
                      </p>
                    </div>
                  </div>

                  <div className="posture-checklist">
                    {posture.checklist?.map((item, idx) => (
                      <div key={idx} className="posture-item">
                        <div className={`posture-icon ${item.status}`}>
                          {item.icon}
                        </div>
                        <div className="posture-text">
                          <h4>{item.item}</h4>
                          <p>{item.message}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Dynamic Center-of-Mass (COM) Sway & Balance</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Postural control index derived from body segmental center-of-mass trajectory
                      </p>
                    </div>
                    <span className="table-status-badge optimal">
                      Score: {balance.score || 85}/100
                    </span>
                  </div>

                  <SvgTimeSeriesChart
                    data={analysis.time_series_data?.balance?.com_x || []}
                    timeline={jointTimeline}
                    label="com_sway"
                    unit="m"
                    color="#8b5cf6"
                  />

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginTop: "18px" }}>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Lateral Sway (Std)</span>
                      <strong className="mini-metric-val">{balance.lateral_sway_std || 0}</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Lateral Sway (Range)</span>
                      <strong className="mini-metric-val">{balance.lateral_sway_range || 0}</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Anterior-Posterior Sway</span>
                      <strong className="mini-metric-val">{balance.ap_sway_std || 0}</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Base of Support Width</span>
                      <strong className="mini-metric-val">{balance.avg_base_of_support || 0} (norm)</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: MOVEMENT METRICS */}
            {activeTab === 'mechanics' && (
              <div className="tab-panel">
                {/* Knee Valgus Timeline */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Knee Valgus Timeline (Frontal Plane Deviation)</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Dynamic medial collapse deviation in degrees from collinear hip-knee-ankle load axis
                      </p>
                    </div>
                  </div>

                  <SvgTimeSeriesChart
                    data={analysis.time_series_data?.valgus?.right || []}
                    timeline={jointTimeline}
                    label="right_valgus"
                    unit="°"
                    color="#ef4444"
                    threshold={10.0}
                  />

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginTop: "16px" }}>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Right Knee Max Valgus</span>
                      <strong className="mini-metric-val">{valgus.right?.max_deviation?.toFixed(1) || 0}°</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Left Knee Max Valgus</span>
                      <strong className="mini-metric-val">{valgus.left?.max_deviation?.toFixed(1) || 0}°</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Valgus Score</span>
                      <strong className="mini-metric-val">{valgus.score || 85}/100</strong>
                    </div>
                  </div>
                </div>

                {/* Hip Stability & Pelvic Tilt */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Pelvic Tilt & Hip Stability Timeline</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Pelvic tilt angle relative to horizontal plane
                      </p>
                    </div>
                  </div>

                  <SvgTimeSeriesChart
                    data={analysis.time_series_data?.hip?.pelvic_tilt || []}
                    timeline={jointTimeline}
                    label="pelvic_tilt"
                    unit="°"
                    color="#f59e0b"
                  />
                </div>

                {/* Trunk Lean Timeline */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Trunk Lean Inclination Timeline</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Torso inclination relative to vertical axis
                      </p>
                    </div>
                  </div>

                  <SvgTimeSeriesChart
                    data={analysis.time_series_data?.trunk?.lean || []}
                    timeline={jointTimeline}
                    label="trunk_lean"
                    unit="°"
                    color="#10b981"
                  />
                </div>

                {/* Joint Alignment Table */}
                <div className="card-panel">
                  <div className="card-panel-header">
                    <h3>Kinetic Chain Joint Alignment</h3>
                  </div>

                  <div className="data-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Joint</th>
                          <th>Right Side</th>
                          <th>Left Side</th>
                          <th>Status</th>
                          <th>Metric Basis</th>
                        </tr>
                      </thead>
                      <tbody>
                        {alignment.table?.map((row, idx) => (
                          <tr key={idx}>
                            <td><strong>{row.joint}</strong></td>
                            <td>{row.right}</td>
                            <td>{row.left}</td>
                            <td>
                              <span className={`table-status-badge ${row.status === 'Optimal' ? 'optimal' : 'mild'}`}>
                                {row.status}
                              </span>
                            </td>
                            <td>{row.metric}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 6: FORCE ESTIMATION */}
            {activeTab === 'force' && (
              <div className="tab-panel">
                <div className="card-panel">
                  <div className="card-panel-header">
                    <div>
                      <h3>Estimated Ground Reaction Force Proxy</h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Visual kinetic proxy estimated from center-of-mass acceleration and body mass
                      </p>
                    </div>
                    <span className="table-status-badge mild">Visual Proxy</span>
                  </div>

                  <SvgTimeSeriesChart
                    data={analysis.time_series_data?.force || []}
                    timeline={jointTimeline}
                    label="force_proxy"
                    unit=" N"
                    color="#ec4899"
                  />

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginTop: "18px" }}>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Peak Estimated Force</span>
                      <strong className="mini-metric-val">{force.peak_force_n || 0} N</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Peak Body Weight Multiple</span>
                      <strong className="mini-metric-val">{force.peak_force_bw || 1.0}x BW</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Average Force</span>
                      <strong className="mini-metric-val">{force.avg_force_n || 0} N</strong>
                    </div>
                    <div className="mini-metric-box">
                      <span className="mini-metric-label">Estimated Mass</span>
                      <strong className="mini-metric-val">{force.estimated_body_mass_kg || "—"} kg</strong>
                    </div>
                  </div>

                  <div className="disclaimer-box" style={{ marginTop: "18px" }}>
                    <strong>Visual Force Disclaimer:</strong> {force.disclaimer || "This is an estimation derived from video-based movement data and is not equivalent to force-plate measurement."}
                  </div>
                </div>
              </div>
            )}

            {/* TAB: TARGETED CORRECTIVE RECOMMENDATIONS */}
            {activeTab === 'recommendations' && (
              <div className="tab-panel">
                <div className="card-panel">
                  <div className="card-panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: "1.2rem", color: "var(--text-primary)" }}>
                        Targeted Corrective Recommendations & Drills
                      </h3>
                      <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        Prescriptive corrective exercises tailored exclusively to detected biomechanical deviations and movement vulnerabilities.
                      </p>
                    </div>
                    <span className="table-status-badge optimal">
                      {recommendations.length} Tailored Protocol{recommendations.length !== 1 ? 's' : ''}
                    </span>
                  </div>

                  {recommendations && recommendations.length > 0 ? (
                    <div className="recommendations-grid">
                      {recommendations.map((rec, idx) => (
                        <div key={idx} className="recommendation-card">
                          <div className="rec-header">
                            <span className="rec-category">{rec.category}</span>
                            <span className={`rec-priority-badge ${rec.priority?.toLowerCase() || 'medium'}`}>
                              {rec.priority || 'Medium'} Priority
                            </span>
                          </div>

                          <div className="rec-observation">
                            <strong>Observation:</strong> {rec.observation}
                          </div>

                          <div className="rec-action">
                            <strong>Corrective Focus:</strong> {rec.action}
                          </div>

                          {rec.drills && rec.drills.length > 0 && (
                            <div className="rec-drills-container">
                              <span className="rec-drills-label">Suggested Drills:</span>
                              <div className="drills-chips-list">
                                {rec.drills.map((drill, dIdx) => (
                                  <span key={dIdx} className="drill-chip">
                                    ✓ {drill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
                      <CheckCircle2 size={40} color="var(--success)" style={{ marginBottom: "12px" }} />
                      <h4 style={{ margin: "0 0 6px", color: "var(--text-primary)" }}>Optimal Movement Patterns Maintained</h4>
                      <p style={{ margin: 0, fontSize: "0.9rem" }}>No critical biomechanical deviations or corrective drills required at this time.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 7: REPORTS & EXPORT */}
            {activeTab === 'reports' && (
              <div className="tab-panel">
                <div className="reports-action-row">
                  {!isProfessionalView && (
                    <div className="report-download-card">
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                          <TableIcon size={20} color="var(--accent)" />
                          <h4 style={{ margin: 0 }}>Frame-by-Frame CSV Dataset</h4>
                        </div>
                        <p>
                          Download the complete kinematic dataset containing frame-by-frame joint angles (hip, knee, ankle, shoulder, elbow), knee valgus, pelvic tilt, trunk inclination, and force proxy estimations.
                        </p>
                      </div>

                      <button
                        className="primary-button"
                        onClick={() => handleDownload('csv')}
                        disabled={downloadingFile === 'csv'}
                      >
                        <Download size={16} />
                        {downloadingFile === 'csv' ? "Downloading CSV..." : "Download Timeseries CSV"}
                      </button>
                    </div>
                  )}

                  {!isProfessionalView && (
                    <>
                      {/* Card 2: ML Biomechanics Dataset */}
                      <div className="report-download-card" style={{ borderColor: "rgba(37, 99, 235, 0.4)" }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                            <Zap size={20} color="var(--accent)" />
                            <h4 style={{ margin: 0 }}>ML Biomechanics Dataset</h4>
                          </div>
                          <p>
                            Download aggregated ML features (exactly 1 row per video) containing ROM, peak valgus, pelvic stability, trunk lean, stride variability, COM sway, and force proxies for model training.
                          </p>
                        </div>

                        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                          <button
                            className="primary-button"
                            onClick={() => handleDownload('ml-csv')}
                            disabled={downloadingFile === 'ml-csv'}
                          >
                            <Download size={16} />
                            {downloadingFile === 'ml-csv' ? "Downloading Video ML CSV..." : "Download Video ML CSV (1 Row)"}
                          </button>
                          <button
                            className="secondary-button"
                            style={{ width: "100%", justifyContent: "center", padding: "8px 12px", fontSize: "0.82rem" }}
                            onClick={() => handleDownload('ml-dataset')}
                            disabled={downloadingFile === 'ml-dataset'}
                          >
                            <Download size={14} />
                            {downloadingFile === 'ml-dataset' ? "Downloading Master Dataset..." : "Download Master ML Dataset (All Videos)"}
                          </button>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Card 3: PDF Report */}
                  <div className="report-download-card">
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                        <FileText size={20} color="var(--accent)" />
                        <h4 style={{ margin: 0 }}>Movement Analysis PDF Report</h4>
                      </div>
                      <p>
                        Download the full printable PDF report including athlete metadata, joint angle & ROM summary tables, symmetry breakdowns, posture assessment checklist, and force proxy estimations.
                      </p>
                    </div>

                    <button
                      className="primary-button"
                      onClick={() => handleDownload('pdf')}
                      disabled={downloadingFile === 'pdf'}
                    >
                      <Download size={16} />
                      {downloadingFile === 'pdf' ? "Downloading PDF..." : "Download PDF Report"}
                    </button>
                  </div>
                </div>

                {/* ML Dataset Feature Summary Preview (1 Row per Video) */}
                {!isProfessionalView && <div className="card-panel" style={{ marginBottom: "20px" }}>
                  <div className="card-panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <h3 style={{ margin: "0 0 4px" }}>ML Feature Dataset Summary (1-Row-per-Video)</h3>
                      <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        Aggregated biomechanical features prepared for machine learning models (exported via <code>ml_dataset.py</code>)
                      </p>
                    </div>
                    <span className="table-status-badge optimal">
                      {analysis.summary_metrics?.feature_quality?.pose_detection_rate || 100}% Valid Frames
                    </span>
                  </div>

                  <div className="data-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Feature Category</th>
                          <th>Primary Metric</th>
                          <th>Mean / Standard Value</th>
                          <th>Peak / Range / ROM</th>
                          <th>Quality / Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td><strong>Knee Kinematics</strong></td>
                          <td>Right & Left Knee ROM</td>
                          <td>
                            R: {analysis.summary_metrics?.joint_angles?.summary?.right_knee?.avg_angle?.toFixed(1) || '—'}° / 
                            L: {analysis.summary_metrics?.joint_angles?.summary?.left_knee?.avg_angle?.toFixed(1) || '—'}°
                          </td>
                          <td>
                            R ROM: {analysis.summary_metrics?.joint_angles?.summary?.right_knee?.rom?.toFixed(1) || '—'}° / 
                            L ROM: {analysis.summary_metrics?.joint_angles?.summary?.left_knee?.rom?.toFixed(1) || '—'}°
                          </td>
                          <td><span className="table-status-badge optimal">Calculated</span></td>
                        </tr>
                        <tr>
                          <td><strong>Frontal Knee Valgus</strong></td>
                          <td>Dynamic Medial Deviation</td>
                          <td>
                            R Mean: {analysis.summary_metrics?.knee_valgus?.right?.avg_normalized_valgus?.toFixed(3) || '—'} / 
                            L Mean: {analysis.summary_metrics?.knee_valgus?.left?.avg_normalized_valgus?.toFixed(3) || '—'}
                          </td>
                          <td>
                            R Peak: {analysis.summary_metrics?.knee_valgus?.right?.peak_normalized_valgus?.toFixed(3) || '—'} / 
                            L Peak: {analysis.summary_metrics?.knee_valgus?.left?.peak_normalized_valgus?.toFixed(3) || '—'}
                          </td>
                          <td>
                            <span className="table-status-badge mild">
                              Score: {analysis.summary_metrics?.knee_valgus?.score || '—'}/100
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Pelvic Stability</strong></td>
                          <td>Pelvic Tilt & Drop</td>
                          <td>Mean Tilt: {analysis.summary_metrics?.hip_stability?.mean_pelvic_tilt_deg?.toFixed(1) || '—'}°</td>
                          <td>Max Tilt: {analysis.summary_metrics?.hip_stability?.max_pelvic_tilt_deg?.toFixed(1) || '—'}°</td>
                          <td>
                            <span className="table-status-badge optimal">
                              Score: {analysis.summary_metrics?.hip_stability?.score || '—'}/100
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Trunk Posture</strong></td>
                          <td>Trunk Inclination & Lateral Lean</td>
                          <td>Mean Lean: {analysis.summary_metrics?.trunk_lean?.avg_trunk_lean_deg?.toFixed(1) || '—'}°</td>
                          <td>Max Lean: {analysis.summary_metrics?.trunk_lean?.max_trunk_lean_deg?.toFixed(1) || '—'}°</td>
                          <td>
                            <span className="table-status-badge optimal">
                              Score: {analysis.summary_metrics?.trunk_lean?.score || '—'}/100
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Stride Kinematics</strong></td>
                          <td>Normalized Foot Separation</td>
                          <td>Mean Stride: {analysis.summary_metrics?.stride?.normalized_stride_length?.toFixed(3) || '—'}</td>
                          <td>Asymmetry: {analysis.summary_metrics?.stride?.stride_asymmetry_pct?.toFixed(1) || '—'}%</td>
                          <td><span className="table-status-badge optimal">Locomotion Tracked</span></td>
                        </tr>
                        <tr>
                          <td><strong>Center of Mass (COM)</strong></td>
                          <td>Dynamic Balance & Sway</td>
                          <td>Lat Sway Std: {analysis.summary_metrics?.balance?.lateral_sway_std?.toFixed(4) || '—'}</td>
                          <td>AP Sway Std: {analysis.summary_metrics?.balance?.ap_sway_std?.toFixed(4) || '—'}</td>
                          <td>
                            <span className="table-status-badge optimal">
                              Score: {analysis.summary_metrics?.balance?.score || '—'}/100
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Force Estimation Proxy</strong></td>
                          <td>Kinematic Vertical Loading</td>
                          <td>Mean Force: {analysis.summary_metrics?.force?.avg_force_n?.toFixed(1) || '—'} N</td>
                          <td>Peak Loading: {analysis.summary_metrics?.force?.peak_force_bw?.toFixed(2) || '—'} BW ({analysis.summary_metrics?.force?.peak_force_n?.toFixed(1) || '—'} N)</td>
                          <td>
                            <span className="table-status-badge optimal">
                              Mass: {analysis.summary_metrics?.athlete_profile?.weight_kg || '—'} kg
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td><strong>Bilateral Symmetry</strong></td>
                          <td>Composite Movement Symmetry</td>
                          <td>Overall Score: {analysis.summary_metrics?.symmetry?.overall_symmetry_score || '—'}%</td>
                          <td>Joint Alignment: {analysis.summary_metrics?.alignment?.score || '—'}/100</td>
                          <td>
                            <span className="table-status-badge optimal">
                              Quality: {analysis.movement_quality || '—'}/100
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>}

                {/* CSV Table Preview */}
                {!isProfessionalView && <div className="card-panel">
                  <div className="card-panel-header">
                    <h3>Frame-by-Frame Timeseries CSV Preview (First 15 Recorded Frames)</h3>
                  </div>

                  <div className="data-table-container">
                    <table className="analysis-table">
                      <thead>
                        <tr>
                          <th>Frame</th>
                          <th>Time (s)</th>
                          <th>R Knee (°)</th>
                          <th>L Knee (°)</th>
                          <th>R Hip (°)</th>
                          <th>L Hip (°)</th>
                          <th>R Valgus (°)</th>
                          <th>L Valgus (°)</th>
                          <th>Pelvic Tilt (°)</th>
                          <th>Trunk Lean (°)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {jointTimeline.slice(0, 15).map((t, idx) => (
                          <tr key={idx}>
                            <td><strong>{idx}</strong></td>
                            <td>{t}s</td>
                            <td>{analysis.time_series_data?.joints?.right_knee?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.joints?.left_knee?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.joints?.right_hip?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.joints?.left_hip?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.valgus?.right?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.valgus?.left?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.hip?.pelvic_tilt?.[idx]?.toFixed(1) || '—'}°</td>
                            <td>{analysis.time_series_data?.trunk?.lean?.[idx]?.toFixed(1) || '—'}°</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>}
              </div>
            )}
          </>
        )}
      </div>
    </LayoutComponent>
  );
}

export default Analysis;
