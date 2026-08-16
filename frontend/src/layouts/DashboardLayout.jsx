import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import {
  LayoutDashboard,
  UserRound,
  Video,
  Upload,
  Sun,
  Moon,
  LogOut,
  Settings,
  Menu,
  X,
} from "lucide-react";

import { useTheme } from "../context/ThemeContext";


function DashboardLayout({ children, onLogout }) {

  const { theme, toggleTheme } = useTheme();

  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);


  const navigation = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
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
    {
      name: "Upload Video",
      path: "/video-upload",
      icon: Upload,
    },
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


  const handleLogout = () => {
    closeSidebar();

    if (onLogout) {
      onLogout();
    }
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

          <div className="logo-icon">
            S
          </div>

          <div>
            <h2>SportRisk</h2>
            <span>Injury Detection</span>
          </div>

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

          <div className="logo-icon">
            S
          </div>

          <div>
            <h2>SportRisk</h2>
            <span>Injury Detection</span>
          </div>


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

          {navigation.map((item) => {

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

          <button
            className="sidebar-action"
            onClick={handleSettings}
          >

            <Settings size={19} />

            <span>
              Settings
            </span>

          </button>


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

        {children}

      </main>


    </div>

  );
}


export default DashboardLayout;