import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser } from "../services/api";


function Dashboard() {

  const [user, setUser] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");

    navigate("/login");
  };
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
    <div>

      <h1>
        Sports Injury Risk Detection
      </h1>

      <h2>
        Dashboard
      </h2>


      {user && (
        <div>

          <h3>
            Welcome, {user.name}
          </h3>

          <p>
            Email: {user.email}
          </p>

          <p>
            Role: {user.role}
          </p>

          <button
            onClick={() => navigate("/athlete-profile")}
            >
            Athlete Profile
          </button>

        </div>
      )}

      <button onClick={handleLogout}>
         Logout
      </button>

    </div>
  );
}


export default Dashboard;