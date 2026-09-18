import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import DashboardLayout from "../../layouts/DashboardLayout";
import { getAnalysisHistory } from "../../services/api";

import "../../styles/dashboard.css";
import "../../styles/analysis-history.css";


function AnalysisHistory() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setError("");
        const records = await getAnalysisHistory();
        setHistory(records);
      } catch (error) {
        setError(error.message || "Failed to load analysis history");
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  const formatDate = (value) => {
    if (!value) return "N/A";
    return new Date(value).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const scoreValue = (value) => {
    if (value === null || value === undefined) return "0";
    return Number(value).toFixed(1);
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="dashboard-card">
          <p>Loading analysis history...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="page-header">
        <p className="page-eyebrow">ANALYSIS</p>
        <h1>Analysis History</h1>
        <p>Review completed movement-risk analyses without changing historical results.</p>
      </div>

      {error && (
        <div className="dashboard-card analysis-history-alert">
          {error}
        </div>
      )}

      {!error && history.length === 0 && (
        <div className="dashboard-card analysis-history-empty">
          <h2>No analyses completed yet</h2>
          <p>Completed video analyses will appear here after processing finishes.</p>
          <button
            className="primary-button"
            onClick={() => navigate("/my-videos")}
          >
            Go to My Videos
          </button>
        </div>
      )}

      {!error && history.length > 0 && (
        <div className="dashboard-card analysis-history-card">
          <div className="analysis-history-table-wrap">
            <table className="analysis-history-table">
              <thead>
                <tr>
                  <th>Video</th>
                  <th>Date</th>
                  <th>S_hist</th>
                  <th>Risk Score</th>
                  <th>Risk</th>
                  <th>Algorithm</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => {
                  const riskScore = item.composite_risk_score ?? item.overall_risk_score;
                  const risk = item.risk_category || item.risk_level || "N/A";

                  return (
                    <tr key={item.analysis_id}>
                      <td>
                        <strong>{item.video?.activity || "Movement Test"}</strong>
                        <span>{String(item.video_id).slice(0, 8)}...</span>
                      </td>
                      <td>{formatDate(item.completed_at || item.analysis_date)}</td>
                      <td>{scoreValue(item.historical_score)}</td>
                      <td>{scoreValue(riskScore)}</td>
                      <td>{risk}</td>
                      <td>{item.algorithm_version || "N/A"}</td>
                      <td>
                        <button
                          className="primary-button history-action-button"
                          onClick={() => navigate(`/analysis/${item.video_id}?analysisId=${item.analysis_id}`)}
                        >
                          View Analysis
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}


export default AnalysisHistory;
