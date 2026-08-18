
import React from "react";
import ReactDOM from "react-dom/client";
import { GoogleOAuthProvider } from "@react-oauth/google";
import "./styles/global.css";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { AthleteProfileProvider } from "./context/AthleteProfileContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <AthleteProfileProvider>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </AthleteProfileProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>
);

console.log(
  "Google Client ID:",
  import.meta.env.VITE_GOOGLE_CLIENT_ID
);
