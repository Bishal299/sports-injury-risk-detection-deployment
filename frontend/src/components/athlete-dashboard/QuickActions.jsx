import React from "react";
import { Upload, UserRound, Video } from "lucide-react";

function QuickActions({ onNavigate }) {
  const actions = [
    {
      label: "Athlete Profile",
      path: "/athlete-profile",
      icon: UserRound,
    },
    {
      label: "Upload Video",
      path: "/video-upload",
      icon: Upload,
    },
    {
      label: "My Videos",
      path: "/my-videos",
      icon: Video,
    },
  ];

  return (
    <section className="athlete-dashboard-card">
      <div className="athlete-card-header">
        <div>
          <h2>Quick Actions</h2>
          <p>Jump back into the most common athlete workflows.</p>
        </div>
      </div>

      <div className="athlete-quick-actions">
        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <button
              className="athlete-action-button"
              key={action.path}
              onClick={() => onNavigate(action.path)}
              type="button"
            >
              <Icon size={18} />
              <span>{action.label}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export default QuickActions;
