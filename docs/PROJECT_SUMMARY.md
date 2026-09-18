# Sports Injury Risk Detection System
## Concise Mentor / Project Progress Document

### Project Goal

Build a working web platform that uses ordinary sports video to identify biomechanical movement risks, generate explainable injury-risk scores, and support athlete care through coaches, physiotherapists, sports scientists, and administrators.

The main idea is to make injury-risk screening more accessible than expensive motion-capture labs by using 2D video, computer vision, and transparent biomechanical rules.

### Current Status

The project is now a complete full-stack application with:

- Athlete registration, login, profile, injury history, video upload, analysis history, and work/rehab tracking.
- MediaPipe/OpenCV movement analysis pipeline.
- Rule-based injury-risk scoring.
- Skeleton overlay video generation.
- CSV, ML CSV, master dataset, and PDF report exports.
- Coach dashboard, athlete discovery, connection requests, athlete review, and task assignment.
- Physiotherapist dashboard, athlete connections, rehabilitation plans, activities, notes, and recovery resources.
- Sports scientist dashboard, biomechanical analytics, team performance, injury insights, athlete comparison, and research reports.
- Admin dashboard, professional role approvals, user management, analytics, system monitoring, and report management.
- Notification system for requests, approvals, tasks, rehabilitation, and role-specific activity.
- Docker/Docker Compose setup for PostgreSQL, backend, and frontend.

### Technology Stack

| Area | Technology |
|---|---|
| Frontend | React 18, Vite, React Router, Lucide React, CSS |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Computer Vision | OpenCV, MediaPipe Pose Landmarker |
| Scoring | Transparent rule-based biomechanical engine |
| Reports | ReportLab PDFs, CSV exports |
| Deployment | Docker, Docker Compose, Nginx |

### How The System Works

```text
Athlete uploads video
  -> Backend stores video and extracts metadata
  -> MediaPipe detects 33 body landmarks per frame
  -> Low-confidence skeleton frames are filtered/masked
  -> Biomechanics modules calculate movement metrics
  -> Risk engine calculates injury-risk score
  -> Reports and skeleton video are generated
  -> Athlete and approved professionals review results
```

### Main Implemented Modules

#### 1. Authentication and Roles

- Users can register/login with JWT authentication.
- New users start as athletes.
- Users can request professional roles: Coach, Physiotherapist, or Sports Scientist.
- Admin approval is required before professional dashboards become available.
- Backend APIs enforce role permissions independently from frontend navigation.

#### 2. Athlete Workflow

- Athlete dashboard.
- Profile with sport, position, height, weight, training context, and injury history.
- Video upload.
- My Videos.
- Analysis workspace.
- Analysis history.
- My Work for coach tasks and recommendations.
- My Rehabilitation for physiotherapy plans and activities.

#### 3. Movement Analysis Pipeline

The backend analyzes uploaded video using:

- OpenCV video reading.
- MediaPipe Pose Landmarker model.
- Frame-level skeleton validity checks.
- Kinematic calculations for joints, valgus, hip stability, trunk lean, balance, stride, alignment, symmetry, landing mechanics, and force proxy.

#### 4. Risk Scoring

The risk score is explainable and rule-based.

Active weights:

| Risk Domain | Weight |
|---|---:|
| Biomechanical deviations | 38.89% |
| Historical injury factors | 22.22% |
| Movement asymmetry | 22.22% |
| Training load indicators | 16.67% |
| Fatigue indicators | 0% |

Risk categories:

| Score | Meaning |
|---|---|
| 0-24.99 | Low risk |
| 25-49.99 | Moderate risk |
| 50-74.99 | High risk |
| 75-100 | Critical risk |

#### 5. Reports and Outputs

The system generates:

- Skeleton overlay video.
- Frame-level time-series CSV.
- Video-level ML dataset CSV.
- Master ML dataset CSV.
- PDF report with athlete details, movement metrics, risk score, and recommendations.

#### 6. Coach Workflow

- Coach dashboard.
- Discover athletes.
- Connection request management.
- Connected athlete profiles.
- Athlete videos and analyses.
- Report/resource views.
- Training tasks and recommendations for athletes.

#### 7. Physiotherapist Workflow

- Physiotherapist dashboard.
- Athlete discovery and connection requests.
- Athlete video/analysis review.
- Rehabilitation plans.
- Rehabilitation activities.
- Physiotherapist notes.
- Recovery reports and movement analytics.

#### 8. Sports Scientist Workflow

- Sports scientist dashboard.
- Connected athletes.
- Biomechanical analytics.
- Team performance.
- Injury insights.
- Athlete comparison.
- Research reports.

#### 9. Admin Workflow

- Admin dashboard.
- Professional role request review.
- User management.
- Platform analytics.
- System monitoring.
- Report management.
- Admin profile/settings.

#### 10. Notifications

Notifications support:

- Professional role requests and approval decisions.
- Athlete-professional connection activity.
- Coach tasks.
- Rehabilitation plans/activities.
- Role-specific dashboard activity.

Users can view unread counts, mark notifications read/unread, and open notification-linked pages.

### Database Coverage

The database includes models/tables for:

- Users
- Athletes
- Videos
- Analysis results
- Injury history
- Professional role requests
- Professional profiles
- Professional-athlete relationships
- Coach profiles
- Coach tasks
- Rehabilitation plans
- Rehabilitation activities
- Physiotherapist notes
- Notifications

Migration SQL files are included for reproducible setup.

### Docker and Deployment Readiness

The project includes:

- Backend Dockerfile.
- Frontend Dockerfile.
- Nginx configuration.
- Docker Compose file.
- PostgreSQL service.
- Persistent database volume.
- Persistent backend uploads volume.
- `.env.example` templates.

Important deployment note:

- `SECRET_KEY` must be provided in `.env`; it should not be hardcoded.
- Runtime uploads and generated reports must remain outside Git and be stored in Docker volumes or deployment storage.

### Verification Results

Recent final audit verification:

| Check | Result |
|---|---|
| Frontend production build | Passed |
| Backend tests | 50 passed |
| Backend root API smoke test | Passed |
| Database connection smoke test | Passed |
| Docker Compose config validation | Passed when `SECRET_KEY` is provided |

Known non-blocking warnings:

- Vite dependency `"use client"` warnings.
- Vite large bundle warning.
- One Python deprecation warning for `datetime.utcnow()` in PDF generation.

### GitHub Readiness

Safe to commit:

- Source code.
- Static logo/favicon assets.
- MediaPipe model file.
- Docker files.
- Database migrations.
- Documentation.
- Tests.
- `.env.example` files.

Must not commit:

- `.env`
- `node_modules/`
- `backend/myvenv/`
- `backend/uploads/`
- `frontend/dist/`
- `__pycache__/`
- `.pytest_cache/`
- Generated videos, generated PDFs, generated CSVs, logs, local DB files, private keys, tokens, or secrets.

### Mentor Demo Flow

Recommended demonstration order:

1. Show landing/login/register.
2. Login as athlete.
3. Open athlete profile and injury history.
4. Upload or open a video.
5. Open analysis page and show:
   - Original video.
   - Skeleton overlay video.
   - Risk score.
   - Top risk factors.
   - Charts and metrics.
   - Report downloads.
6. Show My Work and My Rehabilitation.
7. Show professional role request flow.
8. Show admin approval flow.
9. Show coach/physiotherapist/sports scientist dashboards.
10. Show notifications.
11. Explain Docker deployment and test results.


