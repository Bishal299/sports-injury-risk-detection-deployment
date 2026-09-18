import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import {
  LayoutDashboard,
  UserRound,
  Video,
  History,
  ClipboardList,
  BriefcaseBusiness,
  ShieldCheck,
  Activity,
  BarChart3,
  FileText,
  UsersRound,
  Sun,
  Moon,
  LogOut,
  Settings,
  Menu,
  X,
} from "lucide-react";

import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";
import { useAthleteProfile } from "../context/AthleteProfileContext";
import { getAnalysisHistory, getCurrentUser } from "../services/api";
import { clearAuthSession } from "../utils/authSession";
import { confirmLogout } from "../utils/logoutConfirmation";
import NotificationBell from "../components/notifications/NotificationBell";
import BrandLogo from "../components/BrandLogo";


function DashboardLayout({ children, onLogout }) {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { hasAthleteProfile } = useAthleteProfile();
  const [hasAnalysisHistory, setHasAnalysisHistory] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);


  useEffect(() => {
    let cancelled = false;

    const loadCurrentUser = async () => {
      try {
        const user = await getCurrentUser();

        if (!cancelled) {
          setCurrentUser(user);
        }
      } catch {
        if (!cancelled) {
          setCurrentUser(null);
        }
      }
    };

    loadCurrentUser();
    window.addEventListener("user-role-updated", loadCurrentUser);

    return () => {
      cancelled = true;
      window.removeEventListener("user-role-updated", loadCurrentUser);
    };
  }, []);


  useEffect(() => {
    if (!hasAthleteProfile) {
      setHasAnalysisHistory(false);
      return;
    }

    let cancelled = false;

    const refreshAnalysisHistoryVisibility = async () => {
      try {
        const records = await getAnalysisHistory();
        const hasRecords = Array.isArray(records) && records.length > 0;

        if (!cancelled) {
          setHasAnalysisHistory(hasRecords);
        }
      } catch (error) {
        if (!cancelled) {
          setHasAnalysisHistory(false);
        }
      }
    };

    refreshAnalysisHistoryVisibility();
    window.addEventListener(
      "analysis-history-updated",
      refreshAnalysisHistoryVisibility
    );

    return () => {
      cancelled = true;
      window.removeEventListener(
        "analysis-history-updated",
        refreshAnalysisHistoryVisibility
      );
    };
  }, [hasAthleteProfile]);


  const profileNavigation = [
    {
      name: "Athlete Profile",
      path: "/athlete-profile",
      icon: UserRound,
    },
        {
          name: "My Videos",
          path: "/my-videos",
          icon: Video,
        },
        ...(hasAnalysisHistory
          ? [{
              name: "Analysis History",
              path: "/analysis-history",
              icon: History,
            }]
          : []),
        {
          name: "My Work",
          path: "/my-work",
          icon: ClipboardList,
        },
  ];

  const navigation = hasAthleteProfile
    ? [
        {
          name: "Dashboard",
          path: "/dashboard",
          icon: LayoutDashboard,
        },
        ...profileNavigation,
      ]
    : profileNavigation.filter(
        (item) => item.path === "/athlete-profile"
      );

  const professionalNavigation = [
    {
      name: currentUser?.role === "Coach"
        ? "Coach Access"
        : "Request Professional Role",
      path: "/request-professional-role",
      icon: BriefcaseBusiness,
    },
    ...(currentUser?.role === "Administrator"
      ? [
          {
            name: "Professional Requests",
            path: "/admin/professional-requests",
            icon: ShieldCheck,
          },
        ]
      : []),
  ];

  const fullNavigation = currentUser?.role === "Administrator"
    ? [
        {
          name: "Dashboard",
          path: "/admin/dashboard",
          icon: LayoutDashboard,
        },
        {
          name: "Professional Requests",
          path: "/admin/professional-requests",
          icon: ShieldCheck,
        },
        {
          name: "User Management",
          path: "/admin/users",
          icon: UsersRound,
        },
        {
          name: "Platform Analytics",
          path: "/admin/analytics",
          icon: BarChart3,
        },
        {
          name: "System Monitoring",
          path: "/admin/system-monitoring",
          icon: Activity,
        },
        {
          name: "Report Management",
          path: "/admin/reports",
          icon: FileText,
        },
        {
          name: "Profile",
          path: "/admin/profile",
          icon: UserRound,
        },
        {
          name: "Settings",
          path: "/admin/settings",
          icon: Settings,
        },
      ]
    : currentUser?.role === "Coach"
      ? [
          {
            name: "Coach Access",
            path: "/coach/dashboard",
            icon: BriefcaseBusiness,
          },
        ]
      : [
          ...navigation,
          ...professionalNavigation,
        ];


  const closeSidebar = () => {
    setSidebarOpen(false);
  };


  const handleNavigation = () => {
    closeSidebar();
  };


  const handleSettings = () => {
    closeSidebar();
    navigate("/settings");
  };


  const handleLogout = async () => {
    if (!confirmLogout()) {
      return;
    }

    closeSidebar();

    if (onLogout) {
      await onLogout();
      return;
    }

    await logout();

    navigate("/login", { replace: true });
  };



  return (

    <div className="dashboard-shell">


      {/* Mobile Header */}

      <header className="mobile-header">

        <button
          className="mobile-menu-button"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open navigation"
        >
          <Menu size={24} />
        </button>


        <div className="mobile-logo">
          <BrandLogo />
        </div>

      </header>


      {/* Mobile Overlay */}

      {sidebarOpen && (
        <div
            className="sidebar-overlay"
            onClick={closeSidebar}
            aria-hidden="true"
        />
        )}


      {/* Sidebar */}

      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-mobile-open" : ""
        }`}
      >


        {/* Sidebar Logo */}

        <div className="sidebar-logo">
          <BrandLogo />


          {/* Close button - mobile only */}

          <button
            className="sidebar-close-button"
            onClick={closeSidebar}
            aria-label="Close navigation"
          >
            <X size={22} />
          </button>

        </div>


        {/* Navigation */}

        <nav className="sidebar-nav">

          {fullNavigation.map((item) => {

            const Icon = item.icon;

            return (

              <NavLink
                key={item.path}
                to={item.path}
                onClick={handleNavigation}
                className={({ isActive }) =>
                  `nav-item ${
                    isActive
                      ? "nav-item-active"
                      : ""
                  }`
                }
              >

                <Icon size={20} />

                <span>
                  {item.name}
                </span>

              </NavLink>

            );

          })}

        </nav>


        {/* Bottom Actions */}

        <div className="sidebar-bottom">


          {/* Theme */}

          <button
            className="sidebar-action"
            onClick={() => {
                toggleTheme();
                closeSidebar();
            }}
            >

            {theme === "light"
              ? <Moon size={19} />
              : <Sun size={19} />
            }

            <span>
              {theme === "light"
                ? "Dark Mode"
                : "Light Mode"
              }
            </span>

          </button>


          {/* Settings */}

          {currentUser?.role === "Athlete" && hasAthleteProfile && (
            <button
              className="sidebar-action"
              onClick={handleSettings}
            >

              <Settings size={19} />

              <span>
                Settings
              </span>

            </button>
          )}


          {/* Logout */}

          <button
            className="sidebar-action logout-action"
            onClick={handleLogout}
          >

            <LogOut size={19} />

            <span>
              Logout
            </span>

          </button>


        </div>

      </aside>


      {/* Main Content */}

      <main className="dashboard-main">
        <div className="notification-layout-slot">
          <NotificationBell />
        </div>

        {children}

      </main>


    </div>

  );
}


export default DashboardLayout;
