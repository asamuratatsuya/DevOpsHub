from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import get_db
from app.db.session import engine
from app.models import Project
from app.routers.project import router as project_router
from app.routers.cluster import router as cluster_router
from app.routers.pods import router as pods_router
from app.routers.deployments import router as deployments_router
from app.routers.pipelines import router as pipelines_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 首次启动时，根据模型创建数据库表
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DevOpsHub API",
    description="DevOps 自动化交付管理平台 API",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(project_router)
app.include_router(cluster_router)
app.include_router(deployments_router)
app.include_router(pods_router)
app.include_router(pipelines_router)


@app.get("/")
async def root():
    return {
        "message": "欢迎使用 DevOpsHub API",
        "status": "运行中",
        "version": "1.0.1",
    }


@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc

    return {
        "status": "healthy",
        "service": "DevOpsHub Backend",
        "database": "connected",
    }
