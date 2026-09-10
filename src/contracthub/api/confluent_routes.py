"""Confluent Schema Registry Wire-Compatible Endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.storage.database import get_db
from contracthub.storage.repository import SchemaRepository

router = APIRouter(tags=["Confluent Wire Compatibility"])


class ConfluentRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_content: str = Field(alias="schema")
    schema_type: str | None = Field(default="PROTOBUF", alias="schemaType")
    references: list[dict[str, Any]] | None = None


class ConfluentRegisterResponse(BaseModel):
    id: int


class ConfluentCompatibilityResponse(BaseModel):
    is_compatible: bool


@router.get("/subjects", response_model=list[str])
def confluent_list_subjects(db: Session = Depends(get_db)):
    repo = SchemaRepository(db)
    return repo.list_subjects()


@router.get("/subjects/{subject}/versions", response_model=list[int])
def confluent_list_versions(subject: str, db: Session = Depends(get_db)):
    repo = SchemaRepository(db)
    versions = repo.list_versions_for_subject(subject)
    if not versions and not repo.get_subject(subject):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 40401, "message": f"Subject '{subject}' not found"},
        )
    return versions


@router.get("/subjects/{subject}/versions/{version}")
def confluent_get_version(
    subject: str,
    version: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = SchemaRepository(db)
    if version == "latest":
        v = repo.get_latest_version(subject)
    else:
        try:
            v = repo.get_version(subject, int(version))
        except ValueError:
            v = None

    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": 40402,
                "message": f"Version '{version}' not found for subject '{subject}'",
            },
        )

    return {
        "subject": subject,
        "id": v.id,
        "version": v.version,
        "schemaType": v.schema_type,
        "schema": v.schema_content,
    }


@router.get("/schemas/ids/{schema_id}")
def confluent_get_schema_by_id(
    schema_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = SchemaRepository(db)
    s = repo.get_schema_by_id(schema_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 40403, "message": f"Schema {schema_id} not found"},
        )
    return {
        "schema": s.schema_content,
        "schemaType": s.schema_type,
    }


@router.post("/subjects/{subject}/versions", response_model=ConfluentRegisterResponse)
def confluent_register_schema(
    subject: str,
    payload: ConfluentRegisterRequest,
    db: Session = Depends(get_db),
):
    repo = SchemaRepository(db)
    st_str = (payload.schema_type or "PROTOBUF").upper()
    try:
        schema_type = SchemaType(st_str)
    except ValueError:
        schema_type = SchemaComparator.detect_schema_type(payload.schema_content)

    subj = repo.get_subject(subject)
    mode = CompatibilityMode(subj.compatibility_mode) if subj else CompatibilityMode.FULL

    latest = repo.get_latest_version(subject)
    if latest:
        check = SchemaComparator.compare_strings(
            base_content=latest.schema_content,
            candidate_content=payload.schema_content,
            schema_type=schema_type,
            mode=mode,
        )
        if not check.is_compatible:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": 409,
                    "message": "Schema being registered is incompatible with an earlier schema",
                },
            )

    version_model = repo.register_version(
        subject_name=subject,
        schema_content=payload.schema_content,
        schema_type=schema_type,
        default_mode=mode,
    )
    return ConfluentRegisterResponse(id=version_model.id)


@router.post(
    "/compatibility/subjects/{subject}/versions/{version}",
    response_model=ConfluentCompatibilityResponse,
)
def confluent_check_compatibility(
    subject: str,
    version: str,
    payload: ConfluentRegisterRequest,
    db: Session = Depends(get_db),
):
    repo = SchemaRepository(db)
    if version == "latest":
        target = repo.get_latest_version(subject)
    else:
        try:
            target = repo.get_version(subject, int(version))
        except ValueError:
            target = None

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": 40402, "message": f"Version '{version}' not found"},
        )

    st_str = (payload.schema_type or "PROTOBUF").upper()
    try:
        schema_type = SchemaType(st_str)
    except ValueError:
        schema_type = SchemaComparator.detect_schema_type(payload.schema_content)

    subj = repo.get_subject(subject)
    mode = CompatibilityMode(subj.compatibility_mode) if subj else CompatibilityMode.FULL

    res = SchemaComparator.compare_strings(
        base_content=target.schema_content,
        candidate_content=payload.schema_content,
        schema_type=schema_type,
        mode=mode,
    )
    return ConfluentCompatibilityResponse(is_compatible=res.is_compatible)


@router.get("/config")
def confluent_get_global_config():
    return {"compatibilityLevel": "FULL"}
