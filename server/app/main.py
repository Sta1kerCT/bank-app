from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from .models.database import init_db
from .api import accounts, transactions
from .monitoring.metrics import metrics_endpoint, PrometheusMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Server started successfully")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Bank API", lifespan=lifespan)

app.add_middleware(PrometheusMiddleware)

app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])

@app.get("/metrics")
async def metrics(request: Request):
    return metrics_endpoint(request)

@app.get("/")
async def root():
    return {"message": "Bank API Server"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}