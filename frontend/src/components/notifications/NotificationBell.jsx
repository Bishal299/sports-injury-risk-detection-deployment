import React, { useCallback, useEffect, useRef, useState } from "react";
import { Bell, BellRing, CheckCheck, ClipboardList, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
  getNotificationUnreadCount,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../../services/api";
import "../../styles/notifications.css";


function relativeTime(value) {
  if (!value) return "Recently";
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return "Recently";
  const seconds = Math.max(Math.floor((Date.now() - timestamp) / 1000), 0);
  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function iconForType(type) {
  if (String(type).includes("CONNECTION")) return UserPlus;
  if (String(type).includes("ROLE") || String(type).includes("TASK") || String(type).includes("REHAB")) return ClipboardList;
  return BellRing;
}

function NotificationBell() {
  const navigate = useNavigate();
  const wrapperRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [listData, countData] = await Promise.all([
        getNotifications({ limit: 5, offset: 0 }),
        getNotificationUnreadCount(),
      ]);
      setNotifications(Array.isArray(listData.notifications) ? listData.notifications : []);
      setUnreadCount(Number(countData.unread_count) || 0);
    } catch (error) {
      setError(error.message || "Failed to load notifications.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 60000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    function handleClick(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function openPopover() {
    setOpen((current) => !current);
    setError("");
    setLoading(true);
    try {
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  async function handleNotification(notification) {
    if (!notification.is_read) {
      await markNotificationRead(notification.notification_id);
      await refresh();
    }
    setOpen(false);
    if (notification.action_url) navigate(notification.action_url);
  }

  async function handleMarkAll() {
    await markAllNotificationsRead();
    await refresh();
  }

  const badge = unreadCount > 9 ? "9+" : unreadCount;

  return (
    <div className="notification-shell" ref={wrapperRef}>
      <button className="notification-bell-button" type="button" aria-label="Open notifications" onClick={openPopover}>
        <Bell size={20} />
        {unreadCount > 0 && <span className="notification-badge">{badge}</span>}
      </button>

      {open && (
        <section className="notification-popover">
          <div className="notification-popover-header">
            <div>
              <h2>Notifications</h2>
              <p>{unreadCount ? `${unreadCount} unread` : "All caught up"}</p>
            </div>
            <button type="button" onClick={handleMarkAll} disabled={!unreadCount}>
              <CheckCheck size={16} />
              Mark all as read
            </button>
          </div>

          {loading && <div className="notification-empty">Loading notifications...</div>}
          {error && <div className="notification-error">{error}</div>}
          {!loading && !error && notifications.length === 0 && <div className="notification-empty">No notifications yet.</div>}

          {!loading && !error && notifications.length > 0 && (
            <div className="notification-list">
              {notifications.map((notification) => {
                const Icon = iconForType(notification.type);
                return (
                  <button
                    className={`notification-item ${notification.is_read ? "" : "unread"}`}
                    key={notification.notification_id}
                    type="button"
                    onClick={() => handleNotification(notification)}
                  >
                    <span className="notification-icon"><Icon size={16} /></span>
                    <span>
                      <strong>{notification.title}</strong>
                      <small>{notification.message}</small>
                      <time>{relativeTime(notification.created_at)}</time>
                    </span>
                    {!notification.is_read && <i aria-label="Unread" />}
                  </button>
                );
              })}
            </div>
          )}

          <button className="notification-view-all" type="button" onClick={() => { setOpen(false); navigate("/notifications"); }}>
            View all notifications →
          </button>
        </section>
      )}
    </div>
  );
}


export default NotificationBell;
