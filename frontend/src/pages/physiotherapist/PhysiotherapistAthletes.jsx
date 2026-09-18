import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarClock, Search, Send, UserRound, UsersRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  discoverPhysiotherapistAthletes,
  getPhysiotherapistAthletes,
  sendPhysiotherapistConnectionRequest,
} from "../../services/api";
import "../../styles/coach.css";

const riskFilters = ["All", "Low", "Moderate", "High", "Critical"];
const recoveryFilters = ["All", "NOT_STARTED", "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"];

function formatDate(value) {
  if (!value) return "Not analyzed yet.";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function riskClass(category) {
  return String(category || "not available").toLowerCase().replace(/\s+/g, "-");
}

function requestButtonLabel(status, sending) {
  if (sending) return "Sending...";
  if (status === "PENDING") return "Request Sent";
  if (status === "ACTIVE") return "Connected";
  if (status === "REJECTED") return "Request Rejected";
  if (status === "REVOKED") return "Access Revoked";
  return "Send Request";
}

export function PhysiotherapistDiscoverAthletes() {
  const [filters, setFilters] = useState({ search: "", sport: "", risk_category: "", connection_status: "", sort: "name" });
  const [athletes, setAthletes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sendingId, setSendingId] = useState("");

  const loadAthletes = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await discoverPhysiotherapistAthletes(filters);
      setAthletes(Array.isArray(data) ? data : []);
    } catch (error) {
      setError(error.message || "Failed to discover athletes.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timeout = setTimeout(loadAthletes, 250);
    return () => clearTimeout(timeout);
  }, [loadAthletes]);

  async function handleSendRequest(athleteId) {
    setSendingId(athleteId);
    setError("");
    try {
      await sendPhysiotherapistConnectionRequest(athleteId);
      await loadAthletes();
    } catch (error) {
      setError(error.message || "Failed to send request.");
    } finally {
      setSendingId("");
    }
  }

  return (
    <main className="coach-page">
        <section className="coach-page-header">
          <p className="page-eyebrow">DISCOVER ATHLETES</p>
          <h1>Discover Athletes</h1>
          <p>View limited public athlete information and request physiotherapy access.</p>
        </section>

        <section className="coach-filter-card">
          <label className="coach-search-field"><Search size={17} /><input name="search" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Search athlete name" /></label>
          <input name="sport" value={filters.sport} onChange={(event) => setFilters({ ...filters, sport: event.target.value })} placeholder="Sport" />
          <select name="risk_category" value={filters.risk_category} onChange={(event) => setFilters({ ...filters, risk_category: event.target.value })}>
            <option value="">All risk</option><option value="LOW">Low</option><option value="MODERATE">Moderate</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option>
          </select>
          <select name="connection_status" value={filters.connection_status} onChange={(event) => setFilters({ ...filters, connection_status: event.target.value })}>
            <option value="">All statuses</option><option value="NONE">Not connected</option><option value="PENDING">Pending</option><option value="ACTIVE">Connected</option><option value="REJECTED">Rejected</option><option value="REVOKED">Revoked</option>
          </select>
          <select name="sort" value={filters.sort} onChange={(event) => setFilters({ ...filters, sort: event.target.value })}>
            <option value="name">Name</option><option value="risk_desc">Risk high to low</option><option value="risk_asc">Risk low to high</option><option value="recent">Recent activity</option>
          </select>
        </section>

        {error && <section className="coach-error-card">{error}</section>}
        {loading && <section className="coach-empty-card">Loading athletes...</section>}
        {!loading && athletes.length === 0 && <section className="coach-empty-card"><h2>No athletes found</h2><p>Try adjusting your search or filters.</p></section>}
        {!loading && athletes.length > 0 && (
          <section className="coach-athlete-grid">
            {athletes.map((athlete) => {
              const sending = sendingId === athlete.athlete_id;
              const disabled = athlete.connection_status !== "NONE" || sending;
              return (
                <article className="coach-athlete-card" key={athlete.athlete_id}>
                  <div><h2>{athlete.name}</h2><p>{athlete.sport || "Sport not set"}{athlete.age ? ` · ${athlete.age} yrs` : ""}</p></div>
                  <div className="coach-risk-row"><span className={`coach-risk-badge ${riskClass(athlete.risk_category)}`}>{athlete.risk_category}</span><strong>{athlete.latest_risk_score ?? "N/A"}</strong></div>
                  <div className="coach-card-meta"><span>{athlete.availability}</span><span>{athlete.connection_status}</span></div>
                  <button className="primary-button" disabled={disabled} onClick={() => handleSendRequest(athlete.athlete_id)} type="button"><Send size={16} />{requestButtonLabel(athlete.connection_status, sending)}</button>
                </article>
              );
            })}
          </section>
        )}
    </main>
  );
}

function PhysiotherapistAthletes() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ search: "", risk_category: "All", recovery_status: "All", sort: "recent" });
  const [athletes, setAthletes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const data = await getPhysiotherapistAthletes(filters);
        if (!cancelled) setAthletes(Array.isArray(data) ? data : []);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load connected athletes.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [filters]);

  const resultText = useMemo(() => loading ? "Loading connected athletes..." : `${athletes.length} active athlete${athletes.length === 1 ? "" : "s"}`, [athletes.length, loading]);

  return (
    <main className="coach-page">
        <section className="coach-page-header coach-page-header-row">
          <div><p className="page-eyebrow">MY ATHLETES</p><h1>My Athletes</h1><p>{resultText}</p></div>
          <button className="primary-button" type="button" onClick={() => navigate("/physiotherapist/discover-athletes")}><UsersRound size={18} />Find Athletes</button>
        </section>

        {error && <section className="coach-error-card">{error}</section>}
        <section className="coach-table-toolbar">
          <label className="coach-search-field"><Search size={18} /><input type="search" placeholder="Search athletes..." value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} /></label>
          <div className="coach-filter-pills">{riskFilters.map((risk) => <button className={filters.risk_category === risk ? "active" : ""} key={risk} type="button" onClick={() => setFilters({ ...filters, risk_category: risk })}>{risk}</button>)}</div>
          <select value={filters.recovery_status} onChange={(event) => setFilters({ ...filters, recovery_status: event.target.value })}>{recoveryFilters.map((item) => <option key={item} value={item}>{item.replace("_", " ")}</option>)}</select>
          <select value={filters.sort} onChange={(event) => setFilters({ ...filters, sort: event.target.value })}><option value="recent">Recent Activity</option><option value="risk_desc">Risk High to Low</option><option value="risk_asc">Risk Low to High</option><option value="name">Name</option></select>
        </section>

        {loading && <section className="coach-empty-card">Loading connected athletes...</section>}
        {!loading && athletes.length === 0 && <section className="coach-empty-card"><h2>No athletes connected yet.</h2><p>Accepted physiotherapy relationships will appear here.</p></section>}
        {!loading && athletes.length > 0 && (
          <section className="coach-table-card">
            <div className="coach-athlete-table coach-athlete-table-head"><span>Athlete</span><span>Sport</span><span>Risk</span><span>Recovery Progress</span><span>Rehab Status</span><span>Action</span></div>
            {athletes.map((athlete) => {
              const videosPath = `/physiotherapist/athletes/${athlete.athlete_id}/videos`;
              return (
                <article className="coach-athlete-table" key={athlete.relationship_id}>
                  <div className="coach-athlete-cell athlete"><div className="coach-icon-box"><UserRound size={19} /></div><strong>{athlete.name}</strong></div>
                  <span>{athlete.sport || "Sport not set"}</span>
                  <span className={`coach-risk-text ${riskClass(athlete.risk_category)}`}>{athlete.risk_category}</span>
                  <span className="coach-muted-cell">{athlete.recovery_progress === null || athlete.recovery_progress === undefined ? "No plan" : `${athlete.recovery_progress}%`}</span>
                  <span className="coach-connected-badge active">{athlete.rehabilitation_status}</span>
                  <button className="secondary-button compact" type="button" onClick={() => navigate(videosPath)}>View Videos</button>
                </article>
              );
            })}
          </section>
        )}
    </main>
  );
}

export default PhysiotherapistAthletes;
