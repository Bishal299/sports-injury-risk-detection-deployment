from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from app.routes.users import router as user_router
from app.routes.athletes import router as athlete_router
from app.routes.auth import router as auth_router
from app.routes.injury import router as injury_router
from app.routes.videos import router as video_router
from app.routes.analysis import router as analysis_router
from app.routes.admin_dashboard import router as admin_dashboard_router
from app.routes.admin_profile import router as admin_profile_router
from app.routes.admin_reports import router as admin_reports_router
from app.routes.admin_users import router as admin_users_router
from app.routes.notifications import router as notification_router
from app.routes.professional_role_requests import router as professional_role_request_router
from app.routes.admin_professional_role_requests import router as admin_professional_role_request_router
from app.routes.coach import router as coach_router
from app.routes.physiotherapist import router as physiotherapist_router
from app.routes.sports_scientist import router as sports_scientist_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import (
    User,
    UserRole,
    Athlete,
    InjuryHistory,
    Video,
    AnalysisResult,
    ProfessionalRoleRequest,
    ProfessionalProfile,
    ProfessionalAthleteRelationship,
    CoachProfile,
    CoachTask,
    CoachAthleteRelationship,
    RehabilitationPlan,
    RehabilitationActivity,
    PhysiotherapistNote,
    Notification,
)
from dotenv import load_dotenv
import os

load_dotenv()

Base.metadata.create_all(bind=engine)


def ensure_coach_task_analysis_links():
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text(
                "ALTER TABLE coach_tasks "
                "ADD COLUMN IF NOT EXISTS analysis_id UUID REFERENCES analysis_results(analysis_id) ON DELETE SET NULL"
            ))
            connection.execute(text(
                "ALTER TABLE coach_tasks "
                "ADD COLUMN IF NOT EXISTS video_id UUID REFERENCES videos(video_id) ON DELETE SET NULL"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_coach_tasks_analysis_id ON coach_tasks(analysis_id)"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_coach_tasks_video_id ON coach_tasks(video_id)"
            ))
        elif engine.dialect.name == "sqlite":
            columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(coach_tasks)")).fetchall()
            }
            if "analysis_id" not in columns:
                connection.execute(text("ALTER TABLE coach_tasks ADD COLUMN analysis_id TEXT"))
            if "video_id" not in columns:
                connection.execute(text("ALTER TABLE coach_tasks ADD COLUMN video_id TEXT"))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_coach_tasks_analysis_id ON coach_tasks(analysis_id)"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_coach_tasks_video_id ON coach_tasks(video_id)"
            ))


ensure_coach_task_analysis_links()


def ensure_injury_history_schema():
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS affected_side VARCHAR(20) DEFAULT 'NOT_APPLICABLE' NOT NULL"
            ))
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'UNKNOWN' NOT NULL"
            ))
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS recovery_date DATE"
            ))
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS remarks TEXT"
            ))
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL"
            ))
            connection.execute(text(
                "ALTER TABLE injury_history "
                "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL"
            ))
            connection.execute(text(
                "UPDATE injury_history SET affected_side = 'NOT_APPLICABLE' "
                "WHERE affected_side IS NULL OR affected_side NOT IN ('LEFT', 'RIGHT', 'BILATERAL', 'NOT_APPLICABLE')"
            ))
            connection.execute(text(
                "UPDATE injury_history SET status = 'UNKNOWN' "
                "WHERE status IS NULL OR status NOT IN ('ACTIVE', 'RECOVERED', 'CHRONIC', 'UNKNOWN')"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_id ON injury_history(athlete_id)"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_injury_date ON injury_history(athlete_id, injury_date)"
            ))
        elif engine.dialect.name == "sqlite":
            columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(injury_history)")).fetchall()
            }
            if "affected_side" not in columns:
                connection.execute(text(
                    "ALTER TABLE injury_history ADD COLUMN affected_side TEXT DEFAULT 'NOT_APPLICABLE' NOT NULL"
                ))
            if "status" not in columns:
                connection.execute(text(
                    "ALTER TABLE injury_history ADD COLUMN status TEXT DEFAULT 'UNKNOWN' NOT NULL"
                ))
            if "recovery_date" not in columns:
                connection.execute(text("ALTER TABLE injury_history ADD COLUMN recovery_date DATE"))
            if "remarks" not in columns:
                connection.execute(text("ALTER TABLE injury_history ADD COLUMN remarks TEXT"))
            if "created_at" not in columns:
                connection.execute(text("ALTER TABLE injury_history ADD COLUMN created_at TIMESTAMP"))
            if "updated_at" not in columns:
                connection.execute(text("ALTER TABLE injury_history ADD COLUMN updated_at TIMESTAMP"))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_id ON injury_history(athlete_id)"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_injury_history_athlete_injury_date ON injury_history(athlete_id, injury_date)"
            ))


ensure_injury_history_schema()


def get_cors_origins():
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    configured_origins = os.getenv("BACKEND_CORS_ORIGINS")
    if configured_origins:
        extra = [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]
        return list(set(default_origins + extra))
    return default_origins


os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/frames", exist_ok=True)
os.makedirs("uploads/analysis", exist_ok=True)
os.makedirs("uploads/analysis/skeleton", exist_ok=True)
os.makedirs("uploads/analysis/reports", exist_ok=True)
os.makedirs("uploads/professional_documents", exist_ok=True)


app = FastAPI(
    title="Sports Injury Risk Detection API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(athlete_router)
app.include_router(injury_router)
app.include_router(video_router)
app.include_router(analysis_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_profile_router)
app.include_router(admin_reports_router)
app.include_router(admin_users_router)
app.include_router(notification_router)
app.include_router(professional_role_request_router)
app.include_router(admin_professional_role_request_router)
app.include_router(coach_router)
app.include_router(physiotherapist_router)
app.include_router(sports_scientist_router)



@app.get("/")
def root():
    return {
        "message": "Sports Injury Risk Detection API is running"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).fetchone()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": str(e)
            }
        )


@app.get("/test-db")
def test_database():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

        return {
            "status": "success",
            "message": "PostgreSQL connection successful"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
