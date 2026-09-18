import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BarChart3,
  Gauge,
  ListChecks,
  Search,
  Save,
  UserPlus,
  X,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import {
  assignPhysiotherapistToAthlete,
  cancelCoachAthleteTask,
  createCoachAthleteTask,
  getAssignablePhysiotherapists,
  getCoachAthleteDetail,
  getCoachAthletePhysiotherapists,
  getCoachAthleteTasks,
  updateCoachAthleteTask,
} from "../../services/api";
import "../../styles/coach.css";


function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}


function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Not Available";
  }

  return `${Number(value).toFixed(1)}%`;
}


function scoreValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Not Available";
  }

  return Number(value).toFixed(1);
}


function RiskCard({ profile }) {
  const category = profile?.risk_category || "Not Available";
  const score = profile?.latest_risk_score;
  const className = category.toLowerCase().replace(" ", "-");

  return (
    <article className={`coach-current-risk ${className}`}>
      <span>Current Risk</span>
      <strong>{score === null || score === undefined ? "Risk" : formatScore(score)}</strong>
      <p>{category === "Not Available" ? "Not Available" : category}</p>
    </article>
  );
}


function MetricCard({ label, value }) {
  return (
    <div className="coach-metric-card">
      <span>{label}</span>
      <strong>{scoreValue(value)}</strong>
    </div>
  );
}


function CoachAthleteDetail() {
  const { athleteId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [physiotherapists, setPhysiotherapists] = useState([]);
  const [assignablePhysios, setAssignablePhysios] = useState([]);
  const [physioSearch, setPhysioSearch] = useState("");
  const [physioLoading, setPhysioLoading] = useState(false);
  const [assignmentMessage, setAssignmentMessage] = useState("");
  const [assignmentError, setAssignmentError] = useState("");
  const [assigningId, setAssigningId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    due_date: "",
    priority: "MEDIUM",
    status: "ASSIGNED",
  });
  const [editingTaskId, setEditingTaskId] = useState("");
  const [taskMessage, setTaskMessage] = useState("");
  const [taskError, setTaskError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDetail() {
      try {
        const [data, physioRelationships, availablePhysios] = await Promise.all([
          getCoachAthleteDetail(athleteId),
          getCoachAthletePhysiotherapists(athleteId),
          getAssignablePhysiotherapists(athleteId),
        ]);
        if (!cancelled) {
          setDetail(data);
          setPhysiotherapists(Array.isArray(physioRelationships) ? physioRelationships : []);
          setAssignablePhysios(Array.isArray(availablePhysios) ? availablePhysios : []);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message || "Failed to load connected athlete.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDetail();

    return () => {
      cancelled = true;
    };
  }, [athleteId]);

  useEffect(() => {
    let cancelled = false;

    async function loadAssignablePhysios() {
      if (!detail) {
        return;
      }

      setPhysioLoading(true);
      try {
        const data = await getAssignablePhysiotherapists(athleteId, physioSearch);
        if (!cancelled) {
          setAssignablePhysios(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (!cancelled) {
          setAssignmentError(error.message || "Failed to load Physiotherapists.");
        }
      } finally {
        if (!cancelled) {
          setPhysioLoading(false);
        }
      }
    }

    const timer = window.setTimeout(loadAssignablePhysios, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [athleteId, detail, physioSearch]);

  const profile = detail?.profile;
  const latestAnalysis = detail?.latest_analysis;

  async function loadTasks() {
    const data = await getCoachAthleteTasks(athleteId);
    setTasks(Array.isArray(data) ? data : []);
  }

  useEffect(() => {
    if (!detail) return;

    let cancelled = false;
    async function load() {
      try {
        const data = await getCoachAthleteTasks(athleteId);
        if (!cancelled) setTasks(Array.isArray(data) ? data : []);
      } catch (error) {
        if (!cancelled) setTaskError(error.message || "Failed to load Coach tasks.");
      }
    }
    load();
    return () => { cancelled = true; };
  }, [athleteId, detail]);

  const performanceItems = useMemo(() => {
    const overview = detail?.performance_overview || {};
    return [
      ["Biomechanical", overview.biomechanical],
      ["Historical", overview.historical],
      ["Movement Asymmetry", overview.movement_asymmetry],
      ["Training Load", overview.training_load],
    ];
  }, [detail]);

  async function handleAssignPhysiotherapist(physiotherapistUserId) {
    setAssignmentError("");
    setAssignmentMessage("");
    setAssigningId(physiotherapistUserId);

    try {
      await assignPhysiotherapistToAthlete(athleteId, physiotherapistUserId);
      const [physioRelationships, availablePhysios] = await Promise.all([
        getCoachAthletePhysiotherapists(athleteId),
        getAssignablePhysiotherapists(athleteId, physioSearch),
      ]);
      setPhysiotherapists(Array.isArray(physioRelationships) ? physioRelationships : []);
      setAssignablePhysios(Array.isArray(availablePhysios) ? availablePhysios : []);
      setAssignmentMessage("Physiotherapist assignment request sent.");
    } catch (error) {
      setAssignmentError(error.message || "Failed to assign Physiotherapist.");
    } finally {
      setAssigningId("");
    }
  }

  function resetTaskForm() {
    setEditingTaskId("");
    setTaskForm({
      title: "",
      description: "",
      due_date: "",
      priority: "MEDIUM",
      status: "ASSIGNED",
    });
  }

  function editTask(task) {
    setEditingTaskId(task.task_id);
    setTaskForm({
      title: task.title || "",
      description: task.description || "",
      due_date: task.due_date || "",
      priority: task.priority || "MEDIUM",
      status: task.status || "ASSIGNED",
    });
  }

  async function handleSaveTask(event) {
    event.preventDefault();
    if (!taskForm.title.trim()) return;
    setTaskError("");
    setTaskMessage("");
    const payload = {
      ...taskForm,
      title: taskForm.title.trim(),
      description: taskForm.description || null,
      due_date: taskForm.due_date || null,
    };
    try {
      if (editingTaskId) {
        await updateCoachAthleteTask(editingTaskId, payload);
        setTaskMessage("Coach task updated.");
      } else {
        await createCoachAthleteTask(athleteId, payload);
        setTaskMessage("Coach task assigned.");
      }
      resetTaskForm();
      await loadTasks();
    } catch (error) {
      setTaskError(error.message || "Failed to save Coach task.");
    }
  }

  async function handleCancelTask(taskId) {
    setTaskError("");
    setTaskMessage("");
    try {
      await cancelCoachAthleteTask(taskId);
      await loadTasks();
      setTaskMessage("Coach task cancelled.");
    } catch (error) {
      setTaskError(error.message || "Failed to cancel Coach task.");
    }
  }

  return (
    <main className="coach-page">
        <button
          className="coach-back-button"
          type="button"
          onClick={() => navigate("/coach/athletes")}
        >
          <ArrowLeft size={18} />
          Back to My Athletes
        </button>

        {loading && <section className="coach-empty-card">Loading connected athlete...</section>}
        {error && <section className="coach-error-card">{error}</section>}

        {!loading && !error && profile && (
          <>
            <section className="coach-athlete-detail-header">
              <div>
                <p className="page-eyebrow">CONNECTED ATHLETE</p>
                <h1>{profile.name}</h1>
                <p>
                  {profile.sport || "Sport not set"}
                  {profile.age ? ` · ${profile.age} years old` : ""}
                </p>
              </div>
              <RiskCard profile={profile} />
            </section>

            <section className="coach-detail-grid">
              <article className="coach-panel-card">
                <div className="coach-section-heading">
                  <div>
                    <h2>Performance Overview</h2>
                    <p>Stored domain scores from the latest completed analysis.</p>
                  </div>
                  <Gauge size={22} />
                </div>
                <div className="coach-performance-grid">
                  {performanceItems.map(([label, value]) => (
                    <MetricCard key={label} label={label} value={value} />
                  ))}
                </div>
              </article>

              <article className="coach-panel-card">
                <div className="coach-section-heading">
                  <div>
                    <h2>Latest Analysis</h2>
                    <p>{latestAnalysis ? formatDate(latestAnalysis.completed_at || latestAnalysis.analysis_date) : "Not analyzed yet."}</p>
                  </div>
                  <BarChart3 size={22} />
                </div>

                {!latestAnalysis ? (
                  <div className="coach-quiet-state">No completed analysis is available.</div>
                ) : (
                  <div className="coach-performance-grid">
                    <MetricCard label="Risk Score" value={latestAnalysis.composite_risk_score ?? latestAnalysis.overall_risk_score} />
                    <MetricCard label="Movement Quality" value={latestAnalysis.movement_quality} />
                    <MetricCard label="Biomechanical" value={latestAnalysis.biomechanical_score} />
                    <MetricCard label="Asymmetry" value={latestAnalysis.asymmetry_score} />
                  </div>
                )}
              </article>
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Assign Physiotherapist</h2>
                  <p>Invite a verified Physiotherapist to support this connected athlete.</p>
                </div>
                <UserPlus size={22} />
              </div>

              {assignmentMessage && <div className="coach-success-card compact">{assignmentMessage}</div>}
              {assignmentError && <div className="coach-error-card compact">{assignmentError}</div>}

              {physiotherapists.length > 0 && (
                <div className="coach-assignment-status-list">
                  {physiotherapists.map((relationship) => (
                    <article className="coach-list-row compact" key={relationship.relationship_id}>
                      <div>
                        <h2>{relationship.professional_name || relationship.physiotherapist_name || "Physiotherapist"}</h2>
                        <p>
                          {relationship.organization || relationship.specialization || "Verified Physiotherapist"}
                          {relationship.requested_by_name ? ` · Assigned by ${relationship.requested_by_name}` : ""}
                        </p>
                      </div>
                      <span className={`coach-connected-badge ${relationship.status.toLowerCase()}`}>
                        {relationship.status === "ACTIVE" ? "Physiotherapist assigned" : "Pending assignment"}
                      </span>
                    </article>
                  ))}
                </div>
              )}

              <label className="coach-search-box">
                <Search size={17} />
                <input
                  value={physioSearch}
                  onChange={(event) => setPhysioSearch(event.target.value)}
                  placeholder="Search verified Physiotherapists"
                />
              </label>

              {physioLoading && <div className="coach-quiet-state">Loading Physiotherapists...</div>}

              {!physioLoading && assignablePhysios.length === 0 && (
                <div className="coach-quiet-state">No verified Physiotherapists found.</div>
              )}

              {!physioLoading && assignablePhysios.length > 0 && (
                <div className="coach-assignable-list">
                  {assignablePhysios.map((physio) => {
                    const alreadyLinked = physio.relationship_status === "PENDING" || physio.relationship_status === "ACTIVE";
                    return (
                      <article className="coach-list-row compact" key={physio.user_id}>
                        <div>
                          <h2>{physio.name}</h2>
                          <p>
                            {physio.specialization || "Physiotherapist"}
                            {physio.years_of_experience !== null && physio.years_of_experience !== undefined
                              ? ` · ${physio.years_of_experience} yrs`
                              : ""}
                            {physio.primary_sport ? ` · ${physio.primary_sport}` : ""}
                          </p>
                        </div>
                        <button
                          className="primary-button compact"
                          disabled={alreadyLinked || assigningId === physio.user_id}
                          onClick={() => handleAssignPhysiotherapist(physio.user_id)}
                          type="button"
                        >
                          {alreadyLinked
                            ? physio.relationship_status === "ACTIVE" ? "Assigned" : "Pending"
                            : assigningId === physio.user_id ? "Sending..." : "Assign"}
                        </button>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Coach Training Tasks</h2>
                  <p>Assigned by Coach. These are training tasks, not rehabilitation plans.</p>
                </div>
                <ListChecks size={22} />
              </div>

              {taskMessage && <div className="coach-success-card compact">{taskMessage}</div>}
              {taskError && <div className="coach-error-card compact">{taskError}</div>}

              <form className="coach-form-card" onSubmit={handleSaveTask}>
                <div className="coach-field-grid">
                  <label>
                    <span>Task Title</span>
                    <input value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} placeholder="e.g. Acceleration mechanics session" />
                  </label>
                  <label>
                    <span>Due Date</span>
                    <input type="date" value={taskForm.due_date} onChange={(event) => setTaskForm({ ...taskForm, due_date: event.target.value })} />
                  </label>
                  <label>
                    <span>Priority</span>
                    <select value={taskForm.priority} onChange={(event) => setTaskForm({ ...taskForm, priority: event.target.value })}>
                      {["LOW", "MEDIUM", "HIGH"].map((item) => <option key={item} value={item}>{item}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Status</span>
                    <select value={taskForm.status} onChange={(event) => setTaskForm({ ...taskForm, status: event.target.value })}>
                      {["ASSIGNED", "IN_PROGRESS", "COMPLETED", "OVERDUE", "CANCELLED"].map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}
                    </select>
                  </label>
                </div>
                <label className="coach-textarea-field">
                  <span>Instructions</span>
                  <textarea rows="3" value={taskForm.description} onChange={(event) => setTaskForm({ ...taskForm, description: event.target.value })} placeholder="Clear training instructions for the athlete." />
                </label>
                <div className="coach-form-actions">
                  {editingTaskId && <button className="secondary-button compact" type="button" onClick={resetTaskForm}><X size={15} />Cancel</button>}
                  <button className="primary-button" type="submit" disabled={!taskForm.title.trim()}><Save size={17} />{editingTaskId ? "Update Task" : "Assign Task"}</button>
                </div>
              </form>

              {tasks.length === 0 ? (
                <div className="coach-quiet-state">No Coach training tasks assigned yet.</div>
              ) : (
                <div className="coach-report-list">
                  {tasks.map((task) => (
                    <article className="coach-report-row" key={task.task_id}>
                      <div>
                        <strong>{task.title}</strong>
                        <p>{task.description || "No instructions added."}</p>
                        {task.athlete_notes && <p>Athlete note: {task.athlete_notes}</p>}
                      </div>
                      <span className={`athlete-rehab-status ${String(task.status || "").toLowerCase()}`}>{task.status.replaceAll("_", " ")}</span>
                      <div className="coach-report-actions">
                        <button className="secondary-button compact" type="button" onClick={() => editTask(task)}>Edit</button>
                        <button className="secondary-button compact danger" type="button" disabled={task.status === "CANCELLED"} onClick={() => handleCancelTask(task.task_id)}>Cancel</button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>

          </>
        )}
    </main>
  );
}


export default CoachAthleteDetail;
