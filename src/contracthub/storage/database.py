"""SQLAlchemy Database Configuration and ORM Models."""

from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from contracthub.config import settings


class Base(DeclarativeBase):
    pass


class SubjectModel(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    compatibility_mode = Column(String(32), default="FULL", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    versions = relationship(
        "SchemaVersionModel",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="SchemaVersionModel.version.asc()",
    )


class SchemaVersionModel(Base):
    __tablename__ = "schema_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Global Schema ID
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    schema_type = Column(String(32), nullable=False)  # PROTOBUF, OPENAPI, JSON_SCHEMA
    schema_content = Column(Text, nullable=False)
    fingerprint = Column(String(64), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    subject = relationship("SubjectModel", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("subject_id", "version", name="uq_subject_version"),
    )


_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.db_url
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionFactory


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
