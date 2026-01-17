from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from db.mongo import connect_db, close_db
from routes import auth, passkey, track, tasks, jobs, passport, video, radar, proctoring, analytics, recruiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Proof of Skill API",
    description="Identity-First Freelance Marketplace Backend",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(passkey.router, prefix="/auth/passkey", tags=["Passkey"])
app.include_router(track.router, prefix="/track", tags=["Telemetry"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(passport.router, prefix="/passport", tags=["Passport"])
app.include_router(video.router, prefix="/video", tags=["Video"])
app.include_router(radar.router, prefix="/radar", tags=["Radar"])
app.include_router(proctoring.router, prefix="/proctoring", tags=["Proctoring"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(recruiter.router, prefix="/recruiter", tags=["Recruiter"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "proof-of-skill-api"}


@app.get("/")
async def root():
    return {
        "message": "Proof of Skill API",
        "docs": "/docs",
        "health": "/health",
    }
