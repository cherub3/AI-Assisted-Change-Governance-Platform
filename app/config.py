"""Application configuration, loaded from environment variables (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()

SYSTEM_ACTOR_ID = 3  # Seed admin user representing automated governance actions


class Config:
    """Base configuration. All values are overridable via .env."""

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///change_governance.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Pinned here deliberately: the governance model requires that the exact
    # Bedrock model + version used for extraction is explicit and auditable,
    # not left to whatever the SDK defaults to.
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "claude-3-5-sonnet-20241022")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
