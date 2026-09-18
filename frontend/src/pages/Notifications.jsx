import React, { useCallback, useEffect, useState } from "react";
import { BellRing, CheckCheck, ClipboardList, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import DashboardLayout from "../layouts/DashboardLayout";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  markNotificationUnread,
} from "../services/api";
import "../styles/notifications.css";


const pageSize = 20;

function formatDate(value) {
  if (!value) return "Recently";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Recently";
  return parsed.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function iconForType(type) {
  if (String(type).includes("CONNECTION")) return UserPlus;
  if (String(type).includes("ROLE") || String(type).includes("TASK") || String(type).includes("REHAB")) return ClipboardList;
  return BellRing;
}

function Notifications() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [data, setData] = useState({ notifications: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getNotifications({
        unread_only: filter === "unread",
        limit: pageSize,
        offset: page * pageSize,
      });
      setData({
        notifications: Array.isArray(response.notifications) ? response.notifications : [],
        total: Number(response.total) || 0,
      });
    } catch (error) {
      setError(error.message || "Failed to load notifications.");
    } finally {
      setLoading(false);
    }
  }, [filter, page]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  async function toggleRead(notification) {
    if (notification.is_read) await markNotificationUnread(notification.notification_id);
    else await markNotificationRead(notification.notification_id);
    await loadNotifications();
  }

  async function openNotification(notification) {
    if (!notification.is_read) await markNotificationRead(notification.notification_id);
    if (notification.action_url) navigate(notification.action_url);
    else await loadNotifications();
  }

  async function markAllRead() {
    await markAllNotificationsRead();
    await loadNotifications();
  }

  const totalPages = Math.max(Math.ceil(data.total / pageSize), 1);

  return (
    <DashboardLayout>
      <main className="notifications-page">
        <section className="notifications-header">
          <div>
            <p className="page-eyebrow">NOTIFICATIONS</p>
            <h1>Notifications</h1>
            <p>Stay updated with requests, recommendations, activity, and important events.</p>
          </div>
          <button className="notifications-secondary-button" type="button" onClick={markAllRead}>
            <CheckCheck size={17} />
            Mark all as read
          </button>
        </section>

        <section className="notifications-toolbar">
          <button className={filter === "all" ? "active" : ""} type="button" onClick={() => { setFilter("all"); setPage(0); }}>All</button>
          <button className={filter === "unread" ? "active" : ""} type="button" onClick={() => { setFilter("unread"); setPage(0); }}>Unread</button>
        </section>

        {loading && <section className="notifications-empty">Loading notifications...</section>}
        {error && <section className="notifications-error">{error}</section>}

        {!loading && !error && data.notifications.length === 0 && (
          <section className="notifications-empty">No notifications yet.</section>
        )}

        {!loading && !error && data.notifications.length > 0 && (
          <section className="notifications-list">
            {data.notifications.map((notification) => {
              const Icon = iconForType(notification.type);
              return (
                <article className={`notifications-row ${notification.is_read ? "" : "unread"}`} key={notification.notification_id}>
                  <button className="notifications-row-main" type="button" onClick={() => openNotification(notification)}>
                    <span className="notifications-icon"><Icon size={18} /></span>
                    <span>
                      <strong>{notification.title}</strong>
                      <small>{notification.message}</small>
                      <time>{formatDate(notification.created_at)}</time>
                    </span>
                  </button>
                  <button className="notifications-secondary-button compact" type="button" onClick={() => toggleRead(notification)}>
                    {notification.is_read ? "Mark unread" : "Mark read"}
                  </button>
                </article>
              );
            })}
          </section>
        )}

        <section className="notifications-pagination">
          <button type="button" disabled={page === 0} onClick={() => setPage((current) => Math.max(current - 1, 0))}>Previous</button>
          <span>Page {page + 1} of {totalPages}</span>
          <button type="button" disabled={page + 1 >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
        </section>
      </main>
    </DashboardLayout>
  );
}


export default Notifications;
