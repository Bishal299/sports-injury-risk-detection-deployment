from fastapi import FastAPI
from sqlalchemy import text
from app.routes.users import router as user_router
from app.routes.athletes import router as athlete_router
from app.routes.auth import router as auth_router
from app.routes.injury import router as injury_router
from app.routes.videos import router as video_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import User, UserRole, Athlete, InjuryHistory
# from app.models import User, UserRole, Athlete, InjuryHistory
from dotenv import load_dotenv
import os

load_dotenv()

Base.metadata.create_all(bind=engine)
def get_cors_origins():
    configured_origins = os.getenv("BACKEND_CORS_ORIGINS")

    if configured_origins:
        return [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]


os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/frames", exist_ok=True)


app = FastAPI(
    title="Sports Injury Risk Detection API"
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=get_cors_origins(),

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


@app.get("/")
def root():
    return {
        "message": "Sports Injury Risk Detection API is running"
    }


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
