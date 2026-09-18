import React, { useEffect, useMemo, useState } from "react";
import { BarChart3, Download, FileText, HeartPulse, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  downloadRecoveryReport,
  getPhysiotherapistAthleteDetail,
  getPhysiotherapistAthletes,
} from "../../services/api";
import "../../styles/coach.css";

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function PhysiotherapistResourceList({ type }) {
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const config = {
    rehabilitation: { eyebrow: "REHABILITATION", title: "Rehabilitation", icon: HeartPulse },
    "movement-analytics": { eyebrow: "MOVEMENT ANALYTICS", title: "Movement Analytics", icon: BarChart3 },
    reports: { eyebrow: "RECOVERY REPORTS", title: "Recovery Reports", icon: FileText },
  }[type];

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const athletes = await getPhysiotherapistAthletes();
        const details = await Promise.all(athletes.map(async (athlete) => ({ athlete, detail: await getPhysiotherapistAthleteDetail(athlete.athlete_id) })));
        if (cancelled) return;
        const nextRows = details.flatMap(({ athlete, detail }) => {
          if (type === "rehabilitation") {
            const plan = detail.rehabilitation_plan;
            return [{
              id: `rehab-${athlete.athlete_id}`,
              athlete_id: athlete.athlete_id,
              athlete_name: athlete.name,
              title: plan?.current_phase?.replaceAll("_", " ") || "No rehabilitation plan created yet.",
              date: plan?.updated_at,
              status: plan?.status || "NOT_STARTED",
              meta: plan?.progress === undefined || plan?.progress === null ? "No progress recorded" : `${plan.progress}% recovery progress`,
            }];
          }
          if (type === "reports") {
            return [{
              id: `report-${athlete.athlete_id}`,
              athlete_id: athlete.athlete_id,
              athlete_name: athlete.name,
              title: "Recovery Report",
              date: detail.rehabilitation_plan?.updated_at || detail.latest_analysis?.completed_at,
              status: detail.rehabilitation_plan ? detail.rehabilitation_plan.status : "NO_PLAN",
              meta: detail.risk_monitoring?.risk_category,
            }];
          }
          if (type === "movement-analytics") {
            const analyses = Array.isArray(detail.analyses) ? detail.analyses : [];
            const latest = detail.latest_analysis || analyses[0] || null;
            return [{
              id: `movement-${athlete.athlete_id}`,
            athlete_id: athlete.athlete_id,
            athlete_name: athlete.name,
              title: latest?.video_activity || "Movement Analytics",
              date: latest?.completed_at || latest?.analysis_date,
              status: analyses.length > 1
                ? detail.movement_comparison?.comparison_status || "Available"
                : (analyses.length === 1 ? "No Previous Assessment" : "No Analysis"),
              meta: detail.risk_monitoring?.risk_category,
            }];
          }
          return [];
        });
        nextRows.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
        setRows(nextRows);
      } catch (error) {
        if (!cancelled) setError(error.message || `Failed to load ${config.title}.`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [config.title, type]);

  const visibleRows = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return rows;
    return rows.filter((row) => row.athlete_name.toLowerCase().includes(value) || row.title.toLowerCase().includes(value) || String(row.meta || "").toLowerCase().includes(value));
  }, [rows, search]);

  const Icon = config.icon;

  return (
    <main className="coach-page">
        <section className="coach-page-header coach-page-header-row"><div><p className="page-eyebrow">{config.eyebrow}</p><h1>{config.title}</h1><p>Real data from active physiotherapy relationships.</p></div><Icon size={28} /></section>
        <section className="coach-table-toolbar"><label className="coach-search-field"><Search size={17} /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${config.title.toLowerCase()}`} /></label></section>
        {error && <section className="coach-error-card">{error}</section>}
        {loading && <section className="coach-empty-card">Loading {config.title.toLowerCase()}...</section>}
        {!loading && !error && visibleRows.length === 0 && <section className="coach-empty-card">No {config.title.toLowerCase()} available.</section>}
        {!loading && !error && visibleRows.length > 0 && (
          <section className="coach-table-card">
            <div className="coach-athlete-table coach-athlete-table-head"><span>Athlete</span><span>Item</span><span>Date</span><span>Status</span><span>Detail</span><span>Action</span></div>
            {visibleRows.map((row) => (
              <article className="coach-athlete-table" key={`${type}-${row.id}`}>
                <div className="coach-athlete-cell athlete"><div className="coach-icon-box"><Icon size={19} /></div><strong>{row.athlete_name}</strong></div>
                <span>{row.title}</span>
                <span className="coach-muted-cell">{formatDate(row.date)}</span>
                <span className="coach-connected-badge active">{row.status}</span>
                <span>{row.meta || "Not available"}</span>
                <div className="coach-report-actions">
                  {type === "reports" ? (
                    <button className="secondary-button compact" type="button" onClick={() => downloadRecoveryReport(row.athlete_id, "pdf")}><Download size={15} />PDF</button>
                  ) : type === "movement-analytics" ? (
                    <button className="secondary-button compact" type="button" onClick={() => navigate(`/physiotherapist/movement-analytics/${row.athlete_id}`)}>Open Analytics</button>
                  ) : type === "rehabilitation" ? (
                    <button className="secondary-button compact" type="button" onClick={() => navigate(`/physiotherapist/rehabilitation/${row.athlete_id}`)}>Open</button>
                  ) : (
                    <button className="secondary-button compact" type="button" onClick={() => navigate(`/physiotherapist/athletes/${row.athlete_id}`)}>Open</button>
                  )}
                </div>
              </article>
            ))}
          </section>
        )}
    </main>
  );
}


export default PhysiotherapistResourceList;
