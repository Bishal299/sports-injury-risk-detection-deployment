import React from "react";
import DashboardLayout from "../layouts/DashboardLayout";
import { useTheme } from "../context/ThemeContext";
import "../styles/settings.css";

function Settings() {
  const { theme, toggleTheme } = useTheme();

  const darkMode = theme === "dark";

  return (
    <DashboardLayout>

      <div className="page-header">
        <p className="page-eyebrow">
          SETTINGS
        </p>

        <h1>
          Settings
        </h1>

        <p>
          Manage your account and application preferences.
        </p>
      </div>


      <div className="settings-container">

        {/* Appearance */}
        <section className="settings-card">

          <div className="settings-card-header">
            <div>
              <h2>
                Appearance
              </h2>

              <p>
                Customize how the application looks.
              </p>
            </div>
          </div>


          <div className="settings-row">

            <div>
              <h3>
                Dark Mode
              </h3>

              <p>
                Use a darker interface for low-light environments.
              </p>
            </div>


            <label className="switch">

              <input
                type="checkbox"
                checked={darkMode}
                onChange={toggleTheme}
              />

              <span className="slider"></span>

            </label>

          </div>

        </section>


        {/* Account */}
        <section className="settings-card">

          <div className="settings-card-header">

            <div>
              <h2>
                Account
              </h2>

              <p>
                Manage your account preferences.
              </p>
            </div>

          </div>


          <div className="settings-row">

            <div>
              <h3>
                Password
              </h3>

              <p>
                Password management will be available here.
              </p>
            </div>

            <button
              className="secondary-button"
              disabled
            >
              Change Password
            </button>

          </div>


          <div className="settings-row">

            <div>
              <h3>
                Google Login
              </h3>

              <p>
                Google authentication will be added later.
              </p>
            </div>

            <button
              className="secondary-button"
              disabled
            >
              Connect
            </button>

          </div>

        </section>


        {/* Application */}
        <section className="settings-card">

          <div className="settings-card-header">

            <div>
              <h2>
                Application
              </h2>

              <p>
                Information about your sports injury detection system.
              </p>
            </div>

          </div>


          <div className="settings-row">

            <div>
              <h3>
                Version
              </h3>

              <p>
                Athlete platform
              </p>
            </div>

            <span className="settings-badge">
              MVP
            </span>

          </div>

        </section>

      </div>

    </DashboardLayout>
  );
}

export default Settings;