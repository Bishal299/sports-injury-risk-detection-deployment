import React from "react";
import ReactDOM from "react-dom/client";
import { GoogleOAuthProvider } from "@react-oauth/google";
import "./styles/global.css";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { AthleteProfileProvider } from "./context/AthleteProfileContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}>
      <AuthProvider>
        <AthleteProfileProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </AthleteProfileProvider>
      </AuthProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>
);
