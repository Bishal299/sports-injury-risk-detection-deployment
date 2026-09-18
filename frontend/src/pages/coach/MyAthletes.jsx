import React, { useEffect, useMemo, useState } from "react";
import { CalendarClock, Search, UserRound, UsersRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getCoachConnectedAthletes } from "../../services/api";
import "../../styles/coach.css";

const riskFilters = ["All", "Low", "Moderate", "High", "Critical"];
const sortOptions = [
  { value: "recent", label: "Recent Activity" },
  { value: "risk_desc", label: "Risk High → Low" },
  { value: "risk_asc", label: "Risk Low → High" },
  { value: "name", label: "Name" },
];


function formatDate(value) {
  if (!value) {
    return "Not analyzed yet.";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}


function RiskBadge({ category }) {
  if (!category || category === "Not Available") {
    return <span className="coach-risk-text unavailable">Not Available</span>;
  }

  const key = category.toLowerCase();
  const labelMap = {
    low: "🟢 Low",
    moderate: "🟡 Moderate",
    high: "🟠 High",
    critical: "🔴 Critical",
  };

  return (
    <span className={`coach-risk-text ${key}`}>
      {labelMap[key] || category}
    </span>
  );
}


function MyAthletes() {
  const navigate = useNavigate();
  const [athletes, setAthletes] = useState([]);
  const [filters, setFilters] = useState({
    search: "",
    risk_category: "All",
    sort: "recent",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadAthletes() {
      try {
        const data = await getCoachConnectedAthletes({
          search: filters.search,
          risk_category: filters.risk_category,
          sort: filters.sort,
        });
        if (!cancelled) {
          setAthletes(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message || "Failed to load connected athletes.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAthletes();

    return () => {
      cancelled = true;
    };
  }, [filters]);

  const resultText = useMemo(() => {
    if (loading) {
      return "Loading connected athletes...";
    }

    if (athletes.length === 1) {
      return "1 active athlete";
    }

    return `${athletes.length} active athletes`;
  }, [athletes.length, loading]);

  return (
    <main className="coach-page">
        <section className="coach-page-header coach-page-header-row">
          <div>
            <p className="page-eyebrow">MY ATHLETES</p>
            <h1>My Athletes</h1>
            <p>{resultText}</p>
          </div>
          <button
            className="primary-button"
            type="button"
            onClick={() => navigate("/coach/discover-athletes")}
          >
            <UsersRound size={18} />
            Find Athletes
          </button>
        </section>

        {error && <section className="coach-error-card">{error}</section>}

        <section className="coach-table-toolbar">
          <label className="coach-search-field">
            <Search size={18} />
            <input
              type="search"
              placeholder="Search athletes..."
              value={filters.search}
              onChange={(event) => setFilters((current) => ({
                ...current,
                search: event.target.value,
              }))}
            />
          </label>

          <div className="coach-filter-pills">
            {riskFilters.map((risk) => (
              <button
                className={filters.risk_category === risk ? "active" : ""}
                key={risk}
                type="button"
                onClick={() => setFilters((current) => ({
                  ...current,
                  risk_category: risk,
                }))}
              >
                {risk}
              </button>
            ))}
          </div>

          <select
            value={filters.sort}
            onChange={(event) => setFilters((current) => ({
              ...current,
              sort: event.target.value,
            }))}
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </section>

        {loading && <section className="coach-empty-card">Loading connected athletes...</section>}

        {!loading && athletes.length === 0 && (
          <section className="coach-empty-card">
            <h2>No athletes connected yet.</h2>
            <p>Accepted athlete relationships will appear here.</p>
            <button
              className="primary-button coach-empty-action"
              type="button"
              onClick={() => navigate("/coach/discover-athletes")}
            >
              <Search size={17} />
              Discover Athletes
            </button>
          </section>
        )}

        {!loading && athletes.length > 0 && (
          <section className="coach-table-card">
            <div className="coach-athlete-table coach-athlete-table-head">
              <span>Athlete</span>
              <span>Sport</span>
              <span>Risk</span>
              <span>Last Analysis</span>
              <span>Status</span>
              <span>Action</span>
            </div>

            {athletes.map((athlete) => (
              <article className="coach-athlete-table" key={athlete.relationship_id}>
                <div className="coach-athlete-cell athlete">
                  <div className="coach-icon-box">
                    <UserRound size={19} />
                  </div>
                  <strong>{athlete.name}</strong>
                </div>
                <span>{athlete.sport || "Sport not set"}</span>
                <RiskBadge category={athlete.risk_category} />
                <span className="coach-muted-cell">
                  <CalendarClock size={15} />
                  {formatDate(athlete.last_analysis_at)}
                </span>
                <span className="coach-connected-badge active">ACTIVE</span>
                <button
                  className="secondary-button compact"
                  type="button"
                  onClick={() => navigate(`/coach/athletes/${athlete.athlete_id}`)}
                >
                  View Profile
                </button>
              </article>
            ))}
          </section>
        )}
    </main>
  );
}


export default MyAthletes;
