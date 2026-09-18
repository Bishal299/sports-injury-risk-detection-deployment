import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  ExternalLink,
  HeartPulse,
  PlayCircle,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  getMyCoachTasks,
  getMyRehabilitationPlans,
  updateMyCoachTask,
  updateMyRehabilitationActivity,
} from "../../services/api";
import "../../styles/dashboard.css";


const statusFilters = ["ALL", "PENDING", "IN_PROGRESS", "COMPLETED", "OVERDUE"];


function formatDate(value) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}


function formatLabel(value) {
  if (!value) return "Not Available";
  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}


function normalizedStatus(item, domain) {
  if (domain === "coach" && item.status === "ASSIGNED") return "PENDING";
  return item.status || "PENDING";
}


function isOverdue(item) {
  if (item.status === "OVERDUE") return true;
  if (!item.due_date && !item.target_date) return false;
  if (["COMPLETED", "CANCELLED", "SKIPPED"].includes(item.status)) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const checkDate = item.due_date || item.target_date;
  return new Date(checkDate) < today;
}


function matchesFilter(item, domain, activeFilter) {
  if (activeFilter === "ALL") return true;
  if (activeFilter === "OVERDUE") return isOverdue(item);
  return normalizedStatus(item, domain) === activeFilter;
}


function MyWork() {
  const [rehabPlans, setRehabPlans] = useState([]);
  const [coachTasks, setCoachTasks] = useState([]);
  const [domainTab, setDomainTab] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [notes, setNotes] = useState({});
  const [savingId, setSavingId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAllCoachTasks, setShowAllCoachTasks] = useState(false);
  const [showAllRehabPlans, setShowAllRehabPlans] = useState(false);

  async function loadWork({ silent = false } = {}) {
    if (!silent) setLoading(true);
    try {
      const [plans, tasks] = await Promise.all([
        getMyRehabilitationPlans(),
        getMyCoachTasks(),
      ]);
      setRehabPlans(Array.isArray(plans) ? plans : []);
      setCoachTasks(Array.isArray(tasks) ? tasks : []);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load your work.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    loadWork();
  }, []);

  const filteredCoachTasks = useMemo(
    () => coachTasks.filter((task) => matchesFilter(task, "coach", statusFilter)),
    [statusFilter, coachTasks],
  );

  const filteredRehabPlans = useMemo(() => {
    if (statusFilter === "ALL") return rehabPlans;
    return rehabPlans.filter((plan) => {
      if (statusFilter === "OVERDUE") {
        return isOverdue(plan) || (plan.activities || []).some((a) => isOverdue(a));
      }
      if (statusFilter === "PENDING") {
        return (
          plan.status === "PENDING" ||
          (plan.activities || []).some((a) => normalizedStatus(a, "rehab") === "PENDING")
        );
      }
      if (statusFilter === "IN_PROGRESS") {
        return (
          plan.status === "ACTIVE" ||
          plan.status === "IN_PROGRESS" ||
          (plan.activities || []).some((a) => a.status === "IN_PROGRESS")
        );
      }
      if (statusFilter === "COMPLETED") {
        return (
          plan.status === "COMPLETED" ||
          ((plan.activities || []).length > 0 &&
            (plan.activities || []).every((a) => a.status === "COMPLETED"))
        );
      }
      return normalizedStatus(plan, "rehab") === statusFilter;
    });
  }, [statusFilter, rehabPlans]);

  const visibleCoachTasks = useMemo(() => {
    return showAllCoachTasks ? filteredCoachTasks : filteredCoachTasks.slice(0, 5);
  }, [showAllCoachTasks, filteredCoachTasks]);

  const visibleRehabPlans = useMemo(() => {
    return showAllRehabPlans ? filteredRehabPlans : filteredRehabPlans.slice(0, 3);
  }, [showAllRehabPlans, filteredRehabPlans]);

  async function updateRehabActivity(activityId, status) {
    setSavingId(activityId);
    try {
      await updateMyRehabilitationActivity(activityId, {
        status,
        athlete_notes: notes[activityId] || null,
      });
      await loadWork({ silent: true });
    } catch (err) {
      setError(err.message || "Failed to update rehabilitation activity.");
    } finally {
      setSavingId("");
    }
  }

  async function updateCoachTask(taskId, status) {
    setSavingId(taskId);
    try {
      await updateMyCoachTask(taskId, {
        status,
        athlete_notes: notes[taskId] || null,
      });
      await loadWork({ silent: true });
    } catch (err) {
      setError(err.message || "Failed to update Coach task.");
    } finally {
      setSavingId("");
    }
  }

  return (
    <DashboardLayout>
      <main className="athlete-dashboard">
        <section className="athlete-dashboard-header">
          <div>
            <p className="page-eyebrow">ATHLETE</p>
            <h1>MY WORK</h1>
            <p>Manage tasks, recommendations, and rehabilitation plans assigned to you.</p>
          </div>
        </section>

        <section className="athlete-work-hub-controls" aria-label="Work filters and navigation">
          <div className="athlete-work-category-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={domainTab === "ALL"}
              className={domainTab === "ALL" ? "active" : ""}
              onClick={() => setDomainTab("ALL")}
            >
              All
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={domainTab === "COACH"}
              className={domainTab === "COACH" ? "active" : ""}
              onClick={() => setDomainTab("COACH")}
            >
              Coach Tasks <span className="athlete-count-badge">{coachTasks.length}</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={domainTab === "REHAB"}
              className={domainTab === "REHAB" ? "active" : ""}
              onClick={() => setDomainTab("REHAB")}
            >
              Rehabilitation <span className="athlete-count-badge">{rehabPlans.length}</span>
            </button>
          </div>

          <div className="athlete-work-filters" aria-label="Status filters">
            {statusFilters.map((filter) => (
              <button
                key={filter}
                className={statusFilter === filter ? "active" : ""}
                type="button"
                onClick={() => setStatusFilter(filter)}
              >
                {formatLabel(filter)}
              </button>
            ))}
          </div>
        </section>

        {error && (
          <section className="dashboard-error-state compact">
            <ClipboardList size={24} />
            <p>{error}</p>
          </section>
        )}

        {loading && <section className="athlete-dashboard-card">Loading your work...</section>}

        {!loading && (
          <section className="dashboard-content-grid single-column">
            {/* SECTION A: COACH TASKS / RECOMMENDATIONS */}
            {(domainTab === "ALL" || domainTab === "COACH") && (
              <article className="athlete-dashboard-card">
                <div className="athlete-card-header">
                  <div>
                    <h2><ClipboardList size={18} /> COACH TASKS</h2>
                    <p>Tasks and recommendations from your coaches.</p>
                  </div>
                  {filteredCoachTasks.length > 0 && (
                    <span className="athlete-count-badge">
                      {filteredCoachTasks.length} {filteredCoachTasks.length === 1 ? "task" : "tasks"}
                    </span>
                  )}
                </div>

                {coachTasks.length === 0 ? (
                  <div className="activity-empty">No tasks from your coaches yet.</div>
                ) : filteredCoachTasks.length === 0 ? (
                  <div className="activity-empty">No tasks from your coaches match this filter.</div>
                ) : (
                  <>
                    <div className="athlete-work-list">
                      {visibleCoachTasks.map((task) => (
                        <article className="athlete-work-row" key={task.task_id}>
                          <div>
                            <strong>{task.title}</strong>
                            <p>{task.description || "No instructions added."}</p>
                            <small>
                              {task.coach_name ? `Coach: ${task.coach_name}` : "Assigned by Coach"}
                              {task.created_at ? ` · Assigned ${formatDate(task.created_at)}` : ""}
                            </small>
                          </div>
                          <div className="athlete-work-meta">
                            <span>Due {formatDate(task.due_date)}</span>
                            <span>Priority {formatLabel(task.priority)}</span>
                          </div>
                          <span
                            className={`athlete-rehab-status ${isOverdue(task) ? "overdue" : String(task.status || "").toLowerCase()}`}
                          >
                            {isOverdue(task) ? "Overdue" : formatLabel(normalizedStatus(task, "coach"))}
                          </span>
                          <label className="athlete-activity-note">
                            <span>Note</span>
                            <textarea
                              rows="2"
                              value={notes[task.task_id] ?? task.athlete_notes ?? ""}
                              onChange={(event) =>
                                setNotes({ ...notes, [task.task_id]: event.target.value })
                              }
                              placeholder="Optional note for your coach..."
                            />
                          </label>
                          <div className="athlete-activity-actions">
                            <button
                              className="secondary-button compact"
                              type="button"
                              disabled={
                                savingId === task.task_id ||
                                task.status === "IN_PROGRESS" ||
                                task.status === "CANCELLED" ||
                                task.status === "COMPLETED"
                              }
                              onClick={() => updateCoachTask(task.task_id, "IN_PROGRESS")}
                            >
                              <PlayCircle size={15} />Start
                            </button>
                            <button
                              className="primary-button compact"
                              type="button"
                              disabled={
                                savingId === task.task_id ||
                                task.status === "COMPLETED" ||
                                task.status === "CANCELLED"
                              }
                              onClick={() => updateCoachTask(task.task_id, "COMPLETED")}
                            >
                              <CheckCircle2 size={15} />Complete
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>

                    {filteredCoachTasks.length > 5 && (
                      <div className="athlete-work-more-row">
                        <button
                          type="button"
                          className="secondary-button compact"
                          onClick={() => setShowAllCoachTasks((prev) => !prev)}
                        >
                          {showAllCoachTasks
                            ? "Show Less"
                            : `Show More (${filteredCoachTasks.length - 5} more)`}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </article>
            )}

            {/* SECTION B: REHABILITATION PLANS */}
            {(domainTab === "ALL" || domainTab === "REHAB") && (
              <article className="athlete-dashboard-card">
                <div className="athlete-card-header">
                  <div>
                    <h2><HeartPulse size={18} /> REHABILITATION PLANS</h2>
                    <p>Plans and recovery work assigned by your physiotherapist.</p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {filteredRehabPlans.length > 0 && (
                      <span className="athlete-count-badge">
                        {filteredRehabPlans.length} {filteredRehabPlans.length === 1 ? "plan" : "plans"}
                      </span>
                    )}
                    <Link
                      to="/my-rehabilitation"
                      className="secondary-button compact"
                      title="Open complete rehabilitation hub"
                    >
                      <ExternalLink size={14} /> View Complete Plan
                    </Link>
                  </div>
                </div>

                {rehabPlans.length === 0 ? (
                  <div className="activity-empty">No rehabilitation plans yet.</div>
                ) : filteredRehabPlans.length === 0 ? (
                  <div className="activity-empty">No rehabilitation plans match this filter.</div>
                ) : (
                  <>
                    <div style={{ display: "grid", gap: "16px" }}>
                      {visibleRehabPlans.map((plan) => {
                        const planActivities = (plan.activities || []).filter((a) =>
                          matchesFilter(a, "rehab", statusFilter)
                        );
                        return (
                          <div
                            key={plan.rehabilitation_plan_id}
                            style={{
                              padding: "16px",
                              borderRadius: "var(--radius-sm)",
                              border: "1px solid var(--border-color)",
                              background: "var(--bg-tertiary)",
                              display: "grid",
                              gap: "12px",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                                flexWrap: "wrap",
                                gap: "10px",
                              }}
                            >
                              <div>
                                <strong style={{ fontSize: "1.05rem", color: "var(--text-primary)" }}>
                                  {plan.title || plan.injury_context || "Rehabilitation Plan"}
                                </strong>
                                <p
                                  style={{
                                    margin: "4px 0 0",
                                    color: "var(--text-secondary)",
                                    fontSize: "0.85rem",
                                  }}
                                >
                                  {plan.physiotherapist_name
                                    ? `Physiotherapist: ${plan.physiotherapist_name}`
                                    : "Assigned by Physiotherapist"}
                                  {plan.created_at ? ` · Created ${formatDate(plan.created_at)}` : ""}
                                </p>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <span
                                  className={`athlete-rehab-status ${String(plan.status || "").toLowerCase()}`}
                                >
                                  {formatLabel(plan.status)}
                                </span>
                                <Link
                                  to="/my-rehabilitation"
                                  className="secondary-button compact"
                                  title="View complete rehabilitation plan"
                                >
                                  <ExternalLink size={13} /> View Complete Plan
                                </Link>
                              </div>
                            </div>

                            <div className="athlete-rehab-grid">
                              <div>
                                <span>Current Phase</span>
                                <strong>{formatLabel(plan.current_phase)}</strong>
                              </div>
                              <div>
                                <span>Progress</span>
                                <strong>
                                  {plan.progress_available
                                    ? `${Number(plan.calculated_progress || 0).toFixed(0)}%`
                                    : "Progress not available"}
                                </strong>
                              </div>
                              <div>
                                <span>Start Date</span>
                                <strong><CalendarDays size={14} /> {formatDate(plan.start_date)}</strong>
                              </div>
                              <div>
                                <span>Review Date</span>
                                <strong><CalendarDays size={14} /> {formatDate(plan.target_date)}</strong>
                              </div>
                              <div>
                                <span>Pending Activities</span>
                                <strong>
                                  {(plan.activities || []).filter((a) => a.status !== "COMPLETED").length}
                                </strong>
                              </div>
                            </div>

                            {plan.description && (
                              <p
                                style={{
                                  margin: "0",
                                  color: "var(--text-secondary)",
                                  fontSize: "0.86rem",
                                  lineHeight: "1.45",
                                }}
                              >
                                {plan.description}
                              </p>
                            )}

                            {/* Plan activities list */}
                            {planActivities.length > 0 && (
                              <div style={{ marginTop: "6px" }}>
                                <div
                                  style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    marginBottom: "8px",
                                  }}
                                >
                                  <span
                                    style={{
                                      fontSize: "0.78rem",
                                      fontWeight: "700",
                                      color: "var(--text-secondary)",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                    }}
                                  >
                                    Assigned Activities ({planActivities.length})
                                  </span>
                                </div>
                                <div className="athlete-work-list">
                                  {planActivities.slice(0, 4).map((activity) => (
                                    <article className="athlete-work-row" key={activity.activity_id}>
                                      <div>
                                        <strong>{activity.title}</strong>
                                        <p>{activity.description || "No instructions added."}</p>
                                        <small>
                                          {formatLabel(activity.phase)} · Priority {formatLabel(activity.priority)}
                                          {activity.due_date ? ` · Due ${formatDate(activity.due_date)}` : ""}
                                        </small>
                                      </div>
                                      <span
                                        className={`athlete-rehab-status ${isOverdue(activity) ? "overdue" : String(activity.status || "").toLowerCase()}`}
                                      >
                                        {isOverdue(activity) ? "Overdue" : formatLabel(activity.status)}
                                      </span>
                                      <label className="athlete-activity-note">
                                        <span>Note</span>
                                        <textarea
                                          rows="2"
                                          value={notes[activity.activity_id] ?? activity.athlete_notes ?? ""}
                                          onChange={(event) =>
                                            setNotes({ ...notes, [activity.activity_id]: event.target.value })
                                          }
                                          placeholder="Optional note for your physiotherapist..."
                                        />
                                      </label>
                                      <div className="athlete-activity-actions">
                                        <button
                                          className="secondary-button compact"
                                          type="button"
                                          disabled={
                                            savingId === activity.activity_id ||
                                            activity.status === "IN_PROGRESS" ||
                                            activity.status === "COMPLETED"
                                          }
                                          onClick={() => updateRehabActivity(activity.activity_id, "IN_PROGRESS")}
                                        >
                                          <PlayCircle size={15} />Start
                                        </button>
                                        <button
                                          className="primary-button compact"
                                          type="button"
                                          disabled={
                                            savingId === activity.activity_id ||
                                            activity.status === "COMPLETED"
                                          }
                                          onClick={() => updateRehabActivity(activity.activity_id, "COMPLETED")}
                                        >
                                          <CheckCircle2 size={15} />Complete
                                        </button>
                                      </div>
                                    </article>
                                  ))}
                                </div>
                                {planActivities.length > 4 && (
                                  <div style={{ textAlign: "center", marginTop: "10px" }}>
                                    <Link
                                      to="/my-rehabilitation"
                                      className="secondary-button compact"
                                      style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                                    >
                                      <ExternalLink size={14} /> View All {planActivities.length} Activities
                                    </Link>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {filteredRehabPlans.length > 3 && (
                      <div className="athlete-work-more-row">
                        <button
                          type="button"
                          className="secondary-button compact"
                          onClick={() => setShowAllRehabPlans((prev) => !prev)}
                        >
                          {showAllRehabPlans
                            ? "Show Less Plans"
                            : `Show More Plans (${filteredRehabPlans.length - 3} more)`}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </article>
            )}
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}


export default MyWork;
