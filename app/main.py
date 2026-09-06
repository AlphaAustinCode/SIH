from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import blocks, kpis, maintenance, optimization, tracks
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Railway Block Optimizer API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(optimization.router)
app.include_router(blocks.router)
app.include_router(kpis.router)
app.include_router(maintenance.router)
app.include_router(tracks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
