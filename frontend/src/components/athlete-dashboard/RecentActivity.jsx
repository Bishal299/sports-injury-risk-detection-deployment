import React from "react";
import { Activity, Clock } from "lucide-react";

function RecentActivity({ activities, formatDateTime, onShowMore }) {
  const visibleActivities = activities.slice(0, 5);
  const hasMore = activities.length > visibleActivities.length;

  return (
    <section className="athlete-dashboard-card activity-card">
      <div className="athlete-card-header">
        <div>
          <h2>Recent Activity</h2>
          <p>Latest uploaded videos, completed analyses, and injury updates.</p>
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="activity-empty">
          <Activity size={22} />
          <p>No recent activity yet.</p>
        </div>
      ) : (
        <div className="activity-list">
          {visibleActivities.map((item) => {
            const Icon = item.icon || Activity;

            return (
              <div className="activity-item" key={item.id}>
                <div className="activity-icon">
                  <Icon size={16} />
                </div>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.detail}</span>
                </div>
                <time>
                  <Clock size={13} />
                  {formatDateTime(item.date)}
                </time>
              </div>
            );
          })}
          {hasMore && (
            <button className="dashboard-show-more-button" type="button" onClick={onShowMore}>
              Show More
            </button>
          )}
        </div>
      )}
    </section>
  );
}

export default RecentActivity;
