from pydantic import field_validator
from pydantic_settings import BaseSettings

DEFAULT_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str = (
        "postgresql+asyncpg://narudzbe_user:narudzbe_pass@localhost:5432/narudzbe"
    )
    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ISSUER: str = "narudzbe-api"
    CORS_ORIGINS: str = ""
    ADMIN_PASSWORD: str = "admin123"

    @field_validator("DATABASE_URL")
    @classmethod
    def _force_asyncpg(cls, v: str) -> str:
        """Normalize database URLs for SQLAlchemy's async driver."""
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip():
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return ["http://127.0.0.1:5173", "http://localhost:5173"]

    model_config = {
        "env_file": (".env", "../.env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
