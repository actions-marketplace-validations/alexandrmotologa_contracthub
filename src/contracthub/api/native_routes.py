"""Native ContractHub REST API Endpoints under /v1."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import (
    CompatibilityMode,
    CompatibilityResult,
    SchemaType,
)
from contracthub.storage.database import get_db
from contracthub.storage.repository import SchemaRepository

router = APIRouter(prefix="/v1", tags=["Native Registry"])


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class RegisterSchemaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_content: str = Field(alias="schema")
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")
    mode: CompatibilityMode | None = None
    force: bool = False


class RegisterSchemaResponse(BaseModel):
    id: int
    subject: str
    version: int
    schema_type: str
    fingerprint: str


class DirectDiffRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    base_schema: str = Field(alias="baseSchema")
    candidate_schema: str = Field(alias="candidateSchema")
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")
    mode: CompatibilityMode = CompatibilityMode.FULL


class SubjectDetailResponse(BaseModel):
    name: str
    compatibility_mode: str
    versions: list[int]


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse()


@router.get("/subjects", response_model=list[str])
def list_subjects(db: Session = Depends(get_db)):
    repo = SchemaRepository(db)
    return repo.list_subjects()


@router.get("/subjects/{subject}", response_model=SubjectDetailResponse)
def get_subject_detail(subject: str, db: Session = Depends(get_db)):
    repo = SchemaRepository(db)
    subj = repo.get_subject(subject)
    if not subj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' not found",
        )
    versions = repo.list_versions_for_subject(subject)
    return SubjectDetailResponse(
        name=subj.name,
        compatibility_mode=subj.compatibility_mode,
        versions=versions,
    )


@router.get("/subjects/{subject}/versions", response_model=list[int])
def list_subject_versions(subject: str, db: Session = Depends(get_db)):
    repo = SchemaRepository(db)
    versions = repo.list_versions_for_subject(subject)
    if not versions and not repo.get_subject(subject):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' not found",
        )
    return versions


@router.get("/subjects/{subject}/versions/latest")
def get_latest_subject_version(subject: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = SchemaRepository(db)
    latest = repo.get_latest_version(subject)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No versions found for subject '{subject}'",
        )
    return {
        "id": latest.id,
        "subject": subject,
        "version": latest.version,
        "schemaType": latest.schema_type,
        "schema": latest.schema_content,
        "fingerprint": latest.fingerprint,
    }


@router.get("/subjects/{subject}/versions/{version}")
def get_subject_version(
    subject: str,
    version: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = SchemaRepository(db)
    v = repo.get_version(subject, version)
    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for subject '{subject}'",
        )
    return {
        "id": v.id,
        "subject": subject,
        "version": v.version,
        "schemaType": v.schema_type,
        "schema": v.schema_content,
        "fingerprint": v.fingerprint,
    }


@router.post("/subjects/{subject}/versions", response_model=RegisterSchemaResponse)
def register_schema(
    subject: str,
    payload: RegisterSchemaRequest,
    db: Session = Depends(get_db),
):
    repo = SchemaRepository(db)
    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(
        payload.schema_content
    )

    subj = repo.get_subject(subject)
    mode = payload.mode
    if not mode:
        mode = CompatibilityMode(subj.compatibility_mode) if subj else CompatibilityMode.FULL

    latest = repo.get_latest_version(subject)
    if latest and not payload.force:
        # Run compatibility check
        check_result = SchemaComparator.compare_strings(
            base_content=latest.schema_content,
            candidate_content=payload.schema_content,
            schema_type=schema_type,
            mode=mode,
        )
        if not check_result.is_compatible:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Candidate schema violates compatibility invariants.",
                    "mode": mode.value,
                    "violations": [v.model_dump() for v in check_result.violations],
                },
            )

    version_model = repo.register_version(
        subject_name=subject,
        schema_content=payload.schema_content,
        schema_type=schema_type,
        default_mode=mode,
    )

    return RegisterSchemaResponse(
        id=version_model.id,
        subject=subject,
        version=version_model.version,
        schema_type=version_model.schema_type,
        fingerprint=version_model.fingerprint,
    )


@router.post(
    "/compatibility/subjects/{subject}/versions/{version}",
    response_model=CompatibilityResult,
)
def test_subject_compatibility(
    subject: str,
    version: str,
    payload: RegisterSchemaRequest,
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
            detail=f"Target version '{version}' not found for subject '{subject}'",
        )

    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(
        payload.schema_content
    )
    subj = repo.get_subject(subject)
    mode = payload.mode or (
        CompatibilityMode(subj.compatibility_mode) if subj else CompatibilityMode.FULL
    )

    return SchemaComparator.compare_strings(
        base_content=target.schema_content,
        candidate_content=payload.schema_content,
        schema_type=schema_type,
        mode=mode,
    )


@router.post("/diff", response_model=CompatibilityResult)
def direct_diff(payload: DirectDiffRequest):
    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(
        payload.base_schema
    )
    return SchemaComparator.compare_strings(
        base_content=payload.base_schema,
        candidate_content=payload.candidate_schema,
        schema_type=schema_type,
        mode=payload.mode,
    )
