import React from "react";

function DashboardStats({ stats }) {
  return (
    <div className="athlete-stats-grid">
      {stats.map((item) => {
        const Icon = item.icon;

        return (
          <section className="athlete-stat-card" key={item.label}>
            <div className="athlete-stat-icon">
              <Icon size={20} />
            </div>
            <div>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default DashboardStats;
