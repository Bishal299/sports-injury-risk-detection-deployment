import React, { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";

import {
  acceptPhysiotherapistAssignedRequest,
  getPhysiotherapistSentRequests,
  rejectPhysiotherapistAssignedRequest,
} from "../../services/api";
import "../../styles/coach.css";


function PhysiotherapistRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [workingId, setWorkingId] = useState("");
  const [success, setSuccess] = useState("");

  const loadRequests = async (cancelled = false) => {
      try {
        const data = await getPhysiotherapistSentRequests();
        if (!cancelled) setRequests(Array.isArray(data) ? data : []);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load requests.");
      } finally {
        if (!cancelled) setLoading(false);
      }
  };

  useEffect(() => {
    let cancelled = false;
    loadRequests(cancelled);
    return () => { cancelled = true; };
  }, []);

  const updateAssignedRequest = async (relationshipId, action, message) => {
    setWorkingId(relationshipId);
    setError("");
    setSuccess("");

    try {
      await action(relationshipId);
      await loadRequests(false);
      setSuccess(message);
    } catch (error) {
      setError(error.message || "Failed to update request.");
    } finally {
      setWorkingId("");
    }
  };

  return (
    <main className="coach-page">
        <section className="coach-page-header"><p className="page-eyebrow">ATHLETE REQUESTS</p><h1>Requests</h1><p>Track physiotherapy connection requests sent to athletes.</p></section>
        {error && <section className="coach-error-card">{error}</section>}
        {success && <section className="coach-success-card">{success}</section>}
        {loading && <section className="coach-empty-card">Loading requests...</section>}
        {!loading && requests.length === 0 && <section className="coach-empty-card"><h2>No requests yet</h2><p>Requests sent from Discover Athletes will appear here.</p></section>}
        {!loading && requests.length > 0 && (
          <section className="coach-list-card">
            {requests.map((request) => {
              const assignedByCoach = request.requested_by_role === "Coach" || request.requested_by_role === "COACH";
              const canRespond = assignedByCoach && request.status === "PENDING";

              return (
                <article className="coach-list-row" key={request.relationship_id}>
                  <div className="coach-icon-box"><ClipboardList size={20} /></div>
                  <div>
                    <h2>{request.athlete_name || "Athlete"}</h2>
                    <p>
                      {request.athlete_sport || request.professional_role}
                      {assignedByCoach ? ` · Assigned by Coach${request.requested_by_name ? ` ${request.requested_by_name}` : ""}` : ""}
                    </p>
                  </div>
                  <div className="coach-request-actions">
                    <span className={`coach-connected-badge ${request.status.toLowerCase()}`}>{request.status}</span>
                    {canRespond && (
                      <>
                        <button
                          className="secondary-button compact"
                          disabled={workingId === request.relationship_id}
                          onClick={() => updateAssignedRequest(
                            request.relationship_id,
                            rejectPhysiotherapistAssignedRequest,
                            "Physiotherapist assignment rejected."
                          )}
                          type="button"
                        >
                          Reject
                        </button>
                        <button
                          className="primary-button compact"
                          disabled={workingId === request.relationship_id}
                          onClick={() => updateAssignedRequest(
                            request.relationship_id,
                            acceptPhysiotherapistAssignedRequest,
                            "Physiotherapist assignment accepted."
                          )}
                          type="button"
                        >
                          Accept
                        </button>
                      </>
                    )}
                  </div>
                </article>
              );
            })}
          </section>
        )}
    </main>
  );
}


export default PhysiotherapistRequests;
