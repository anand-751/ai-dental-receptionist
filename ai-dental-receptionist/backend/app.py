from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.conversation import router as conversation_router
from backend.utils.session_gc import session_gc_loop
from backend.core.profile_store import LATEST_PROFILE


# ============================================
# PROFILE ROUTER
# ============================================

profile_router = APIRouter()

@profile_router.post("/store-profile")
async def store_profile(profile: dict):
    LATEST_PROFILE.clear()
    LATEST_PROFILE.update(profile)
    print("💾 PROFILE STORED:", LATEST_PROFILE)
    return {"status": "stored"}


# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting AI Dental Receptionist backend")

    gc_task = asyncio.create_task(session_gc_loop())

    try:
        yield
    finally:
        gc_task.cancel()
        print("🛑 Backend shutdown")


# ============================================
# APP
# ============================================

app = FastAPI(
    title="AI Dental Receptionist API",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ROUTERS
# ============================================

app.include_router(conversation_router)
app.include_router(profile_router)

# ============================================
# HEALTH
# ============================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================
# SERVE FRONTEND (ROOT)
# ============================================

# Serve the built React app at "/"
@app.get("/")
async def serve_root():
    return FileResponse("../dist/index.html")


# Serve all static assets (JS, CSS, images)
app.mount("/", StaticFiles(directory="../dist", html=True), name="frontend")
