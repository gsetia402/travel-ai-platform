"""Service layer for Trip Documents (coordinator-uploaded documents for travellers)."""
import uuid
import logging
from typing import List

from sqlalchemy.orm import Session

from models.trip_document import (
    TripDocumentTable,
    TripDocumentUploadResponse,
    TripDocumentListResponse,
    TripDocumentVisibility,
)
from services.storage_provider import get_storage_provider, _content_type_from_filename

logger = logging.getLogger(__name__)


def upload_trip_document(
    db: Session,
    trip_id: str,
    organization_id: str,
    title: str,
    document_type: str,
    file_name: str,
    file_content: bytes,
    description: str = None,
    visibility: str = TripDocumentVisibility.ALL_TRAVELLERS.value,
    uploaded_by: str = None,
) -> TripDocumentUploadResponse:
    storage = get_storage_provider()
    doc_id = str(uuid.uuid4())
    content_type = _content_type_from_filename(file_name)

    # storage key: trip-documents/<trip_id>/<doc_id>/<file_name>
    key = f"trip-documents/{trip_id}/{doc_id}/{file_name}"
    storage.upload(key, file_content, content_type)

    doc = TripDocumentTable(
        document_id=doc_id,
        organization_id=organization_id,
        trip_id=trip_id,
        title=title,
        description=description,
        document_type=document_type,
        file_name=file_name,
        mime_type=content_type,
        file_size=len(file_content),
        storage_provider=storage.provider_name(),
        storage_key=key,
        visibility=visibility,
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info(f"Trip document {doc_id} uploaded for trip {trip_id}")
    return TripDocumentUploadResponse.model_validate(doc)


def list_trip_documents(db: Session, trip_id: str) -> List[TripDocumentListResponse]:
    docs = (
        db.query(TripDocumentTable)
        .filter(TripDocumentTable.trip_id == trip_id)
        .order_by(TripDocumentTable.created_at.desc())
        .all()
    )
    return [TripDocumentListResponse.model_validate(d) for d in docs]


def get_trip_document(db: Session, document_id: str) -> TripDocumentTable:
    doc = db.query(TripDocumentTable).filter(TripDocumentTable.document_id == document_id).first()
    if not doc:
        raise ValueError(f"Trip document not found: {document_id}")
    return doc


def delete_trip_document(db: Session, document_id: str) -> bool:
    doc = get_trip_document(db, document_id)
    # Delete from storage
    try:
        storage = get_storage_provider()
        storage.delete(doc.storage_key)
    except Exception as e:
        logger.warning(f"Failed to delete storage key {doc.storage_key}: {e}")
    db.delete(doc)
    db.commit()
    return True


def get_trip_document_download_url(db: Session, document_id: str) -> dict:
    doc = get_trip_document(db, document_id)
    storage = get_storage_provider()
    url = storage.get_signed_url(doc.storage_key, expires_in=3600)
    return {
        "document_id": doc.document_id,
        "file_name": doc.file_name,
        "mime_type": doc.mime_type,
        "download_url": url,
    }


def get_trip_document_content(db: Session, document_id: str) -> tuple:
    """Return (bytes, file_name, mime_type) for direct download."""
    doc = get_trip_document(db, document_id)
    storage = get_storage_provider()
    data = storage.download(doc.storage_key)
    return data, doc.file_name, doc.mime_type or "application/octet-stream"
