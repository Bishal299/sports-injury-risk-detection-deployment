import React from "react";
import ReactDOM from "react-dom/client";
import { GoogleOAuthProvider } from "@react-oauth/google";
import "./styles/global.css";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { AthleteProfileProvider } from "./context/AthleteProfileContext";
import { GOOGLE_CLIENT_ID, isGoogleAuthConfigured } from "./config/googleOAuth";

const appTree = (
  <React.StrictMode>
    <AuthProvider>
      <AthleteProfileProvider>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </AthleteProfileProvider>
    </AuthProvider>
  </React.StrictMode>
);

ReactDOM.createRoot(document.getElementById("root")).render(
  isGoogleAuthConfigured ? (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {appTree}
    </GoogleOAuthProvider>
  ) : (
    appTree
  )
);
