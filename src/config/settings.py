"""
Application configuration management.

This module defines a `Settings` class using Pydantic's `BaseSettings` to pull
configuration values from environment variables.  It makes it easy to
customise behaviour without hard‑coding paths and secrets.
"""

try:
    # Pydantic v2 stores BaseSettings in pydantic_settings
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for Pydantic v1
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Global application settings.

    The default values can be overridden by providing a `.env` file or by
    exporting environment variables at runtime.
    """

    api_version: str = "v1"
    env: str = "dev"
    model_path: str = "models/baseline_logreg.pkl"
    preprocessor_path: str = "models/preprocessor.pkl"
    raw_runtime_bundle_path: str = "models/logreg_raw_runtime_bundle.joblib"
    raw_runtime_manifest_path: str = "models/logreg_raw_runtime_manifest.json"
    raw_runtime_artifact_path: str = "models/logreg_raw.pkl"
    raw_runtime_threshold_path: str = "models/best_threshold.txt"
    raw_runtime_coefficients_path: str = "models/model_coefficients.csv"

    github_repo: str = "BeediGoua/Brokerflow_ai"
    model_release_tag: str = "v1.0-models"
    model_release_base_url: str | None = None
    model_auto_download: bool = True
    model_download_timeout_seconds: int = 45

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instantiate a single settings object that can be imported across the app
settings = Settings()