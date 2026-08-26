import React from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Database,
  FileVideo,
  Gauge,
  History,
  LineChart,
  Play,
  ScanLine,
  ShieldCheck,
  UserRound,
  Video,
  Zap,
} from "lucide-react";

import "../styles/landing.css";


const workSteps = [
  {
    icon: UserRound,
    title: "Create Athlete Profile",
    text: "Capture athlete context such as sport, body metrics, and injury history.",
  },
  {
    icon: FileVideo,
    title: "Upload Video",
    text: "Add training or movement footage for structured analysis.",
  },
  {
    icon: ScanLine,
    title: "AI Movement Analysis",
    text: "Use pose estimation to read movement patterns from video frames.",
  },
  {
    icon: Gauge,
    title: "Risk Assessment",
    text: "Review indicators that can support safer training decisions.",
  },
];


const features = [
  {
    icon: Brain,
    title: "AI Movement Analysis",
    text: "Computer vision workflows extract pose landmarks from athlete motion.",
  },
  {
    icon: Video,
    title: "Video Assessment",
    text: "Upload sports videos and keep analysis tied to each athlete record.",
  },
  {
    icon: UserRound,
    title: "Athlete Profiles",
    text: "Maintain profile details that add useful context to movement review.",
  },
  {
    icon: ShieldCheck,
    title: "Risk Assessment",
    text: "Surface risk signals without replacing coach or medical judgment.",
  },
  {
    icon: LineChart,
    title: "Performance Insights",
    text: "Translate movement data into readable training and review signals.",
  },
  {
    icon: History,
    title: "Analysis History",
    text: "Keep uploaded videos and outcomes organized for later comparison.",
  },
];


const techFlow = [
  "Computer Vision",
  "Pose Estimation",
  "Feature Extraction",
  "ML Model",
  "Risk Assessment",
];


function Landing() {

  return (
    <div className="landing-page">

      <header className="landing-navbar">
        <Link
          to="/"
          className="landing-brand"
        >
          <span className="landing-logo-icon">
            S
          </span>

          <span>
            <strong>SportRisk</strong>
            <small>Injury Detection</small>
          </span>
        </Link>

        <nav className="landing-nav-links">
          <a href="#home">Home</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </nav>

        <div className="landing-nav-actions">
          <Link
            to="/login"
            className="landing-button landing-button-ghost"
          >
            Login
          </Link>

          <Link
            to="/register"
            className="landing-button landing-button-primary"
          >
            Get Started
            <ArrowRight size={17} />
          </Link>
        </div>
      </header>


      <main>
        <section
          id="home"
          className="landing-hero"
        >
          <div className="landing-hero-content">
            <p className="landing-eyebrow">
              AI-POWERED SPORTS ANALYTICS
            </p>

            <h1>
              Predict Injury Risk. Protect Every Athlete.
            </h1>

            <p className="landing-hero-copy">
              SportRisk helps athletes and performance teams review movement
              videos, organize athlete data, and identify signals that may
              support safer training decisions.
            </p>

            {/* <div className="landing-hero-actions">
              <Link
                to="/register"
                className="landing-button landing-button-primary landing-button-large"
              >
                Get Started
                <ArrowRight size={18} />
              </Link>

              <Link
                to="/login"
                className="landing-button landing-button-glass landing-button-large"
              >
                <Play size={17} />
                Login
              </Link>
            </div> */}

            <div className="landing-proof-row">
              <span>
                <CheckCircle2 size={17} />
                Athlete profiles
              </span>

              <span>
                <CheckCircle2 size={17} />
                Video uploads
              </span>

              <span>
                <CheckCircle2 size={17} />
                Pose analysis workflow
              </span>
            </div>
          </div>

          <div
            className="landing-hero-visual"
            aria-label="Sports movement analysis preview"
          >
            <div className="analysis-panel analysis-panel-main">
              <div className="analysis-panel-header">
                <span>Movement Scan</span>
                <strong>Live Review</strong>
              </div>

              <div className="pose-stage">
                <div className="scan-line" />
                <div className="court-lines" />

                <div className="pose-figure">
                  <span className="joint joint-head" />
                  <span className="joint joint-shoulder-left" />
                  <span className="joint joint-shoulder-right" />
                  <span className="joint joint-hip-left" />
                  <span className="joint joint-hip-right" />
                  <span className="joint joint-knee-left" />
                  <span className="joint joint-knee-right" />
                  <span className="joint joint-foot-left" />
                  <span className="joint joint-foot-right" />
                  <span className="limb limb-neck" />
                  <span className="limb limb-shoulders" />
                  <span className="limb limb-core-left" />
                  <span className="limb limb-core-right" />
                  <span className="limb limb-thigh-left" />
                  <span className="limb limb-thigh-right" />
                  <span className="limb limb-shin-left" />
                  <span className="limb limb-shin-right" />
                </div>

                <div className="metric-chip chip-knee">
                  Knee angle
                  <strong>42 deg</strong>
                </div>

                <div className="metric-chip chip-load">
                  Landing load
                  <strong>Review</strong>
                </div>
              </div>
            </div>

            <div className="analysis-panel floating-panel risk-panel">
              <span>Risk Indicator</span>
              <strong>Moderate</strong>
              <div className="risk-meter">
                <span />
              </div>
            </div>

            <div className="analysis-panel floating-panel data-panel">
              <Activity size={18} />
              <div>
                <span>Landmarks</span>
                <strong>33 tracked</strong>
              </div>
            </div>
          </div>
        </section>


        <section
          id="how-it-works"
          className="landing-section"
        >
          <div className="landing-section-heading">
            <p className="landing-eyebrow">
              HOW IT WORKS
            </p>

            <h2>
              From athlete profile to movement review.
            </h2>
          </div>

          <div className="work-grid">
            {workSteps.map((step, index) => {
              const Icon = step.icon;

              return (
                <article
                  className="work-card"
                  key={step.title}
                >
                  <div className="work-card-top">
                    <span className="work-number">
                      0{index + 1}
                    </span>

                    <span className="work-icon">
                      <Icon size={22} />
                    </span>
                  </div>

                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                </article>
              );
            })}
          </div>
        </section>


        <section
          id="features"
          className="landing-section landing-section-muted"
        >
          <div className="landing-section-heading">
            <p className="landing-eyebrow">
              FEATURES
            </p>

            <h2>
              A focused toolkit for safer athlete monitoring.
            </h2>
          </div>

          <div className="feature-grid">
            {features.map((feature) => {
              const Icon = feature.icon;

              return (
                <article
                  className="feature-card"
                  key={feature.title}
                >
                  <span className="feature-icon">
                    <Icon size={21} />
                  </span>

                  <h3>{feature.title}</h3>
                  <p>{feature.text}</p>
                </article>
              );
            })}
          </div>
        </section>


        <section
          id="about"
          className="landing-section tech-section"
        >
          <div className="landing-section-heading">
            <p className="landing-eyebrow">
              AI TECHNOLOGY
            </p>

            <h2>
              Built around a transparent analysis pipeline.
            </h2>

            <p>
              The workflow supports movement review by combining video input,
              pose landmarks, and structured feature extraction before presenting
              risk indicators to the user.
            </p>
          </div>

          <div className="tech-flow">
            {techFlow.map((item, index) => (
              <React.Fragment key={item}>
                <div className="tech-step">
                  <span>{index + 1}</span>
                  <strong>{item}</strong>
                </div>

                {index < techFlow.length - 1 && (
                  <ArrowRight
                    className="tech-arrow"
                    size={20}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </section>


        <section className="landing-section preview-section">
          <div className="preview-copy">
            <p className="landing-eyebrow">
              PRODUCT PREVIEW
            </p>

            <h2>
              Keep athlete data, video analysis, and review status in one place.
            </h2>

            <p>
              The dashboard experience is designed for quick scanning, clear
              next actions, and practical follow-up after each uploaded video.
            </p>
          </div>

          <div className="dashboard-preview">
            <div className="preview-sidebar">
              <div className="preview-mark" />
              <span />
              <span />
              <span />
            </div>

            <div className="preview-main">
              <div className="preview-topbar">
                <div>
                  <span>Athlete Dashboard</span>
                  <strong>Training Review</strong>
                </div>

                <div className="status-pill">
                  Active
                </div>
              </div>

              <div className="preview-stats">
                <div>
                  <span>Athlete</span>
                  <strong>Sprinter</strong>
                </div>

                <div>
                  <span>Videos</span>
                  <strong>12</strong>
                </div>

                <div>
                  <span>Status</span>
                  <strong>Review</strong>
                </div>
              </div>

              <div className="preview-content">
                <div className="video-card">
                  <div className="video-frame">
                    <ScanLine size={34} />
                  </div>

                  <span>Jump landing analysis</span>
                </div>

                <div className="indicator-stack">
                  <div className="indicator-row">
                    <span>Knee alignment</span>
                    <strong>Watch</strong>
                  </div>

                  <div className="indicator-row">
                    <span>Hip stability</span>
                    <strong>Stable</strong>
                  </div>

                  <div className="indicator-row">
                    <span>Load symmetry</span>
                    <strong>Review</strong>
                  </div>

                  <div className="mini-chart">
                    <BarChart3 size={38} />
                    <Zap size={18} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>


        <section className="landing-cta">
          <div>
            <p className="landing-eyebrow">
              START SAFER TRAINING
            </p>

            <h2>
              Ready to Make Training Safer?
            </h2>

            <p>
              Create an account or sign in to continue managing athlete profiles
              and video-based movement reviews.
            </p>
          </div>

          <div className="landing-cta-actions">
            <Link
              to="/register"
              className="landing-button landing-button-primary landing-button-large"
            >
              Get Started
              <ArrowRight size={18} />
            </Link>

            <Link
              to="/login"
              className="landing-button landing-button-glass landing-button-large"
            >
              Login
            </Link>
          </div>
        </section>
      </main>


      <footer className="landing-footer">
        <div>
          <Link
            to="/"
            className="landing-brand"
          >
            <span className="landing-logo-icon">
              S
            </span>

            <span>
              <strong>SportRisk</strong>
              <small>Injury Detection</small>
            </span>
          </Link>

          <p>
            Sports Injury Risk Detection helps organize athlete information and
            video-based movement review in a clean, practical workflow.
          </p>
        </div>

        <nav className="footer-links">
          <a href="#home">Home</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
          <Link to="/login">Login</Link>
          <Link to="/register">Get Started</Link>
        </nav>
      </footer>
    </div>
  );
}


export default Landing;
