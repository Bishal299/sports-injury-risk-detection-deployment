import React from "react";
import { CheckCircle2, ClipboardList } from "lucide-react";

function ProfileCompletion({ completion, onComplete }) {
  const missingText = completion.missingLabels.length
    ? completion.missingLabels.slice(0, 3).join(", ")
    : "All key fields completed";

  return (
    <section className="athlete-dashboard-card compact-card">
      <div className="athlete-card-header">
        <div>
          <h2>Profile Completion</h2>
          <p>Based on sport, position, body metrics, and training indicators.</p>
        </div>
        <div className="completion-icon">
          {completion.percent === 100 ? (
            <CheckCircle2 size={20} />
          ) : (
            <ClipboardList size={20} />
          )}
        </div>
      </div>

      <div className="completion-row">
        <strong>{completion.percent}%</strong>
        <span>{completion.completed}/{completion.total} fields</span>
      </div>

      <div className="completion-track" aria-hidden="true">
        <div
          className="completion-fill"
          style={{ width: `${completion.percent}%` }}
        />
      </div>

      <p className="completion-missing">{missingText}</p>

      {completion.percent < 100 && (
        <button
          className="athlete-secondary-action"
          onClick={onComplete}
          type="button"
        >
          Complete Profile
        </button>
      )}
    </section>
  );
}

export default ProfileCompletion;
