import React, { useCallback, useEffect, useState } from "react";
import { Search, Send } from "lucide-react";

import { discoverAthletes, sendCoachConnectionRequest } from "../../services/api";
import "../../styles/coach.css";


function riskClass(category) {
  return String(category || "not available").toLowerCase().replace(/\s+/g, "-");
}


function requestButtonLabel(status, isSending) {
  if (isSending) {
    return "Sending...";
  }

  if (status === "PENDING") {
    return "Request Sent";
  }

  if (status === "ACTIVE") {
    return "Connected";
  }

  if (status === "REJECTED") {
    return "Request Rejected";
  }

  if (status === "REVOKED") {
    return "Access Revoked";
  }

  return "Send Request";
}


function DiscoverAthletes() {
  const [filters, setFilters] = useState({
    search: "",
    sport: "",
    risk_category: "",
    connection_status: "",
    sort: "name",
  });
  const [athletes, setAthletes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sendingId, setSendingId] = useState("");

  const loadAthletes = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await discoverAthletes(filters);
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

  const handleFilter = (event) => {
    const { name, value } = event.target;
    setFilters((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSendRequest = async (athleteId) => {
    setSendingId(athleteId);
    setError("");

    try {
      await sendCoachConnectionRequest(athleteId);
      setAthletes((current) =>
        current.map((athlete) =>
          athlete.athlete_id === athleteId
            ? {
                ...athlete,
                connection_status: "PENDING",
              }
            : athlete
        )
      );
      await loadAthletes();
    } catch (error) {
      setError(error.message || "Failed to send request.");
    } finally {
      setSendingId("");
    }
  };

  return (
    <main className="coach-page">
        <section className="coach-page-header">
          <p className="page-eyebrow">DISCOVER ATHLETES</p>
          <h1>Discover Athletes</h1>
          <p>View limited public athlete information and request access.</p>
        </section>

        <section className="coach-filter-card">
          <label className="coach-search-field">
            <Search size={17} />
            <input
              name="search"
              value={filters.search}
              onChange={handleFilter}
              placeholder="Search athlete name"
            />
          </label>

          <input
            name="sport"
            value={filters.sport}
            onChange={handleFilter}
            placeholder="Sport"
          />

          <select
            name="risk_category"
            value={filters.risk_category}
            onChange={handleFilter}
          >
            <option value="">All risk</option>
            <option value="LOW">Low</option>
            <option value="MODERATE">Moderate</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>

          <select
            name="connection_status"
            value={filters.connection_status}
            onChange={handleFilter}
          >
            <option value="">All statuses</option>
            <option value="NONE">Not connected</option>
            <option value="PENDING">Pending</option>
            <option value="ACTIVE">Connected</option>
            <option value="REJECTED">Rejected</option>
            <option value="REVOKED">Revoked</option>
          </select>

          <select
            name="sort"
            value={filters.sort}
            onChange={handleFilter}
          >
            <option value="name">Name</option>
            <option value="risk_desc">Risk high to low</option>
            <option value="risk_asc">Risk low to high</option>
            <option value="recent">Recent activity</option>
          </select>
        </section>

        {error && <section className="coach-error-card">{error}</section>}
        {loading && <section className="coach-empty-card">Loading athletes...</section>}

        {!loading && athletes.length === 0 && (
          <section className="coach-empty-card">
            <h2>No athletes found</h2>
            <p>Try adjusting your search or filters.</p>
          </section>
        )}

        {!loading && athletes.length > 0 && (
          <section className="coach-athlete-grid">
            {athletes.map((athlete) => (
              <article className="coach-athlete-card" key={athlete.athlete_id}>
                {(() => {
                  const isSending = sendingId === athlete.athlete_id;
                  const isActionDisabled = athlete.connection_status !== "NONE" || isSending;

                  return (
                    <>
                      <div>
                        <h2>{athlete.name}</h2>
                        <p>{athlete.sport || "Sport not set"}{athlete.age ? ` • ${athlete.age} yrs` : ""}</p>
                      </div>

                      <div className="coach-risk-row">
                        <span className={`coach-risk-badge ${riskClass(athlete.risk_category)}`}>
                          {athlete.risk_category}
                        </span>
                        <strong>
                          {athlete.latest_risk_score !== null && athlete.latest_risk_score !== undefined
                            ? Math.round(athlete.latest_risk_score)
                            : "N/A"}
                        </strong>
                      </div>

                      <div className="coach-card-meta">
                        <span>{athlete.availability}</span>
                        <span>{athlete.connection_status}</span>
                      </div>

                      <button
                        className="primary-button"
                        disabled={isActionDisabled}
                        onClick={() => handleSendRequest(athlete.athlete_id)}
                        type="button"
                      >
                        <Send size={16} />
                        {requestButtonLabel(athlete.connection_status, isSending)}
                      </button>
                    </>
                  );
                })()}
              </article>
            ))}
          </section>
        )}
    </main>
  );
}


export default DiscoverAthletes;
