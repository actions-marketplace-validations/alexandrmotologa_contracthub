"""Native ContractHub REST API Endpoints under /v1."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from contracthub.core.codegen import CodeGenerator
from contracthub.core.comparator import SchemaComparator
from contracthub.core.mock_generator import MockGenerator
from contracthub.core.models import (
    CompatibilityMode,
    CompatibilityResult,
    SchemaType,
)
from contracthub.core.semver import SemVerEngine, SemVerRecommendation
from contracthub.core.validator import PayloadValidator, ValidationResult
from contracthub.core.webhook_dispatcher import WebhookDispatcher
from contracthub.storage.database import WebhookModel, get_db
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
    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(payload.schema_content)

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
            WebhookDispatcher.dispatch(
                db=db,
                event_name="COMPATIBILITY_REJECTED",
                payload={
                    "subject": subject,
                    "mode": mode.value,
                    "violations": [v.model_dump() for v in check_result.violations],
                },
            )
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

    WebhookDispatcher.dispatch(
        db=db,
        event_name="VERSION_REGISTERED",
        payload={
            "id": version_model.id,
            "subject": subject,
            "version": version_model.version,
            "schema_type": version_model.schema_type,
            "fingerprint": version_model.fingerprint,
        },
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

    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(payload.schema_content)
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
    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(payload.base_schema)
    return SchemaComparator.compare_strings(
        base_content=payload.base_schema,
        candidate_content=payload.candidate_schema,
        schema_type=schema_type,
        mode=payload.mode,
    )


class MockDataRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_content: str = Field(alias="schema")
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")
    target_entity: str | None = Field(default=None, alias="targetEntity")


@router.post("/mock")
def generate_mock_data(payload: MockDataRequest) -> Any:
    return MockGenerator.generate(
        schema_content=payload.schema_content,
        schema_type=payload.schema_type,
        target_entity=payload.target_entity,
    )


class CreateWebhookRequest(BaseModel):
    url: str
    secret: str | None = None
    events: str = "VERSION_REGISTERED,COMPATIBILITY_REJECTED"


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: str
    is_active: bool


@router.post("/webhooks", response_model=WebhookResponse)
def create_webhook(payload: CreateWebhookRequest, db: Session = Depends(get_db)):
    wh = WebhookModel(
        url=payload.url,
        secret=payload.secret,
        events=payload.events,
        is_active=True,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return WebhookResponse(
        id=wh.id,
        url=wh.url,
        events=wh.events,
        is_active=wh.is_active,
    )


@router.get("/webhooks", response_model=list[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    items = db.query(WebhookModel).order_by(WebhookModel.id.asc()).all()
    return [
        WebhookResponse(
            id=wh.id,
            url=wh.url,
            events=wh.events,
            is_active=wh.is_active,
        )
        for wh in items
    ]


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    wh = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )
    db.delete(wh)
    db.commit()
    return {"status": "deleted", "webhook_id": webhook_id}


class DirectValidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_content: str = Field(alias="schema")
    payload: Any
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")
    target_entity: str | None = None


class SubjectValidateRequest(BaseModel):
    payload: Any
    target_entity: str | None = None


@router.post("/validate", response_model=ValidationResult)
def validate_payload_direct(payload: DirectValidateRequest) -> ValidationResult:
    """Validate a JSON payload directly against an arbitrary schema string."""
    return PayloadValidator.validate(
        schema_content=payload.schema_content,
        payload=payload.payload,
        schema_type=payload.schema_type,
        target_entity=payload.target_entity,
    )


@router.post("/subjects/{subject}/versions/{version}/validate", response_model=ValidationResult)
def validate_payload_against_subject(
    subject: str,
    version: int,
    payload: SubjectValidateRequest,
    db: Session = Depends(get_db),
) -> ValidationResult:
    """Validate a JSON payload against a registered subject version."""
    repo = SchemaRepository(db)
    schema_obj = repo.get_version(subject, version)
    if not schema_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' version {version} not found",
        )

    return PayloadValidator.validate(
        schema_content=schema_obj.schema_content,
        payload=payload.payload,
        schema_type=SchemaType(schema_obj.schema_type),
        target_entity=payload.target_entity,
    )


class DirectSemVerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    base_schema: str = Field(alias="baseSchema")
    candidate_schema: str = Field(alias="candidateSchema")
    current_version: str = "1.0.0"
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")
    mode: CompatibilityMode = CompatibilityMode.FULL


class SubjectSemVerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    candidate_schema: str = Field(alias="candidateSchema")
    current_version: str | None = None
    mode: CompatibilityMode = CompatibilityMode.FULL


@router.post("/semver", response_model=SemVerRecommendation)
def recommend_semver_direct(payload: DirectSemVerRequest) -> SemVerRecommendation:
    """Recommend next SemVer bump for arbitrary base and candidate schemas."""
    schema_type = payload.schema_type or SchemaComparator.detect_schema_type(
        payload.candidate_schema
    )
    return SemVerEngine.recommend_bump(
        base_content=payload.base_schema,
        candidate_content=payload.candidate_schema,
        schema_type=schema_type,
        current_version=payload.current_version,
        mode=payload.mode,
    )


@router.post("/subjects/{subject}/versions/{version}/semver", response_model=SemVerRecommendation)
def recommend_semver_against_subject(
    subject: str,
    version: int,
    payload: SubjectSemVerRequest,
    db: Session = Depends(get_db),
) -> SemVerRecommendation:
    """Recommend next SemVer bump for a candidate schema against a registered subject version."""
    repo = SchemaRepository(db)
    base_obj = repo.get_version(subject, version)
    if not base_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' version {version} not found",
        )

    cur_version = payload.current_version or f"1.{version}.0"
    schema_type = SchemaType(base_obj.schema_type)

    return SemVerEngine.recommend_bump(
        base_content=base_obj.schema_content,
        candidate_content=payload.candidate_schema,
        schema_type=schema_type,
        current_version=cur_version,
        mode=payload.mode,
    )


class DirectCodegenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_content: str = Field(alias="schema")
    target: str = "typescript"
    schema_type: SchemaType | None = Field(default=None, alias="schemaType")


class CodegenResponse(BaseModel):
    code: str
    target: str
    schema_type: str


@router.post("/codegen", response_model=CodegenResponse)
def generate_client_models(payload: DirectCodegenRequest) -> CodegenResponse:
    """Generate typed client data models (TypeScript or Pydantic v2) from schema content."""
    detected_type = payload.schema_type or SchemaComparator.detect_schema_type(
        payload.schema_content
    )
    code = CodeGenerator.generate(
        schema_content=payload.schema_content,
        target=payload.target,
        schema_type=detected_type,
    )
    return CodegenResponse(
        code=code,
        target=payload.target,
        schema_type=detected_type.value,
    )


@router.get("/subjects/{subject}/versions/{version}/codegen", response_model=CodegenResponse)
def generate_models_from_subject_version(
    subject: str,
    version: str,
    target: str = "typescript",
    db: Session = Depends(get_db),
) -> CodegenResponse:
    """Generate typed client models from a schema version registered in the repository."""
    repo = SchemaRepository(db)
    if version == "latest":
        schema_obj = repo.get_latest_version(subject)
    else:
        try:
            v_int = int(version)
            schema_obj = repo.get_version(subject, v_int)
        except ValueError:
            schema_obj = None

    if not schema_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema version '{version}' not found for subject '{subject}'",
        )

    stype = SchemaType(schema_obj.schema_type)
    code = CodeGenerator.generate(
        schema_content=schema_obj.schema_content,
        target=target,
        schema_type=stype,
    )
    return CodegenResponse(
        code=code,
        target=target,
        schema_type=stype.value,
    )
