import React, { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";

import { getCoachSentRequests } from "../../services/api";
import "../../styles/coach.css";


function CoachRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadRequests() {
      try {
        const data = await getCoachSentRequests();
        if (!cancelled) {
          setRequests(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message || "Failed to load Coach requests.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadRequests();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="coach-page">
        <section className="coach-page-header">
          <p className="page-eyebrow">ATHLETE REQUESTS</p>
          <h1>Requests</h1>
          <p>Track connection requests you have sent to athletes.</p>
        </section>

        {error && <section className="coach-error-card">{error}</section>}
        {loading && <section className="coach-empty-card">Loading requests...</section>}

        {!loading && requests.length === 0 && (
          <section className="coach-empty-card">
            <h2>No requests yet</h2>
            <p>Requests sent from Discover Athletes will appear here.</p>
          </section>
        )}

        {!loading && requests.length > 0 && (
          <section className="coach-list-card">
            {requests.map((request) => (
              <article className="coach-list-row" key={request.relationship_id}>
                <div className="coach-icon-box">
                  <ClipboardList size={20} />
                </div>
                <div>
                  <h2>{request.athlete_name || "Athlete"}</h2>
                  <p>{request.athlete_sport || "Sport not set"}</p>
                </div>
                <span className={`coach-connected-badge ${request.status.toLowerCase()}`}>
                  {request.status}
                </span>
              </article>
            ))}
          </section>
        )}
    </main>
  );
}


export default CoachRequests;
