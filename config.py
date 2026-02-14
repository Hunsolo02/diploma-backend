from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Analyzer
    LANDMARK_WEIGHTS_PATH: str = "/home/ermakov/webproj/trainModel2/landmark_model.pth"
    PHENOTYPE_WEIGHTS_PATH: str = "analyzer/weights/phenotype_best.pt"

    # App
    APP_NAME: str = "Diploma Backend"
    DEBUG: bool = False

    # CORS (comma-separated origins, e.g. "http://localhost:3000,http://localhost:5173")
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
