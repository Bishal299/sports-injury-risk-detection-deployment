import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser } from "../services/api";
import DashboardLayout from "../layouts/DashboardLayout";
import "../styles/dashboard.css";
// @import "./variables.css";


function Dashboard() {

  const [user, setUser] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const navigate = useNavigate();
  useEffect(() => {

    const fetchUser = async () => {

      try {

        const data = await getCurrentUser();

        console.log("Current user:", data);

        setUser(data);

      } catch (error) {

        console.error(error);

        setError(error.message);

      } finally {

        setLoading(false);

      }

    };


    fetchUser();

  }, []);


  if (loading) {

    return (
      <div>
        <h1>Sports Injury Risk Detection</h1>

        <p>
          Loading dashboard...
        </p>
      </div>
    );

  }


  if (error) {

    return (
      <div>

        <h1>Sports Injury Risk Detection</h1>

        <p style={{ color: "red" }}>
          {error}
        </p>

      </div>
    );

  }


  return (
  <DashboardLayout>

    <div className="page-header">

      <p className="page-eyebrow">
        ATHLETE DASHBOARD
      </p>

      <h1>
        Welcome back, {user?.name}
      </h1>

      <p>
        Monitor your sports performance and injury risk.
      </p>

    </div>


    <div className="dashboard-grid">

      <div className="stat-card">
        <span>Role</span>
        <strong>
          {user?.role}
        </strong>
      </div>


      <div className="stat-card">
        <span>Email</span>
        <strong>
          {user?.email}
        </strong>
      </div>


      <div className="stat-card">
        <span>Status</span>
        <strong>
          Active
        </strong>
      </div>

    </div>


    <div className="dashboard-card">

      <h2>
        Quick Actions
      </h2>

      <p>
        Manage your athlete profile and
        sports videos.
      </p>


      <div className="quick-actions">

        <button
          className="primary-button"
          onClick={() =>
            navigate("/athlete-profile")
          }
        >
          Athlete Profile
        </button>


        <button
          className="primary-button"
          onClick={() =>
            navigate("/video-upload")
          }
        >
          Upload Video
        </button>


        <button
          className="primary-button"
          onClick={() =>
            navigate("/my-videos")
          }
        >
          My Videos
        </button>

      </div>

    </div>

  </DashboardLayout>
);
}


export default Dashboard;
