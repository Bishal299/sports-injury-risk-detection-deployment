import React from "react";

function BrandLogo({ className = "" }) {
  return (
    <div className={`brand-logo ${className}`}>
      <img
        className="brand-runner-icon"
        src="/sportrisk_runner_transparent.png"
        alt="SportRisk"
      />
      <div className="brand-text">
        <h2>
          Sport<span className="brand-risk-text">Risk</span>
        </h2>
      </div>
    </div>
  );
}

export default BrandLogo;
