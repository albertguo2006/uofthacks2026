from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "proof_of_skill"

    # JWT
    jwt_secret: str = "development-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 1
    jwt_refresh_expiry_days: int = 7

    # WebAuthn
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Proof of Skill"
    webauthn_origin: str = "http://localhost:3000"

    # Amplitude
    amplitude_api_key: str = ""

    # TwelveLabs
    twelvelabs_api_key: str = ""

    # Sandbox
    sandbox_runner_url: str = "http://localhost:8080"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
