import React, { useEffect, useState } from "react";
import { CalendarDays, CheckCircle2, HeartPulse, PlayCircle, UserRound } from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import { getMyRehabilitationPlans, updateMyRehabilitationActivity } from "../../services/api";
import "../../styles/dashboard.css";


function formatDate(value) {
  if (!value) {
    return "Not set";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}


function formatLabel(value) {
  if (!value) {
    return "Not Available";
  }

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}


function MyRehabilitation() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingActivityId, setSavingActivityId] = useState("");
  const [activityNotes, setActivityNotes] = useState({});
  const [error, setError] = useState("");

  async function loadPlans({ silent = false } = {}) {
    if (!silent) setLoading(true);
    try {
      const data = await getMyRehabilitationPlans();
      setPlans(Array.isArray(data) ? data : []);
      setError("");
    } catch (error) {
      setError(error.message || "Failed to load rehabilitation plans.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  function groupActivities(activities = []) {
    return activities.reduce((groups, activity) => {
      const phase = activity.phase || "OTHER";
      return {
        ...groups,
        [phase]: [...(groups[phase] || []), activity],
      };
    }, {});
  }

  async function updateActivity(activityId, status) {
    setSavingActivityId(activityId);
    setError("");

    try {
      await updateMyRehabilitationActivity(activityId, {
        status,
        athlete_notes: activityNotes[activityId] || null,
      });
      await loadPlans({ silent: true });
    } catch (error) {
      setError(error.message || "Failed to update activity.");
    } finally {
      setSavingActivityId("");
    }
  }

  return (
    <DashboardLayout>
      <main className="athlete-dashboard">
        <section className="athlete-dashboard-header">
          <div>
            <p className="page-eyebrow">ATHLETE</p>
            <h1>My Rehabilitation</h1>
            <p>View rehabilitation plans shared by your connected Physiotherapist.</p>
          </div>
        </section>

        {error && (
          <section className="dashboard-error-state compact">
            <HeartPulse size={24} />
            <p>{error}</p>
          </section>
        )}

        {loading && <section className="athlete-dashboard-card">Loading rehabilitation plans...</section>}

        {!loading && plans.length === 0 && (
          <section className="athlete-dashboard-card activity-empty">
            <HeartPulse size={20} />
            <span>No rehabilitation plan created yet.</span>
          </section>
        )}

        {!loading && plans.length > 0 && (
          <section className="dashboard-content-grid single-column">
            {plans.map((plan) => (
              <article className="athlete-dashboard-card" key={plan.rehabilitation_plan_id}>
                <div className="athlete-card-header">
                  <div>
                    <h2>{plan.title || "Rehabilitation Plan"}</h2>
                    <p>{plan.description || "No description provided."}</p>
                  </div>
                  <span className={`athlete-rehab-status ${String(plan.status || "").toLowerCase()}`}>
                    {plan.status}
                  </span>
                </div>

                <div className="athlete-rehab-grid">
                  <div>
                    <span>Progress</span>
                    <strong>
                      {plan.progress_available
                        ? `${Number(plan.calculated_progress || 0).toFixed(0)}%`
                        : "Progress not available"}
                    </strong>
                  </div>
                  <div>
                    <span>Current Phase</span>
                    <strong>{formatLabel(plan.current_phase)}</strong>
                  </div>
                  <div>
                    <span>Assigned Physiotherapist</span>
                    <strong>{plan.physiotherapist_name || "Physiotherapist"}</strong>
                  </div>
                  <div>
                    <span>Start Date</span>
                    <strong><CalendarDays size={15} /> {formatDate(plan.start_date)}</strong>
                  </div>
                  <div>
                    <span>Review Date</span>
                    <strong><CalendarDays size={15} /> {formatDate(plan.target_date)}</strong>
                  </div>
                </div>

                <div className="athlete-rehab-section">
                  <h3>Activities</h3>
                  {Array.isArray(plan.activities) && plan.activities.length > 0 ? (
                    <div className="athlete-activity-groups">
                      {Object.entries(groupActivities(plan.activities)).map(([phase, activities]) => (
                        <section className="athlete-activity-group" key={phase}>
                          <h4>{formatLabel(phase)}</h4>
                          {activities.map((activity) => (
                            <article className="athlete-activity-card" key={activity.activity_id}>
                              <div>
                                <div className="athlete-activity-title">
                                  <strong>{activity.title}</strong>
                                  <span className={`athlete-rehab-status ${String(activity.status || "").toLowerCase()}`}>
                                    {formatLabel(activity.status)}
                                  </span>
                                </div>
                                <p>{activity.description || "No instructions added."}</p>
                                <small>
                                  Priority: {formatLabel(activity.priority)}
                                  {activity.due_date ? ` · Due ${formatDate(activity.due_date)}` : ""}
                                </small>
                              </div>
                              <label className="athlete-activity-note">
                                <span>Completion note</span>
                                <textarea
                                  rows="2"
                                  value={activityNotes[activity.activity_id] ?? activity.athlete_notes ?? ""}
                                  onChange={(event) => setActivityNotes({
                                    ...activityNotes,
                                    [activity.activity_id]: event.target.value,
                                  })}
                                  placeholder="Optional note for your Physiotherapist"
                                />
                              </label>
                              <div className="athlete-activity-actions">
                                <button
                                  className="secondary-button compact"
                                  type="button"
                                  disabled={savingActivityId === activity.activity_id || activity.status === "IN_PROGRESS"}
                                  onClick={() => updateActivity(activity.activity_id, "IN_PROGRESS")}
                                >
                                  <PlayCircle size={15} />In Progress
                                </button>
                                <button
                                  className="primary-button compact"
                                  type="button"
                                  disabled={savingActivityId === activity.activity_id || activity.status === "COMPLETED"}
                                  onClick={() => updateActivity(activity.activity_id, "COMPLETED")}
                                >
                                  <CheckCircle2 size={15} />Completed
                                </button>
                              </div>
                            </article>
                          ))}
                        </section>
                      ))}
                    </div>
                  ) : (
                    <p>Progress not available. No rehabilitation activities added yet.</p>
                  )}
                </div>

                <div className="athlete-rehab-section">
                  <h3>Goals</h3>
                  {Array.isArray(plan.goals) && plan.goals.length > 0 ? (
                    <ul>
                      {plan.goals.map((goal, index) => (
                        <li key={`${goal}-${index}`}>{goal}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No goals added yet.</p>
                  )}
                </div>

                {plan.notes && (
                  <div className="athlete-rehab-section">
                    <h3><UserRound size={16} /> Professional Notes</h3>
                    <p>{plan.notes}</p>
                  </div>
                )}
              </article>
            ))}
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}


export default MyRehabilitation;
