import React, { useState } from "react";
import { BadgeCheck, ShieldCheck, XCircle } from "lucide-react";

import {
  acceptCoachRequest,
  acceptPhysiotherapistRequest,
  acceptSportsScientistRequest,
  rejectCoachRequest,
  rejectPhysiotherapistRequest,
  rejectSportsScientistRequest,
  revokeCoachAccess,
  revokePhysiotherapistAccess,
  revokeSportsScientistAccess,
} from "../../services/api";


function CoachConnections({
  requests,
  connections,
  physiotherapistRequests = [],
  connectedPhysiotherapists = [],
  sportsScientistRequests = [],
  connectedSportsScientists = [],
  onRefresh,
}) {
  const [workingId, setWorkingId] = useState("");
  const [error, setError] = useState("");
  const [expandedSections, setExpandedSections] = useState({});

  function visibleRows(sectionKey, rows) {
    return expandedSections[sectionKey] ? rows : rows.slice(0, 5);
  }

  function toggleSection(sectionKey) {
    setExpandedSections((current) => ({
      ...current,
      [sectionKey]: !current[sectionKey],
    }));
  }

  function showMoreButton(sectionKey, rows) {
    if (rows.length <= 5) return null;
    return (
      <button className="dashboard-show-more-button" type="button" onClick={() => toggleSection(sectionKey)}>
        {expandedSections[sectionKey] ? "Show Less" : `Show More (${rows.length - 5})`}
      </button>
    );
  }

  const runAction = async (relationshipId, action) => {
    setWorkingId(relationshipId);
    setError("");

    try {
      await action(relationshipId);
      await onRefresh?.();
    } catch (error) {
      setError(error.message || "Professional connection update failed.");
    } finally {
      setWorkingId("");
    }
  };

  const hasAnyRelationships =
    requests.length > 0 ||
    connections.length > 0 ||
    physiotherapistRequests.length > 0 ||
    connectedPhysiotherapists.length > 0 ||
    sportsScientistRequests.length > 0 ||
    connectedSportsScientists.length > 0;

  return (
    <section className="athlete-dashboard-card coach-connections-card">
      <div className="athlete-card-header">
        <div>
          <h2>Professional Requests / Connections</h2>
          <p>Approve or revoke professional access to your private athlete information.</p>
        </div>
        <div className="completion-icon">
          <ShieldCheck size={20} />
        </div>
      </div>

      {error && <div className="coach-connection-error">{error}</div>}

      {!hasAnyRelationships && (
        <div className="activity-empty">
          <ShieldCheck size={18} />
          <span>No professional requests or connected professionals yet.</span>
        </div>
      )}

      {requests.length > 0 && (
        <div className="coach-connection-section">
          <h3>Pending Coach Requests</h3>
          {visibleRows("coachRequests", requests).map((request) => (
            <article className="coach-connection-row" key={request.relationship_id}>
              <div>
                <strong>{request.coach_name || "Coach"}</strong>
                <span>
                  {request.primary_sport || "Sport not set"}
                  {request.years_of_experience !== null &&
                  request.years_of_experience !== undefined
                    ? ` • ${request.years_of_experience} yrs`
                    : ""}
                </span>
                {request.coaching_specialization && (
                  <p>{request.coaching_specialization}</p>
                )}
              </div>

              <div className="coach-connection-actions">
                <button
                  className="athlete-secondary-action"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, rejectCoachRequest)
                  }
                  type="button"
                >
                  <XCircle size={16} />
                  Reject
                </button>
                <button
                  className="athlete-action-button"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, acceptCoachRequest)
                  }
                  type="button"
                >
                  <BadgeCheck size={16} />
                  Accept
                </button>
              </div>
            </article>
          ))}
          {showMoreButton("coachRequests", requests)}
        </div>
      )}

      {connections.length > 0 && (
        <div className="coach-connection-section">
          <h3>Connected Coaches</h3>
          {visibleRows("coachConnections", connections).map((connection) => (
            <article className="coach-connection-row" key={connection.relationship_id}>
              <div>
                <strong>{connection.coach_name || "Coach"}</strong>
                <span>
                  {connection.organization || connection.primary_sport || "Verified Coach"}
                </span>
              </div>

              <button
                className="athlete-secondary-action danger-lite"
                disabled={workingId === connection.relationship_id}
                onClick={() =>
                  runAction(connection.relationship_id, revokeCoachAccess)
                }
                type="button"
              >
                Revoke Access
              </button>
            </article>
          ))}
          {showMoreButton("coachConnections", connections)}
        </div>
      )}

      {physiotherapistRequests.length > 0 && (
        <div className="coach-connection-section">
          <h3>Pending Physiotherapist Requests</h3>
          {visibleRows("physioRequests", physiotherapistRequests).map((request) => (
            <article className="coach-connection-row" key={request.relationship_id}>
              <div>
                <strong>{request.professional_name || request.physiotherapist_name || "Physiotherapist"}</strong>
                <span>
                  {request.primary_sport || "Physiotherapy"}
                  {request.years_of_experience !== null &&
                  request.years_of_experience !== undefined
                    ? ` • ${request.years_of_experience} yrs`
                    : ""}
                </span>
                {request.specialization && (
                  <p>{request.specialization}</p>
                )}
              </div>

              <div className="coach-connection-actions">
                <button
                  className="athlete-secondary-action"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, rejectPhysiotherapistRequest)
                  }
                  type="button"
                >
                  <XCircle size={16} />
                  Reject
                </button>
                <button
                  className="athlete-action-button"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, acceptPhysiotherapistRequest)
                  }
                  type="button"
                >
                  <BadgeCheck size={16} />
                  Accept
                </button>
              </div>
            </article>
          ))}
          {showMoreButton("physioRequests", physiotherapistRequests)}
        </div>
      )}

      {connectedPhysiotherapists.length > 0 && (
        <div className="coach-connection-section">
          <h3>Connected Physiotherapists</h3>
          {visibleRows("physioConnections", connectedPhysiotherapists).map((connection) => (
            <article className="coach-connection-row" key={connection.relationship_id}>
              <div>
                <strong>{connection.professional_name || connection.physiotherapist_name || "Physiotherapist"}</strong>
                <span>
                  {connection.organization || connection.primary_sport || "Verified Physiotherapist"}
                </span>
              </div>

              <button
                className="athlete-secondary-action danger-lite"
                disabled={workingId === connection.relationship_id}
                onClick={() =>
                  runAction(connection.relationship_id, revokePhysiotherapistAccess)
                }
                type="button"
              >
                Revoke Access
              </button>
            </article>
          ))}
          {showMoreButton("physioConnections", connectedPhysiotherapists)}
        </div>
      )}

      {sportsScientistRequests.length > 0 && (
        <div className="coach-connection-section">
          <h3>Pending Sports Scientist Requests</h3>
          {visibleRows("scientistRequests", sportsScientistRequests).map((request) => (
            <article className="coach-connection-row" key={request.relationship_id}>
              <div>
                <strong>{request.professional_name || "Sports Scientist"}</strong>
                <span>
                  {request.organization || request.primary_sport || "Sports science analysis"}
                  {request.years_of_experience !== null &&
                  request.years_of_experience !== undefined
                    ? ` • ${request.years_of_experience} yrs`
                    : ""}
                </span>
                {request.specialization && <p>{request.specialization}</p>}
              </div>

              <div className="coach-connection-actions">
                <button
                  className="athlete-secondary-action"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, rejectSportsScientistRequest)
                  }
                  type="button"
                >
                  <XCircle size={16} />
                  Reject
                </button>
                <button
                  className="athlete-action-button"
                  disabled={workingId === request.relationship_id}
                  onClick={() =>
                    runAction(request.relationship_id, acceptSportsScientistRequest)
                  }
                  type="button"
                >
                  <BadgeCheck size={16} />
                  Accept
                </button>
              </div>
            </article>
          ))}
          {showMoreButton("scientistRequests", sportsScientistRequests)}
        </div>
      )}

      {connectedSportsScientists.length > 0 && (
        <div className="coach-connection-section">
          <h3>Connected Sports Scientists</h3>
          {visibleRows("scientistConnections", connectedSportsScientists).map((connection) => (
            <article className="coach-connection-row" key={connection.relationship_id}>
              <div>
                <strong>{connection.professional_name || "Sports Scientist"}</strong>
                <span>
                  {connection.organization || connection.primary_sport || "Verified Sports Scientist"}
                </span>
              </div>

              <button
                className="athlete-secondary-action danger-lite"
                disabled={workingId === connection.relationship_id}
                onClick={() =>
                  runAction(connection.relationship_id, revokeSportsScientistAccess)
                }
                type="button"
              >
                Revoke Access
              </button>
            </article>
          ))}
          {showMoreButton("scientistConnections", connectedSportsScientists)}
        </div>
      )}
    </section>
  );
}


export default CoachConnections;
