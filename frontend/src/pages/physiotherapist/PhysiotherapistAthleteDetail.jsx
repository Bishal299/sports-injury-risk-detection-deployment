import React, { useEffect, useState } from "react";
import { ArrowLeft, HeartPulse, Plus, Save, Trash2, X } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import {
  createRehabilitationActivity,
  createPhysiotherapistNote,
  createRehabilitationPlan,
  deleteRehabilitationActivity,
  getPhysiotherapistAthleteDetail,
  updateRehabilitationActivity,
  updateRehabilitationPlan,
} from "../../services/api";
import "../../styles/coach.css";

const phases = ["ASSESSMENT", "MOBILITY", "STRENGTH", "BALANCE_STABILITY", "MOVEMENT_CORRECTION", "SPORT_SPECIFIC_TRAINING", "RETURN_TO_SPORT"];
const statuses = ["ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"];
const activityStatuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED"];
const priorities = ["LOW", "MEDIUM", "HIGH"];
const emptyActivityForm = {
  title: "",
  description: "",
  phase: "ASSESSMENT",
  due_date: "",
  priority: "MEDIUM",
  status: "PENDING",
};

function formatDate(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function score(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Not Available";
  return Number(value).toFixed(1);
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

function PhysiotherapistAthleteDetail() {
  const { athleteId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [detail, setDetail] = useState(null);
  const [planForm, setPlanForm] = useState({});
  const [activityForm, setActivityForm] = useState(emptyActivityForm);
  const [editingActivityId, setEditingActivityId] = useState(null);
  const [noteForm, setNoteForm] = useState({ title: "", note: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadDetail() {
    const data = await getPhysiotherapistAthleteDetail(athleteId);
    setDetail(data);
    const plan = data.rehabilitation_plan;
    setPlanForm(plan ? {
      injury_context: plan.injury_context || "",
      start_date: plan.start_date || "",
      target_date: plan.target_date || "",
      current_phase: plan.current_phase || "ASSESSMENT",
      progress: plan.progress ?? 0,
      status: plan.status || "ACTIVE",
      recent_assessment: plan.recent_assessment || "",
      goals: Array.isArray(plan.goals) ? plan.goals.join("\n") : "",
      notes: plan.notes || "",
    } : {
      injury_context: "",
      start_date: "",
      target_date: "",
      current_phase: "ASSESSMENT",
      progress: 0,
      status: "ACTIVE",
      recent_assessment: "",
      goals: "",
      notes: "",
    });
  }

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getPhysiotherapistAthleteDetail(athleteId);
        if (!cancelled) {
          setDetail(data);
          const plan = data.rehabilitation_plan;
          setPlanForm(plan ? {
            injury_context: plan.injury_context || "",
            start_date: plan.start_date || "",
            target_date: plan.target_date || "",
            current_phase: plan.current_phase || "ASSESSMENT",
            progress: plan.progress ?? 0,
            status: plan.status || "ACTIVE",
            recent_assessment: plan.recent_assessment || "",
            goals: Array.isArray(plan.goals) ? plan.goals.join("\n") : "",
            notes: plan.notes || "",
          } : {
            injury_context: "", start_date: "", target_date: "", current_phase: "ASSESSMENT", progress: 0, status: "ACTIVE", recent_assessment: "", goals: "", notes: "",
          });
        }
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load athlete.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [athleteId]);

  function listValue(value) {
    return String(value || "").split("\n").map((item) => item.trim()).filter(Boolean);
  }

  function resetActivityForm() {
    setActivityForm(emptyActivityForm);
    setEditingActivityId(null);
  }

  function editActivity(activity) {
    setEditingActivityId(activity.activity_id);
    setActivityForm({
      title: activity.title || "",
      description: activity.description || "",
      phase: activity.phase || "ASSESSMENT",
      due_date: activity.due_date || "",
      priority: activity.priority || "MEDIUM",
      status: activity.status || "PENDING",
    });
  }

  async function handleSavePlan(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    const payload = {
      ...planForm,
      progress: Number(planForm.progress || 0),
      goals: listValue(planForm.goals),
      start_date: planForm.start_date || null,
      target_date: planForm.target_date || null,
    };
    try {
      if (detail.rehabilitation_plan?.rehabilitation_plan_id) {
        await updateRehabilitationPlan(detail.rehabilitation_plan.rehabilitation_plan_id, payload);
      } else {
        await createRehabilitationPlan(athleteId, payload);
      }
      await loadDetail();
      setSuccess("Rehabilitation plan saved.");
    } catch (error) {
      setError(error.message || "Failed to save rehabilitation plan.");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddNote(event) {
    event.preventDefault();
    if (!noteForm.note.trim()) return;
    setSaving(true);
    setError("");
    try {
      await createPhysiotherapistNote(athleteId, noteForm);
      setNoteForm({ title: "", note: "" });
      await loadDetail();
      setSuccess("Note added.");
    } catch (error) {
      setError(error.message || "Failed to add note.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveActivity(event) {
    event.preventDefault();
    const planId = detail?.rehabilitation_plan?.rehabilitation_plan_id;
    if (!planId || !activityForm.title.trim()) return;

    setSaving(true);
    setError("");
    setSuccess("");
    const payload = {
      ...activityForm,
      title: activityForm.title.trim(),
      description: activityForm.description || null,
      due_date: activityForm.due_date || null,
    };

    try {
      if (editingActivityId) {
        await updateRehabilitationActivity(editingActivityId, payload);
        setSuccess("Activity updated.");
      } else {
        await createRehabilitationActivity(planId, payload);
        setSuccess("Activity added.");
      }
      resetActivityForm();
      await loadDetail();
    } catch (error) {
      setError(error.message || "Failed to save activity.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteActivity(activityId) {
    if (!window.confirm("Delete this rehabilitation activity?")) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await deleteRehabilitationActivity(activityId);
      if (editingActivityId === activityId) resetActivityForm();
      await loadDetail();
      setSuccess("Activity deleted.");
    } catch (error) {
      setError(error.message || "Failed to delete activity.");
    } finally {
      setSaving(false);
    }
  }

  const profile = detail?.profile;
  const risk = detail?.risk_monitoring || {};
  const notes = Array.isArray(detail?.notes) ? detail.notes : [];
  const activities = Array.isArray(detail?.rehabilitation_plan?.activities) ? detail.rehabilitation_plan.activities : [];
  const monitoring = detail?.rehabilitation_monitoring || {};
  const needsAttention = Array.isArray(detail?.needs_attention) ? detail.needs_attention : [];
  const timeline = Array.isArray(detail?.timeline)
    ? detail.timeline.filter((event) => event.type !== "movement_analysis")
    : [];
  const isRehabilitationWorkspace = location.pathname.startsWith("/physiotherapist/rehabilitation");
  const backPath = isRehabilitationWorkspace ? "/physiotherapist/rehabilitation" : "/physiotherapist/athletes";
  const backLabel = isRehabilitationWorkspace ? "Back to Rehabilitation" : "Back to My Athletes";

  return (
    <main className="coach-page">
        <button className="coach-back-button" type="button" onClick={() => navigate(backPath)}><ArrowLeft size={18} />{backLabel}</button>
        {loading && <section className="coach-empty-card">Loading athlete...</section>}
        {error && <section className="coach-error-card">{error}</section>}
        {success && <section className="coach-success-card">{success}</section>}

        {!loading && !error && profile && (
          <>
            <section className="coach-athlete-detail-header">
              <div><p className="page-eyebrow">CONNECTED ATHLETE</p><h1>{profile.name}</h1><p>{profile.sport || "Sport not set"}{profile.age ? ` · ${profile.age} years old` : ""}</p></div>
              <article className={`coach-current-risk ${String(risk.risk_category || "not-available").toLowerCase()}`}><span>Current Risk</span><strong>{score(risk.current_risk)}</strong><p>{risk.risk_category}</p></article>
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading">
                <div>
                  <h2>Rehabilitation Overview</h2>
                  <p>Recovery management for this connected athlete.</p>
                </div>
              </div>
              <div className="coach-performance-grid">
                <div className="coach-metric-card"><span>Current Risk</span><strong>{score(risk.current_risk)}</strong></div>
                <div className="coach-metric-card"><span>Risk Category</span><strong>{risk.risk_category || "Not Available"}</strong></div>
                <div className="coach-metric-card"><span>Activity Completion</span><strong>{monitoring.activity_count ? `${monitoring.completed_activity_count || 0}/${monitoring.activity_count}` : "No activities"}</strong></div>
                <div className="coach-metric-card"><span>Recovery Progress</span><strong>{monitoring.progress_available ? `${Number(monitoring.calculated_progress || 0).toFixed(0)}%` : "Not Available"}</strong></div>
              </div>
            </section>

            <section className="coach-detail-grid">
              <article className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Plan Status</h2><p>Current rehabilitation state.</p></div></div>
                <div className="coach-performance-grid">
                  <div className="coach-metric-card"><span>Current Phase</span><strong>{formatLabel(monitoring.current_phase)}</strong></div>
                  <div className="coach-metric-card"><span>Status</span><strong>{detail.rehabilitation_plan?.status || "NOT STARTED"}</strong></div>
                  <div className="coach-metric-card"><span>Start Date</span><strong>{formatDate(detail.rehabilitation_plan?.start_date)}</strong></div>
                  <div className="coach-metric-card"><span>Review Date</span><strong>{formatDate(monitoring.next_review_date)}</strong></div>
                </div>
              </article>

              <article className="coach-panel-card">
                <div className="coach-section-heading"><div><h2>Goals</h2><p>Plan goals recorded for recovery.</p></div></div>
                {Array.isArray(detail.rehabilitation_plan?.goals) && detail.rehabilitation_plan.goals.length > 0 ? (
                  detail.rehabilitation_plan.goals.map((goal, index) => (
                    <article className="coach-report-row" key={`${goal}-${index}`}>
                      <div><strong>{goal}</strong><p>Goal {index + 1}</p></div>
                    </article>
                  ))
                ) : (
                  <div className="coach-quiet-state">No rehabilitation goals added yet.</div>
                )}
              </article>
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading"><div><h2>Rehabilitation</h2><p>{detail.rehabilitation_plan ? "View and update your active rehabilitation plan." : "Create a rehabilitation plan for this athlete."}</p></div><HeartPulse size={22} /></div>
              {detail.rehabilitation_plan && (
                <div className="coach-rehab-monitoring">
                  <div className="coach-rehab-progress-row">
                    <span>Activity Completion</span>
                    <strong>{monitoring.activity_count ? `${monitoring.completed_activity_count || 0}/${monitoring.activity_count}` : "No activities"}</strong>
                    <p>Completed and pending activities from this plan.</p>
                  </div>
                  <div className="coach-performance-grid">
                    <div className="coach-metric-card"><span>Rehabilitation Progress</span><strong>{monitoring.progress_available ? `${Number(monitoring.calculated_progress || 0).toFixed(0)}%` : "Not Available"}</strong></div>
                    <div className="coach-metric-card"><span>Current Phase</span><strong>{formatLabel(monitoring.current_phase)}</strong></div>
                    <div className="coach-metric-card"><span>Completed</span><strong>{monitoring.completed_activity_count || 0}</strong></div>
                    <div className="coach-metric-card"><span>Pending</span><strong>{monitoring.pending_activity_count || 0}</strong></div>
                    <div className="coach-metric-card"><span>Recent Rehab Activity</span><strong>{monitoring.recent_rehabilitation_activity?.title || "Not Available"}</strong></div>
                    <div className="coach-metric-card"><span>Next Review</span><strong>{formatDate(monitoring.next_review_date)}</strong></div>
                  </div>
                </div>
              )}
              {needsAttention.length > 0 && (
                <div className="coach-attention-list">
                  {needsAttention.map((item, index) => (
                    <article className="coach-attention-row" key={`${item.type}-${index}`}>
                      <div>
                        <strong>{item.title}</strong>
                        <p>{item.detail}</p>
                      </div>
                      <span className={`coach-risk-text ${String(item.severity || "").toLowerCase()}`}>{item.severity || "Attention"}</span>
                    </article>
                  ))}
                </div>
              )}
              <form className="coach-form-card" onSubmit={handleSavePlan}>
                <div className="coach-field-grid">
                  <label><span>Plan Title</span><input value={planForm.injury_context || ""} onChange={(event) => setPlanForm({ ...planForm, injury_context: event.target.value })} placeholder="e.g. ACL return-to-sport rehabilitation" /></label>
                  <label><span>Start Date</span><input type="date" value={planForm.start_date || ""} onChange={(event) => setPlanForm({ ...planForm, start_date: event.target.value })} /></label>
                  <label><span>Target / Review Date</span><input type="date" value={planForm.target_date || ""} onChange={(event) => setPlanForm({ ...planForm, target_date: event.target.value })} /></label>
                  <label><span>Current Phase</span><select value={planForm.current_phase || "ASSESSMENT"} onChange={(event) => setPlanForm({ ...planForm, current_phase: event.target.value })}>{phases.map((phase) => <option key={phase} value={phase}>{phase.replaceAll("_", " ")}</option>)}</select></label>
                  <label><span>Status</span><select value={planForm.status || "ACTIVE"} onChange={(event) => setPlanForm({ ...planForm, status: event.target.value })}>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                </div>
                <label className="coach-textarea-field"><span>Description</span><textarea rows="3" value={planForm.recent_assessment || ""} onChange={(event) => setPlanForm({ ...planForm, recent_assessment: event.target.value })} placeholder="Brief rehabilitation context, review focus, or current clinical summary." /></label>
                <label className="coach-textarea-field"><span>Goals</span><textarea rows="3" value={planForm.goals || ""} onChange={(event) => setPlanForm({ ...planForm, goals: event.target.value })} placeholder="Add one goal per line." /></label>
                <label className="coach-textarea-field"><span>Professional Notes</span><textarea rows="3" value={planForm.notes || ""} onChange={(event) => setPlanForm({ ...planForm, notes: event.target.value })} placeholder="Private professional notes for this rehabilitation plan." /></label>
                <div className="coach-form-actions"><button className="primary-button" disabled={saving} type="submit"><Save size={17} />{saving ? "Saving..." : "Save Plan"}</button></div>
              </form>

              {detail.rehabilitation_plan && (
                <div className="coach-activity-manager">
                  <div className="coach-section-heading compact">
                    <div>
                      <h2>Activities</h2>
                      <p>Add rehabilitation activities for the athlete to complete.</p>
                    </div>
                  </div>
                  <form className="coach-form-card" onSubmit={handleSaveActivity}>
                    <div className="coach-field-grid">
                      <label><span>Activity Title</span><input value={activityForm.title} onChange={(event) => setActivityForm({ ...activityForm, title: event.target.value })} placeholder="e.g. Mobility drill set" /></label>
                      <label><span>Phase</span><select value={activityForm.phase} onChange={(event) => setActivityForm({ ...activityForm, phase: event.target.value })}>{phases.map((phase) => <option key={phase} value={phase}>{phase.replaceAll("_", " ")}</option>)}</select></label>
                      <label><span>Due Date</span><input type="date" value={activityForm.due_date || ""} onChange={(event) => setActivityForm({ ...activityForm, due_date: event.target.value })} /></label>
                      <label><span>Priority</span><select value={activityForm.priority} onChange={(event) => setActivityForm({ ...activityForm, priority: event.target.value })}>{priorities.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                      <label><span>Status</span><select value={activityForm.status} onChange={(event) => setActivityForm({ ...activityForm, status: event.target.value })}>{activityStatuses.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
                    </div>
                    <label className="coach-textarea-field"><span>Instructions</span><textarea rows="3" value={activityForm.description || ""} onChange={(event) => setActivityForm({ ...activityForm, description: event.target.value })} placeholder="Brief instructions for the athlete." /></label>
                    <div className="coach-form-actions">
                      {editingActivityId && <button className="secondary-button compact" type="button" onClick={resetActivityForm}><X size={15} />Cancel</button>}
                      <button className="primary-button" disabled={saving || !activityForm.title.trim()} type="submit"><Save size={17} />{editingActivityId ? "Update Activity" : "Add Activity"}</button>
                    </div>
                  </form>

                  {activities.length === 0 ? (
                    <div className="coach-quiet-state">No rehabilitation activities added yet.</div>
                  ) : (
                    <div className="coach-activity-list">
                      {activities.map((activity) => (
                        <article className="coach-activity-row" key={activity.activity_id}>
                          <div>
                            <strong>{activity.title}</strong>
                            <p>{activity.description || "No instructions added."}</p>
                            {activity.athlete_notes && <p className="coach-activity-note">Athlete note: {activity.athlete_notes}</p>}
                          </div>
                          <span>{activity.phase.replaceAll("_", " ")}</span>
                          <span className={`athlete-rehab-status ${String(activity.status || "").toLowerCase()}`}>{activity.status.replaceAll("_", " ")}</span>
                          <div className="coach-report-actions">
                            <button className="secondary-button compact" type="button" onClick={() => editActivity(activity)}>Edit</button>
                            <button className="secondary-button compact danger" type="button" onClick={() => handleDeleteActivity(activity.activity_id)}><Trash2 size={15} />Delete</button>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading"><div><h2>Recovery Timeline</h2><p>Stored rehabilitation, activity, and review events.</p></div></div>
              {timeline.length === 0 ? <div className="coach-quiet-state">No recovery timeline events yet.</div> : (
                <div className="coach-timeline-list">
                  {timeline.slice(0, 10).map((event, index) => (
                    <article className="coach-report-row" key={`${event.type}-${index}`}>
                      <div>
                        <strong>{event.title}</strong>
                        <p>{formatLabel(event.type)}</p>
                      </div>
                      <span>{formatDate(event.date)}</span>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="coach-panel-card">
              <div className="coach-section-heading"><div><h2>Physiotherapist Notes</h2><p>Notes are separate from automated injury-risk scoring.</p></div></div>
              <form className="coach-form-card" onSubmit={handleAddNote}>
                <div className="coach-field-grid"><label><span>Title</span><input value={noteForm.title} onChange={(event) => setNoteForm({ ...noteForm, title: event.target.value })} /></label></div>
                <label className="coach-textarea-field"><span>Note</span><textarea rows="3" value={noteForm.note} onChange={(event) => setNoteForm({ ...noteForm, note: event.target.value })} /></label>
                <div className="coach-form-actions"><button className="primary-button" disabled={saving} type="submit"><Plus size={17} />Add Note</button></div>
              </form>
              {notes.length === 0 ? <div className="coach-quiet-state">No notes yet.</div> : notes.map((note) => <article className="coach-report-row" key={note.note_id}><div><strong>{note.title || "Note"}</strong><p>{note.note}</p></div><span>{formatDate(note.created_at)}</span></article>)}
            </section>
          </>
        )}
    </main>
  );
}


export default PhysiotherapistAthleteDetail;
