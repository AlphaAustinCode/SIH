import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import tracks, trains, maintenance, blocks

app = FastAPI(
    title="AI Automatic Block Planning Engine",
    description="Indian Railways SIH - Multi-department Maintenance Optimization",
    version="1.0.0"
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(tracks.router, prefix="/api")
app.include_router(trains.router, prefix="/api")
app.include_router(maintenance.router, prefix="/api")
app.include_router(blocks.router, prefix="/api")

# Serve compiled frontend from Railway/dist if available
DIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Railway", "dist")
if os.path.exists(DIST_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(DIST_PATH, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_PATH, "index.html"))