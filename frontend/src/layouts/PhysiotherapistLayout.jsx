import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BarChart3,
  ClipboardList,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sun,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";

import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";
import { logoutUser } from "../services/api";
import { clearAuthSession } from "../utils/authSession";
import { confirmLogout } from "../utils/logoutConfirmation";
import NotificationBell from "../components/notifications/NotificationBell";
import BrandLogo from "../components/BrandLogo";


const mainNavigation = [
  { name: "Dashboard", path: "/physiotherapist/dashboard", icon: LayoutDashboard },
  { name: "My Athletes", path: "/physiotherapist/athletes", icon: UsersRound },
  { name: "Discover Athletes", path: "/physiotherapist/discover-athletes", icon: Search },
  { name: "Athlete Requests", path: "/physiotherapist/requests", icon: ClipboardList },
  { name: "Rehabilitation", path: "/physiotherapist/rehabilitation", icon: HeartPulse },
  { name: "Movement Analytics", path: "/physiotherapist/movement-analytics", icon: BarChart3 },
  { name: "Recovery Reports", path: "/physiotherapist/recovery-reports", icon: FileText },
];

const profileNavigation = [
  { name: "Profile", path: "/physiotherapist/profile", icon: UserRound },
  { name: "Settings", path: "/physiotherapist/settings", icon: Settings },
];


function PhysiotherapistLayout({ children }) {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = () => setSidebarOpen(false);

  async function handleLogout() {
    if (!confirmLogout()) {
      return;
    }

    closeSidebar();
    await logout();
    navigate("/login", { replace: true });
  }


  return (
    <div className="dashboard-shell coach-shell">
      <header className="mobile-header">
        <button className="mobile-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open Physiotherapist navigation" type="button">
          <Menu size={24} />
        </button>
        <div className="mobile-logo">
          <BrandLogo />
        </div>
      </header>

      {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar} aria-hidden="true" />}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-mobile-open" : ""}`}>
        <div className="sidebar-logo">
          <BrandLogo />
          <button className="sidebar-close-button" onClick={closeSidebar} aria-label="Close navigation" type="button">
            <X size={22} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {mainNavigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={closeSidebar}
                className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          {profileNavigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={closeSidebar}
                className={({ isActive }) => `sidebar-action ${isActive ? "nav-item-active" : ""}`}
              >
                <Icon size={19} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
          <button className="sidebar-action" onClick={() => { toggleTheme(); closeSidebar(); }} type="button">
            {theme === "light" ? <Moon size={19} /> : <Sun size={19} />}
            <span>{theme === "light" ? "Dark Mode" : "Light Mode"}</span>
          </button>
          <button className="sidebar-action logout-action" onClick={handleLogout} type="button">
            <LogOut size={19} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <div className="notification-layout-slot">
          <NotificationBell />
        </div>
        {children || <Outlet />}
      </main>
    </div>
  );
}


export default PhysiotherapistLayout;
