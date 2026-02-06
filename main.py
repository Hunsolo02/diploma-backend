from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from database import engine, Base
from models import Item, User, Region, Phenotype, FaceFeature  # noqa: F401 - register models before create_all
from routers import items, auth, analyzer, regions, phenotypes, face_features


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup if needed


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(analyzer.router, prefix="/api")
app.include_router(regions.router, prefix="/api")
app.include_router(phenotypes.router, prefix="/api")
app.include_router(face_features.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Welcome to Diploma Backend API", "docs": "/docs"}
