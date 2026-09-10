"""Repository for Subject and SchemaVersion persistence."""

import hashlib

from sqlalchemy.orm import Session

from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.storage.database import SchemaVersionModel, SubjectModel


class SchemaRepository:
    """Encapsulates CRUD operations for subjects and schema versions."""

    def __init__(self, db: Session):
        self.db = db

    def list_subjects(self) -> list[str]:
        subjects = self.db.query(SubjectModel.name).order_by(SubjectModel.name.asc()).all()
        return [s[0] for s in subjects]

    def get_subject(self, name: str) -> SubjectModel | None:
        return self.db.query(SubjectModel).filter(SubjectModel.name == name).first()

    def get_or_create_subject(
        self,
        name: str,
        default_mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> SubjectModel:
        subject = self.get_subject(name)
        if not subject:
            subject = SubjectModel(name=name, compatibility_mode=default_mode.value)
            self.db.add(subject)
            self.db.commit()
            self.db.refresh(subject)
        return subject

    def get_latest_version(self, subject_name: str) -> SchemaVersionModel | None:
        subject = self.get_subject(subject_name)
        if not subject:
            return None
        return (
            self.db.query(SchemaVersionModel)
            .filter(SchemaVersionModel.subject_id == subject.id)
            .order_by(SchemaVersionModel.version.desc())
            .first()
        )

    def get_version(self, subject_name: str, version_num: int) -> SchemaVersionModel | None:
        subject = self.get_subject(subject_name)
        if not subject:
            return None
        return (
            self.db.query(SchemaVersionModel)
            .filter(
                SchemaVersionModel.subject_id == subject.id,
                SchemaVersionModel.version == version_num,
            )
            .first()
        )

    def list_versions_for_subject(self, subject_name: str) -> list[int]:
        subject = self.get_subject(subject_name)
        if not subject:
            return []
        versions = (
            self.db.query(SchemaVersionModel.version)
            .filter(SchemaVersionModel.subject_id == subject.id)
            .order_by(SchemaVersionModel.version.asc())
            .all()
        )
        return [v[0] for v in versions]

    def get_schema_by_id(self, schema_id: int) -> SchemaVersionModel | None:
        return self.db.query(SchemaVersionModel).filter(SchemaVersionModel.id == schema_id).first()

    def register_version(
        self,
        subject_name: str,
        schema_content: str,
        schema_type: SchemaType,
        default_mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> SchemaVersionModel:
        subject = self.get_or_create_subject(subject_name, default_mode)

        # Check if identical content already registered as latest
        latest = self.get_latest_version(subject_name)
        fingerprint = hashlib.sha256(schema_content.encode("utf-8")).hexdigest()

        if latest and latest.fingerprint == fingerprint:
            return latest

        next_version = (latest.version + 1) if latest else 1

        new_version = SchemaVersionModel(
            subject_id=subject.id,
            version=next_version,
            schema_type=schema_type.value,
            schema_content=schema_content,
            fingerprint=fingerprint,
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version
