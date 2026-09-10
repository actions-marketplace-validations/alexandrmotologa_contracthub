"""Configuration settings for ContractHub."""

import os
from enum import Enum

from pydantic import BaseModel, Field


class CompatibilityMode(str, Enum):
    BACKWARD = "BACKWARD"
    FORWARD = "FORWARD"
    FULL = "FULL"
    NONE = "NONE"


class SchemaType(str, Enum):
    PROTOBUF = "PROTOBUF"
    OPENAPI = "OPENAPI"
    JSON_SCHEMA = "JSON_SCHEMA"
    AVRO = "AVRO"


class Settings(BaseModel):
    db_url: str = Field(
        default_factory=lambda: os.getenv("CONTRACTHUB_DB", "sqlite:///contracthub.db")
    )
    default_compatibility: CompatibilityMode = Field(
        default_factory=lambda: CompatibilityMode(
            os.getenv("CONTRACTHUB_DEFAULT_COMPATIBILITY", "FULL")
        )
    )
    host: str = Field(default_factory=lambda: os.getenv("CONTRACTHUB_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("CONTRACTHUB_PORT", "8000")))
    registry_url: str = Field(
        default_factory=lambda: os.getenv("CONTRACTHUB_URL", "http://localhost:8000")
    )


settings = Settings()
