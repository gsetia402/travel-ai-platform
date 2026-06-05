"""Routes for Trip Documents — coordinator upload/manage, traveller download."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable, TravellerTable
from models.trip_document import (
    TripDocumentType,
    TripDocumentUploadResponse,
    TripDocumentListResponse,
    TripDocumentVisibility,
)
from services.trip_document_service import (
    upload_trip_document,
    list_trip_documents,
    get_trip_document,
    delete_trip_document,
    get_trip_document_download_url,
    get_trip_document_content,
)
from services.auth_service import get_current_user
from services.traveller_portal_service import get_current_traveller
from dependencies import require_trip_access

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Trip Documents"])


# ---------- Coordinator APIs ----------

@router.post("/trips/{trip_id}/trip-documents", response_model=TripDocumentUploadResponse, status_code=201)
async def upload_doc(
    trip_id: str,
    title: str = Form(...),
    document_type: TripDocumentType = Form(...),
    file: UploadFile = File(...),
    description: str = Form(None),
    visibility: TripDocumentVisibility = Form(TripDocumentVisibility.ALL_TRAVELLERS),
    db: Session = Depends(get_db),
    trip: TripTable = Depends(require_trip_access),
    user: UserTable = Depends(get_current_user),
):
    content = await file.read()
    return upload_trip_document(
        db=db,
        trip_id=trip_id,
        organization_id=user.organization_id,
        title=title,
        document_type=document_type.value,
        file_name=file.filename,
        file_content=content,
        description=description,
        visibility=visibility.value,
        uploaded_by=user.email,
    )


@router.get("/trips/{trip_id}/trip-documents", response_model=List[TripDocumentListResponse])
def list_docs(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    return list_trip_documents(db, trip_id)


@router.get("/trip-documents/{document_id}", response_model=TripDocumentUploadResponse)
def get_doc(document_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        doc = get_trip_document(db, document_id)
        return TripDocumentUploadResponse.model_validate(doc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/trip-documents/{document_id}", status_code=200)
def delete_doc(document_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        delete_trip_document(db, document_id)
        return {"message": "Document deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trip-documents/{document_id}/download")
def download_doc(document_id: str, db: Session = Depends(get_db)):
    """Direct download — works for both local and S3 (returns file bytes)."""
    try:
        data, file_name, mime_type = get_trip_document_content(db, document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found on storage")
    safe_name = file_name.encode("ascii", "ignore").decode("ascii").replace('"', '') or "document"
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


# ---------- Traveller APIs ----------

@router.get("/traveller/trip-documents", response_model=List[TripDocumentListResponse])
def traveller_list_docs(db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    docs = list_trip_documents(db, traveller.trip_id)
    # Filter by visibility
    return [d for d in docs if d.visibility == TripDocumentVisibility.ALL_TRAVELLERS.value]


@router.get("/traveller/trip-documents/{document_id}/download")
def traveller_download_doc(document_id: str, db: Session = Depends(get_db), traveller: TravellerTable = Depends(get_current_traveller)):
    try:
        doc = get_trip_document(db, document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Verify document belongs to traveller's trip
    if doc.trip_id != traveller.trip_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if doc.visibility != TripDocumentVisibility.ALL_TRAVELLERS.value:
        raise HTTPException(status_code=403, detail="Document not visible to you")

    try:
        data, file_name, mime_type = get_trip_document_content(db, document_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    safe_name = file_name.encode("ascii", "ignore").decode("ascii").replace('"', '') or "document"
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )
