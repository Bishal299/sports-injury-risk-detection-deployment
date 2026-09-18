import React, { useCallback, useEffect, useMemo, useState } from "react";
import { BadgeCheck, Search, Send, UserRound, UsersRound, XCircle } from "lucide-react";

import {
  acceptSportsScientistIncomingRequest,
  discoverSportsScientistAthletes,
  getCurrentUser,
  getSportsScientistAthletes,
  getSportsScientistRequests,
  rejectSportsScientistIncomingRequest,
  removeSportsScientistConnection,
  sendSportsScientistConnectionRequest,
} from "../../services/api";
import "../../styles/coach.css";


function riskClass(category) {
  return String(category || "not available").toLowerCase().replace(/\s+/g, "-");
}

function formatDate(value) {
  if (!value) return "No analysis yet";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function requestButtonLabel(status, sending) {
  if (sending) return "Sending...";
  if (status === "PENDING") return "Request Sent";
  if (status === "ACTIVE") return "Connected";
  if (status === "REJECTED") return "Rejected";
  if (status === "REVOKED") return "Revoked";
  return "Send Request";
}

function SportsScientistAthletes() {
  const [filters, setFilters] = useState({
    search: "",
    sport: "",
    connection_status: "",
    sort: "recent",
  });
  const [currentUser, setCurrentUser] = useState(null);
  const [athletes, setAthletes] = useState([]);
  const [discoverable, setDiscoverable] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [workingId, setWorkingId] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const requestFilters = {
        search: filters.search,
        sport: filters.sport,
        connection_status: filters.connection_status,
        sort: filters.sort,
      };
      const [user, activeAthletes, discoveredAthletes, relationshipRequests] = await Promise.all([
        getCurrentUser(),
        getSportsScientistAthletes(requestFilters),
        discoverSportsScientistAthletes(requestFilters),
        getSportsScientistRequests(),
      ]);

      setCurrentUser(user);
      setAthletes(Array.isArray(activeAthletes) ? activeAthletes : []);
      setDiscoverable(Array.isArray(discoveredAthletes) ? discoveredAthletes : []);
      setRequests(Array.isArray(relationshipRequests) ? relationshipRequests : []);
    } catch (error) {
      setError(error.message || "Failed to load Sports Scientist athlete connections.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timeout = setTimeout(loadData, 250);
    return () => clearTimeout(timeout);
  }, [loadData]);

  const pendingOutgoing = useMemo(
    () =>
      requests.filter(
        (request) =>
          request.status === "PENDING" &&
          String(request.requested_by || "") === String(currentUser?.user_id || "")
      ),
    [currentUser?.user_id, requests]
  );

  const pendingIncoming = useMemo(
    () =>
      requests.filter(
        (request) =>
          request.status === "PENDING" &&
          String(request.requested_by || "") !== String(currentUser?.user_id || "")
      ),
    [currentUser?.user_id, requests]
  );

  function handleFilter(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function runAction(id, action) {
    setWorkingId(id);
    setError("");
    try {
      await action(id);
      await loadData();
    } catch (error) {
      setError(error.message || "Connection update failed.");
    } finally {
      setWorkingId("");
    }
  }

  return (
    <main className="coach-page">
      <section className="coach-page-header">
        <p className="page-eyebrow">SPORTS SCIENTIST</p>
        <h1>My Athletes</h1>
        <p>Manage athletes connected to your sports science analysis.</p>
      </section>

      <section className="coach-filter-card">
        <label className="coach-search-field">
          <Search size={17} />
          <input name="search" value={filters.search} onChange={handleFilter} placeholder="Search athletes" />
        </label>
        <input name="sport" value={filters.sport} onChange={handleFilter} placeholder="Sport" />
        <select name="connection_status" value={filters.connection_status} onChange={handleFilter}>
          <option value="">All statuses</option>
          <option value="NONE">Not connected</option>
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
          <option value="REJECTED">Rejected</option>
          <option value="REVOKED">Revoked</option>
        </select>
        <select name="sort" value={filters.sort} onChange={handleFilter}>
          <option value="recent">Recent analysis</option>
          <option value="name">Name</option>
          <option value="risk_desc">Risk high to low</option>
          <option value="risk_asc">Risk low to high</option>
        </select>
      </section>

      {error && <section className="coach-error-card">{error}</section>}
      {loading && <section className="coach-empty-card">Loading athlete connections...</section>}

      {!loading && (
        <>
          <section className="coach-stats-grid">
            <article className="coach-stat-card"><div className="coach-icon-box"><UsersRound size={21} /></div><div><span>Active athletes</span><strong>{athletes.length}</strong></div></article>
            <article className="coach-stat-card"><div className="coach-icon-box"><Send size={21} /></div><div><span>Pending requests</span><strong>{pendingOutgoing.length}</strong></div></article>
            <article className="coach-stat-card"><div className="coach-icon-box"><BadgeCheck size={21} /></div><div><span>Incoming requests</span><strong>{pendingIncoming.length}</strong></div></article>
          </section>

          <section className="coach-table-card">
            <div className="coach-section-heading"><div><h2>Active Athletes</h2><p>Connected athletes authorized for sports science analysis.</p></div></div>
            {athletes.length === 0 ? (
              <div className="coach-quiet-state">No active Sports Scientist athlete connections found.</div>
            ) : (
              <>
                <div className="coach-athlete-table scientist-athlete-table coach-athlete-table-head">
                  <span>Athlete</span><span>Sport</span><span>Position</span><span>Analyses</span><span>Risk</span><span>Connection</span><span>Action</span>
                </div>
                {athletes.map((athlete) => (
                  <article className="coach-athlete-table scientist-athlete-table" key={athlete.relationship_id}>
                    <div className="coach-athlete-cell athlete"><div className="coach-icon-box"><UserRound size={19} /></div><strong>{athlete.name}</strong></div>
                    <span>{athlete.sport || "Sport not set"}</span>
                    <span>{athlete.position || "Position not set"}</span>
                    <span>{athlete.analysis_count}</span>
                    <span className={`coach-risk-text ${riskClass(athlete.risk_category)}`}>{athlete.risk_category}{athlete.latest_risk_score !== null && athlete.latest_risk_score !== undefined ? ` (${Math.round(athlete.latest_risk_score)})` : ""}</span>
                    <span className="coach-connected-badge active">{athlete.connection_status}</span>
                    <button className="secondary-button compact" type="button" disabled={workingId === athlete.relationship_id} onClick={() => runAction(athlete.relationship_id, removeSportsScientistConnection)}>Remove</button>
                  </article>
                ))}
              </>
            )}
          </section>

          <section className="coach-dashboard-grid">
            <article className="coach-panel-card">
              <div className="coach-section-heading"><div><h2>Pending Requests</h2><p>Outgoing Sports Scientist connection requests awaiting athlete approval.</p></div></div>
              {pendingOutgoing.length === 0 ? <div className="coach-quiet-state">No outgoing pending requests.</div> : pendingOutgoing.map((request) => (
                <div className="coach-list-row" key={request.relationship_id}><div><strong>{request.athlete_name || "Athlete"}</strong><span>{request.athlete_sport || "Sport not set"}</span></div><span className="coach-connected-badge pending">PENDING</span></div>
              ))}
            </article>

            <article className="coach-panel-card">
              <div className="coach-section-heading"><div><h2>Incoming Requests</h2><p>Athlete-initiated Sports Scientist connection requests.</p></div></div>
              {pendingIncoming.length === 0 ? <div className="coach-quiet-state">No incoming pending requests.</div> : pendingIncoming.map((request) => (
                <div className="coach-list-row" key={request.relationship_id}>
                  <div><strong>{request.athlete_name || "Athlete"}</strong><span>{request.athlete_sport || "Sport not set"}</span></div>
                  <div className="coach-row-actions">
                    <button className="secondary-button compact" disabled={workingId === request.relationship_id} onClick={() => runAction(request.relationship_id, rejectSportsScientistIncomingRequest)} type="button"><XCircle size={14} />Reject</button>
                    <button className="primary-button compact" disabled={workingId === request.relationship_id} onClick={() => runAction(request.relationship_id, acceptSportsScientistIncomingRequest)} type="button"><BadgeCheck size={14} />Accept</button>
                  </div>
                </div>
              ))}
            </article>
          </section>

          <section className="coach-athlete-grid">
            {discoverable.length === 0 ? (
              <article className="coach-empty-card"><h2>No eligible athletes found</h2><p>Try adjusting search, sport, or status filters.</p></article>
            ) : discoverable.map((athlete) => {
              const sending = workingId === athlete.athlete_id;
              const disabled = athlete.connection_status !== "NONE" || sending;
              return (
                <article className="coach-athlete-card" key={athlete.athlete_id}>
                  <div><h2>{athlete.name}</h2><p>{athlete.sport || "Sport not set"}{athlete.position ? ` • ${athlete.position}` : ""}</p></div>
                  <div className="coach-risk-row"><span className={`coach-risk-badge ${riskClass(athlete.risk_category)}`}>{athlete.risk_category}</span><strong>{athlete.analysis_count}</strong></div>
                  <div className="coach-card-meta"><span>{formatDate(athlete.latest_activity_at)}</span><span>{athlete.connection_status}</span></div>
                  <button className="primary-button" type="button" disabled={disabled} onClick={() => runAction(athlete.athlete_id, sendSportsScientistConnectionRequest)}><Send size={16} />{requestButtonLabel(athlete.connection_status, sending)}</button>
                </article>
              );
            })}
          </section>
        </>
      )}
    </main>
  );
}


export default SportsScientistAthletes;
