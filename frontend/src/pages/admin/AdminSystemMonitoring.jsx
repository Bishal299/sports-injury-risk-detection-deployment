import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Database, RefreshCw, Server, ShieldCheck } from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  AdminBarDistribution,
  AdminTimeSeriesChart,
  formatNumber,
} from "../../components/admin/AdminVisualizations";
import { getAdminSystemMonitoring } from "../../services/api";
import "../../styles/admin.css";

function formatDateTime(value) {
  if (!value) return "Not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Not available";
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function statusClass(status) {
  return String(status || "not monitored").toLowerCase().replace(/\s+/g, "-");
}

function serviceIcon(service) {
  if (service.includes("Database")) return Database;
  if (service.includes("Authentication")) return ShieldCheck;
  if (service.includes("Analysis")) return Activity;
  if (service.includes("Processing")) return Activity;
  return Server;
}

function AdminSystemMonitoring() {
  const [filters, setFilters] = useState({ service: "", event_status: "", event_date: "" });
  const [monitoring, setMonitoring] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadMonitoring = useCallback(async ({ background = false } = {}) => {
    if (background) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      const data = await getAdminSystemMonitoring(filters);
      setMonitoring(data);
    } catch (error) {
      setError(error.message || "Failed to load system monitoring.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    loadMonitoring();
  }, [loadMonitoring]);

  function updateFilter(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  const overview = monitoring?.overview || {};
  const processing = monitoring?.processing_monitor || {};
  const cards = useMemo(
    () => [
      { label: "API Health", value: overview.api_status || "Not checked", icon: Server },
      { label: "Database", value: overview.database_status || "Not checked", icon: Database },
      { label: "Videos Processing", value: overview.videos_currently_processing, icon: Activity },
      { label: "Completed Analyses", value: overview.completed_analyses, icon: CheckCircle2 },
      { label: "Failed Analyses", value: overview.failed_analyses, icon: AlertTriangle },
      { label: "Pending / Queued", value: overview.pending_queued_jobs, icon: Activity },
    ],
    [overview]
  );

  const processingRows = [
    { label: "Queued", value: processing.queued || 0 },
    { label: "Processing", value: processing.processing || 0 },
    { label: "Completed", value: processing.completed || 0 },
    { label: "Failed", value: processing.failed || 0 },
  ];

  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN</p>
            <h1>System Monitoring</h1>
            <p>Monitor platform health, services, processing status, and system events.</p>
          </div>
          <button className="admin-primary-button" type="button" disabled={refreshing} onClick={() => loadMonitoring({ background: true })}>
            <RefreshCw size={18} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </section>

        {monitoring?.last_checked_at && (
          <section className="admin-empty-card">Last successful health check: {formatDateTime(monitoring.last_checked_at)}</section>
        )}

        {error && <section className="admin-error-card">{error}</section>}
        {loading && <section className="admin-empty-card">Loading system monitoring...</section>}

        {!loading && !error && (
          <>
            <section className="admin-health-grid">
              {(monitoring?.service_health || []).map((item) => {
                const Icon = serviceIcon(item.service);
                return (
                  <article className="admin-health-card" key={item.service}>
                    <div className="admin-icon-box"><Icon size={21} /></div>
                    <div>
                      <h2>{item.service}</h2>
                      <span className={`admin-status-pill ${statusClass(item.status)}`}>{item.status}</span>
                      <p>{item.detail}</p>
                    </div>
                  </article>
                );
              })}
            </section>

            <section className="admin-summary-grid">
              {cards.map((card) => {
                const Icon = card.icon;
                const isNumber = typeof card.value === "number";
                return (
                  <article className="admin-summary-card" key={card.label}>
                    <div className="admin-icon-box"><Icon size={21} /></div>
                    <div><span>{card.label}</span><strong>{isNumber ? formatNumber(card.value) : card.value}</strong></div>
                  </article>
                );
              })}
            </section>

            <section className="admin-chart-grid">
              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Analysis Processing Monitor</h2><p>Stored video and analysis processing records.</p></div></div>
                <AdminBarDistribution rows={processingRows} valueKey="value" emptyText="No processing records are available." />
              </article>

              <article className="admin-panel-card">
                <div className="admin-panel-heading"><div><h2>Recent Processing Activity</h2><p>Analysis records by date where timestamps exist.</p></div></div>
                <AdminTimeSeriesChart rows={processing.recent_activity || []} valueKey="records" compact emptyText="No processing trend data is available." ariaLabel="Recent processing activity trend by date" />
              </article>
            </section>

            <section className="admin-panel-card">
              <div className="admin-panel-heading">
                <div><h2>System Events / Errors</h2><p>Stored processing failures from existing records.</p></div>
              </div>

              <section className="admin-filter-card analytics-filter-card">
                <label>
                  <span>Service</span>
                  <select name="service" value={filters.service} onChange={updateFilter}>
                    <option value="">All services</option>
                    {(monitoring?.event_filters?.services || []).map((service) => <option key={service} value={service}>{service}</option>)}
                  </select>
                </label>
                <label>
                  <span>Status</span>
                  <select name="event_status" value={filters.event_status} onChange={updateFilter}>
                    <option value="">All statuses</option>
                    {(monitoring?.event_filters?.statuses || []).map((status) => <option key={status} value={status}>{status}</option>)}
                  </select>
                </label>
                <label>
                  <span>Date</span>
                  <input type="date" name="event_date" value={filters.event_date} onChange={updateFilter} />
                </label>
              </section>

              {monitoring?.events?.length ? (
                <div className="admin-monitor-table">
                  <div className="admin-monitor-table-head"><span>Time</span><span>Service</span><span>Event</span><span>Status</span></div>
                  {monitoring.events.map((event, index) => (
                    <article className="admin-monitor-table-row" key={`${event.time}-${event.service}-${index}`}>
                      <span>{formatDateTime(event.time)}</span>
                      <span>{event.service}</span>
                      <span>{event.event}</span>
                      <span><span className={`admin-status-pill ${statusClass(event.status)}`}>{event.status}</span></span>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="admin-empty-state">No persistent system-event source or matching stored processing errors are available.</div>
              )}
            </section>
          </>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminSystemMonitoring;
