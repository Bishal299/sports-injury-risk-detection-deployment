import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  ClipboardList,
  FileText,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  AdminBarDistribution,
  AdminRecentList,
  AdminTimeSeriesChart,
  formatNumber,
} from "../../components/admin/AdminVisualizations";
import { getAdminDashboard } from "../../services/api";
import "../../styles/admin.css";

function formatDate(value) {
  if (!value) return "Recently";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Recently";
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function AdminDashboard() {
  const navigate = useNavigate();
  const [rangeDays, setRangeDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        const data = await getAdminDashboard({ range_days: rangeDays });
        if (!cancelled) setDashboard(data);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load admin dashboard.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [rangeDays]);

  const summary = dashboard?.summary || {};
  const cards = useMemo(
    () => [
      { label: "Total Users", value: summary.total_users, icon: UsersRound },
      { label: "Athletes", value: summary.athletes, icon: Activity },
      { label: "Active Professionals", value: summary.active_professionals, icon: ShieldCheck },
      { label: "Pending Professional Requests", value: summary.pending_professional_requests, icon: ClipboardList },
      { label: "Active Connections", value: summary.active_connections, icon: UsersRound },
      { label: "Completed Analyses", value: summary.completed_analyses, icon: BarChart3 },
    ],
    [summary]
  );

  const quickActions = [
    { label: "Professional Requests", path: "/admin/professional-requests", icon: ShieldCheck },
    { label: "User Management", path: "/admin/users", icon: UsersRound },
    { label: "Platform Analytics", path: "/admin/analytics", icon: BarChart3 },
    { label: "System Monitoring", path: "/admin/system-monitoring", icon: Activity },
    { label: "Report Management", path: "/admin/reports", icon: FileText },
  ];

  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN</p>
            <h1>Admin Dashboard</h1>
            <p>Monitor users, professionals, analyses, and overall platform activity.</p>
          </div>
          <label className="admin-range-select">
            <span>Range</span>
            <select value={rangeDays} onChange={(event) => setRangeDays(Number(event.target.value))}>
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
              <option value={365}>365 days</option>
            </select>
          </label>
        </section>

        {error && <section className="admin-error-card">{error}</section>}
        {loading && <section className="admin-empty-card">Loading admin dashboard...</section>}

        {!loading && !error && (
          <>
            <section className="admin-summary-grid">
              {cards.map((card) => {
                const Icon = card.icon;
                return (
                  <article className="admin-summary-card" key={card.label}>
                    <div className="admin-icon-box"><Icon size={21} /></div>
                    <div><span>{card.label}</span><strong>{formatNumber(card.value)}</strong></div>
                  </article>
                );
              })}
            </section>

            <section className="admin-chart-grid">
              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>User Distribution</h2><p>Current users by application role.</p></div></div>
                <AdminBarDistribution rows={dashboard?.user_distribution || []} emptyText="No user records are available." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Analysis Activity</h2><p>Completed analyses over the selected range.</p></div></div>
                <AdminTimeSeriesChart rows={dashboard?.analysis_activity || []} valueKey="completed_analyses" emptyText="No completed analysis activity is available for this range." ariaLabel="Completed analyses over the selected date range" />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Risk Distribution</h2><p>Completed analyses by existing risk band.</p></div></div>
                <AdminBarDistribution rows={dashboard?.risk_distribution || []} emptyText="No completed risk results are available." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Analyses by Sport</h2><p>Completed analyses grouped by athlete sport.</p></div></div>
                <AdminBarDistribution rows={dashboard?.analyses_by_sport || []} labelKey="sport" emptyText="No completed analyses have athlete sport data." />
              </article>
            </section>

            <section className="admin-lower-grid">
              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Recent Activity</h2><p>Real platform events from existing records.</p></div></div>
                <AdminRecentList
                  items={dashboard?.recent_activity || []}
                  limit={5}
                  emptyText="No recent platform activity is available."
                  renderItem={(item, index) => (
                      <div className="admin-activity-row" key={`${item.type}-${item.occurred_at}-${index}`}>
                        <div><strong>{item.title}</strong><span>{item.detail}</span></div>
                        <time>{formatDate(item.occurred_at)}</time>
                      </div>
                  )}
                />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Quick Actions</h2><p>Open common admin work areas.</p></div></div>
                <div className="admin-action-grid">
                  {quickActions.map((action) => {
                    const Icon = action.icon;
                    return (
                      <button className="admin-action-button" key={action.path} type="button" onClick={() => navigate(action.path)}>
                        <Icon size={18} />
                        <span>{action.label}</span>
                      </button>
                    );
                  })}
                </div>
              </article>
            </section>
          </>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminDashboard;
