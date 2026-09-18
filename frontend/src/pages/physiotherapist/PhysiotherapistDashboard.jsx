import React, { useEffect, useState } from "react";
import { AlertTriangle, HeartPulse, Search, UsersRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getCurrentUser, getPhysiotherapistDashboard } from "../../services/api";
import "../../styles/coach.css";


function greeting(name) {
  const hour = new Date().getHours();
  if (hour >= 4 && hour < 12) return `Good Morning, ${name}`;
  if (hour >= 12 && hour < 17) return `Good Afternoon, ${name}`;
  return `Good Evening, ${name}`;
}


function PhysiotherapistDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [currentUser, data] = await Promise.all([
          getCurrentUser(),
          getPhysiotherapistDashboard(),
        ]);
        if (!cancelled) {
          setUser(currentUser);
          setDashboard(data);
        }
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load Physiotherapist dashboard.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const stats = [
    { label: "Total Athletes", value: dashboard?.stats?.total_athletes ?? 0, icon: UsersRound },
    { label: "Recovering", value: dashboard?.stats?.recovering ?? 0, icon: HeartPulse },
    { label: "High Risk", value: dashboard?.stats?.high_risk ?? 0, icon: AlertTriangle },
    { label: "Needs Attention", value: dashboard?.stats?.needs_attention ?? 0, icon: AlertTriangle },
  ];
  const athletes = Array.isArray(dashboard?.athletes) ? dashboard.athletes : [];
  const attention = Array.isArray(dashboard?.attention) ? dashboard.attention : [];
  const visibleAthletes = athletes.slice(0, 5);
  const visibleAttention = attention.slice(0, 5);

  return (
    <main className="coach-page">
        <section className="coach-page-header">
          <p className="page-eyebrow">PHYSIOTHERAPIST DASHBOARD</p>
          <h1>{greeting(user?.name || "Physiotherapist")}</h1>
          <p>Monitor rehabilitation progress, recovery, and injury risk.</p>
        </section>

        {loading && <section className="coach-empty-card">Loading Physiotherapist environment...</section>}
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
                <div className="coach-section-heading"><div><h2>Needs Attention</h2><p>High risk or rehab follow-up signals from real records.</p></div></div>
                {attention.length === 0 ? (
                  <div className="coach-quiet-state">No current recovery alerts.</div>
                ) : (
                  <div className="coach-alert-list">
                    {visibleAttention.map((item) => (
                      <div className="coach-alert-row" key={`${item.athlete_id}-${item.latest_analysis_at || ""}`}>
                        <span className={`coach-risk-dot ${String(item.risk_category || "moderate").toLowerCase()}`} />
                        <div>
                          <strong>{item.athlete_name}</strong>
                          <p>{item.risk_category} risk · {item.rehabilitation_status}</p>
                        </div>
                      </div>
                    ))}
                    {attention.length > visibleAttention.length && (
                      <button className="secondary-button compact" type="button" onClick={() => navigate("/physiotherapist/athletes")}>Show More</button>
                    )}
                  </div>
                )}
              </article>

              <article className="coach-panel-card">
                <div className="coach-section-heading">
                  <div><h2>My Athletes</h2><p>Recently active rehabilitation caseload.</p></div>
                  <button className="secondary-button compact" type="button" onClick={() => navigate("/physiotherapist/athletes")}>View All</button>
                </div>
                {athletes.length === 0 ? (
                  <div className="coach-empty-inline">
                    <p>No active athlete relationships yet.</p>
                    <button className="primary-button" type="button" onClick={() => navigate("/physiotherapist/discover-athletes")}>
                      <Search size={17} /> Discover Athletes
                    </button>
                  </div>
                ) : (
                  <div className="coach-mini-athlete-list">
                    {visibleAthletes.map((athlete) => (
                      <div className="coach-mini-athlete" key={athlete.athlete_id}>
                        <div><strong>{athlete.name}</strong><span>{athlete.current_phase || "No rehabilitation plan"}</span></div>
                        <span className={`coach-risk-badge ${athlete.risk_category?.toLowerCase().replace(" ", "-")}`}>{athlete.risk_category}</span>
                      </div>
                    ))}
                    {athletes.length > visibleAthletes.length && (
                      <button className="secondary-button compact" type="button" onClick={() => navigate("/physiotherapist/athletes")}>Show More</button>
                    )}
                  </div>
                )}
              </article>
            </section>
          </>
        )}
    </main>
  );
}


export default PhysiotherapistDashboard;
