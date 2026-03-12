"""
PFM-Agents API Server
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routes import bookkeeping, health

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期"""
    logger.info("Starting PFM-Agents API...")
    yield
    logger.info("Shutting down PFM-Agents API...")


app = FastAPI(
    title="PFM-Agents API",
    description="個人財務管理多代理人系統 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(health.router, tags=["Health"])
app.include_router(bookkeeping.router, prefix="/api/bookkeeping", tags=["Bookkeeping"])


@app.get("/")
async def root():
    return {
        "name": "PFM-Agents API",
        "version": "0.1.0",
        "status": "running",
    }
