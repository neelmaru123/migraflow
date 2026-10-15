import os
import secrets
from typing import Any, List, Literal
from dotenv import find_dotenv, load_dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically load .env variables into process os.environ for LangChain/LangSmith AI tracing
load_dotenv(find_dotenv())


class Settings(BaseSettings):
    PROJECT_NAME: str = "Migraflow API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "default_secret_key_change_me_in_production"
    JWT_SECRET_KEY: str = "default_jwt_secret_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: Literal["lax", "none", "strict"] = "lax"
    COOKIE_DOMAIN: str | None = None

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://host.docker.internal:8000"
    AGENT_DOCKER_IMAGE: str = "data-migration-agent:latest"

    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres_password@localhost:5432/migration_platform"
    REDIS_URL: str = "redis://redis:6379/0"

    # Google Gmail SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = "Migraflow Platform"
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 5
    RESET_PASSWORD_COOLDOWN_SECONDS: int = 60

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: Literal["gemini", "openai"] = "gemini"
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: float = 360.0

    # LangSmith AI Observability & Error Tracing (default disabled for privacy)
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "migraflow-platform"

    MAX_CLOUD_ROWS: int = 500_000
    MAX_CLOUD_SIZE_MB: float = 100.0

    CORS_ORIGINS: List[str] | str = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        origins: List[str] = []
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.startswith("["):
                import json
                try:
                    origins = json.loads(v_strip)
                except Exception:
                    origins = [i.strip() for i in v.split(",") if i.strip()]
            else:
                origins = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = list(v)
        else:
            return v
        # UK GDPR compliance: Exclude '*' wildcard to prevent credential leakage via CORS
        return [o.rstrip("/") for o in origins if o != "*"]

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        insecure_defaults = {
            "default_secret_key_change_me_in_production",
            "default_jwt_secret_key_change_me_in_production",
            "generate_a_random_32_character_secret_key",
            "099b4b4cd041aac731d6f92587f2ecba8a63943386e52d5ecc0cb75c7654d493",
            "07e7dbe717bb29263fb626af239df7a10a554c5eb1efd459cdb268d08b54b45c",
            "secret",
            "changeme",
            "password",
            "<GENERATE_SECRET_KEY_MIN_32_CHARS>",
            "<GENERATE_JWT_SECRET_KEY_MIN_32_CHARS>",
            "migraflow-super-secret-key-change-in-production",
            "migraflow-jwt-super-secret-key-change-in-production",
        }

        is_production = self.ENVIRONMENT.lower() == "production"

        if is_production:
            sec_lower = (self.SECRET_KEY or "").lower()
            jwt_lower = (self.JWT_SECRET_KEY or "").lower()
            is_insecure_sec = (
                not self.SECRET_KEY
                or self.SECRET_KEY.strip() in insecure_defaults
                or len(self.SECRET_KEY.strip()) < 32
                or any(b in sec_lower for b in ["change_me", "change-me", "change_in_production", "change-in-production"])
            )
            if is_insecure_sec:
                raise ValueError(
                    "Production configuration error: Insecure default SECRET_KEY is not permitted. "
                    "SECRET_KEY must be explicitly configured with at least 32 characters of high-entropy secret material. "
                    "Using default/placeholder secrets or silently auto-generating keys at startup is prohibited."
                )

            is_insecure_jwt = (
                not self.JWT_SECRET_KEY
                or self.JWT_SECRET_KEY.strip() in insecure_defaults
                or len(self.JWT_SECRET_KEY.strip()) < 32
                or any(b in jwt_lower for b in ["change_me", "change-me", "change_in_production", "change-in-production"])
            )
            if is_insecure_jwt:
                raise ValueError(
                    "Production configuration error: Insecure default JWT_SECRET_KEY is not permitted. "
                    "JWT_SECRET_KEY must be explicitly configured with at least 32 characters of high-entropy secret material. "
                    "Using default/placeholder secrets or silently auto-generating keys at startup is prohibited."
                )
            if self.SECRET_KEY.strip() == self.JWT_SECRET_KEY.strip():
                raise ValueError(
                    "Production configuration error: SECRET_KEY and JWT_SECRET_KEY must not share "
                    "the same value to ensure cryptographic domain separation."
                )

            if "COOKIE_SECURE" not in os.environ:
                if self.FRONTEND_URL.startswith("https://"):
                    self.COOKIE_SECURE = True
                elif self.FRONTEND_URL.startswith("http://"):
                    # Direct IP or HTTP deployments require COOKIE_SECURE=False so browsers accept session cookies
                    self.COOKIE_SECURE = False
                else:
                    self.COOKIE_SECURE = True
        else:
            # Development / testing: keep setup practical without weakening production
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_defaults:
                self.SECRET_KEY = "dev_secret_key_only_for_testing_and_local_development_32chars"
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY in insecure_defaults:
                self.JWT_SECRET_KEY = "dev_jwt_key_only_for_testing_and_local_development_32chars"

        return self

    model_config = SettingsConfigDict(
        env_file=("../../.env", "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
