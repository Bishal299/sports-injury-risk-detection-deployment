import React, { useEffect, useMemo, useState } from "react";
import { Activity, BarChart3, ShieldCheck, Upload, UsersRound } from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  AdminBarDistribution,
  AdminTimeSeriesChart,
  formatNumber,
} from "../../components/admin/AdminVisualizations";
import { getAdminPlatformAnalytics } from "../../services/api";
import "../../styles/admin.css";


const rangeOptions = [
  { label: "7 Days", value: "7" },
  { label: "30 Days", value: "30" },
  { label: "3 Months", value: "90" },
  { label: "1 Year", value: "365" },
  { label: "Custom", value: "custom" },
];
const roleOptions = ["", "Athlete", "Coach", "Physiotherapist", "Sports Scientist", "Administrator"];

function AdminPlatformAnalytics() {
  const [filters, setFilters] = useState({
    range: "30",
    sport: "",
    user_role: "",
    date_from: "",
    date_to: "",
  });
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadAnalytics() {
      setLoading(true);
      setError("");
      try {
        const requestFilters = {
          sport: filters.sport,
          user_role: filters.user_role,
          range_days: filters.range === "custom" ? 30 : filters.range,
          date_from: filters.range === "custom" ? filters.date_from : "",
          date_to: filters.range === "custom" ? filters.date_to : "",
        };
        const data = await getAdminPlatformAnalytics(requestFilters);
        if (!cancelled) setAnalytics(data);
      } catch (error) {
        if (!cancelled) setError(error.message || "Failed to load platform analytics.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAnalytics();
    return () => {
      cancelled = true;
    };
  }, [filters]);

  function updateFilter(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  const summary = analytics?.summary || {};
  const cards = useMemo(
    () => [
      { label: "Total Users", value: summary.total_users, icon: UsersRound },
      { label: "New Users", value: summary.new_users, icon: UsersRound },
      { label: "Videos Uploaded", value: summary.videos_uploaded, icon: Upload },
      { label: "Analyses Completed", value: summary.analyses_completed, icon: BarChart3 },
      { label: "Active Professionals", value: summary.active_professionals, icon: ShieldCheck },
      { label: "Active Athlete Connections", value: summary.active_athlete_connections, icon: Activity },
    ],
    [summary]
  );

  const professionalActivity = analytics?.professional_activity || {};
  const professionalRows = [
    { label: "Applications", count: professionalActivity.applications || 0 },
    { label: "Approved", count: professionalActivity.approved || 0 },
    { label: "Rejected", count: professionalActivity.rejected || 0 },
    { label: "Pending", count: professionalActivity.pending || 0 },
    { label: "Active Connections", count: professionalActivity.active_connections || 0 },
  ];

  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN</p>
            <h1>Platform Analytics</h1>
            <p>Monitor platform usage, analysis activity, users, sports, and risk distribution.</p>
          </div>
        </section>

        <section className="admin-filter-card analytics-filter-card">
          <label>
            <span>Date Range</span>
            <select name="range" value={filters.range} onChange={updateFilter}>
              {rangeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          {filters.range === "custom" && (
            <>
              <label><span>From</span><input type="date" name="date_from" value={filters.date_from} onChange={updateFilter} /></label>
              <label><span>To</span><input type="date" name="date_to" value={filters.date_to} onChange={updateFilter} /></label>
            </>
          )}
          <label>
            <span>Sport</span>
            <select name="sport" value={filters.sport} onChange={updateFilter}>
              <option value="">All sports</option>
              {(analytics?.sports || []).map((sport) => <option key={sport} value={sport}>{sport}</option>)}
            </select>
          </label>
          <label>
            <span>User Role</span>
            <select name="user_role" value={filters.user_role} onChange={updateFilter}>
              {roleOptions.map((role) => <option key={role || "ALL"} value={role}>{role || "All roles"}</option>)}
            </select>
          </label>
        </section>

        {error && <section className="admin-error-card">{error}</section>}
        {loading && <section className="admin-empty-card">Loading platform analytics...</section>}

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
                <div className="admin-panel-heading"><div><h2>User Growth</h2><p>New users over the selected range.</p></div></div>
                <AdminTimeSeriesChart rows={analytics?.user_growth || []} valueKey="new_users" emptyText="No new user records are available for these filters." ariaLabel="User growth time series showing new users by date" />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Analysis Activity</h2><p>Completed analyses over time.</p></div></div>
                <AdminTimeSeriesChart rows={analytics?.analysis_activity || []} valueKey="completed_analyses" emptyText="No completed analyses are available for these filters." ariaLabel="Analysis activity time series showing completed analyses by date" />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Users by Role</h2><p>Current users by role.</p></div></div>
                <AdminBarDistribution rows={analytics?.users_by_role || []} emptyText="No user-role data is available." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Analyses by Sport</h2><p>Completed analyses grouped by sport.</p></div></div>
                <AdminBarDistribution rows={analytics?.analyses_by_sport || []} labelKey="sport" emptyText="No sport analysis data is available for these filters." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Risk Distribution</h2><p>Existing risk bands from completed analyses.</p></div></div>
                <AdminBarDistribution rows={analytics?.risk_distribution || []} emptyText="No risk distribution data is available for these filters." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Professional Activity</h2><p>Applications, decisions, and active professional connections.</p></div></div>
                <AdminBarDistribution rows={professionalRows} emptyText="No professional activity is available for these filters." />
              </article>
            </section>
          </>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminPlatformAnalytics;
