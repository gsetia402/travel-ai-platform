from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models.auth import UserTable
from models.group_trip import TripTable
from models.document import (
    DocumentUploadResponse,
    VerifyRequest,
    RequirementCreateRequest,
    RequirementResponse,
    DocumentSummaryResponse,
    TravellerReadinessResponse,
    TripDocumentStatsResponse,
    DocumentType,
)
from services.document_service import (
    upload_document,
    list_traveller_documents,
    verify_doc,
    reject_doc,
    add_trip_requirement,
    list_trip_requirements,
    get_document_summary,
    get_traveller_readiness,
    get_trip_document_stats,
    get_trip_all_documents,
    ConflictError,
)
from services.auth_service import get_current_user
from dependencies import require_trip_access

router = APIRouter(tags=["Documents"])


@router.post("/travellers/{traveller_id}/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_doc(
    traveller_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserTable = Depends(get_current_user),
):
    try:
        content = await file.read()
        return upload_document(db, traveller_id, document_type.value, file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/travellers/{traveller_id}/documents", response_model=List[DocumentUploadResponse])
def list_documents(traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return list_traveller_documents(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/documents/{document_id}/verify", response_model=DocumentUploadResponse)
def verify_document(document_id: str, request: VerifyRequest = VerifyRequest(), db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return verify_doc(db, document_id, request)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/documents/{document_id}/reject", response_model=DocumentUploadResponse)
def reject_document(document_id: str, request: VerifyRequest = VerifyRequest(), db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return reject_doc(db, document_id, request)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/documents/{document_id}", status_code=200)
def delete_document(document_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    from models.document import TravellerDocumentTable
    doc = db.query(TravellerDocumentTable).filter(TravellerDocumentTable.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}


@router.get("/documents/{document_id}/download")
def download_document(document_id: str, token: str = None, db: Session = Depends(get_db)):
    """Download a document file via StorageProvider."""
    from models.document import TravellerDocumentTable
    from fastapi.responses import Response
    from services.storage_provider import get_storage_provider, _content_type_from_filename

    if token:
        from services.auth_service import decode_token
        try:
            decode_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    doc = db.query(TravellerDocumentTable).filter(TravellerDocumentTable.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_storage_provider()
    try:
        content = storage.download(doc.file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found on storage")

    content_type = _content_type_from_filename(doc.file_name)
    safe_name = doc.file_name.encode("ascii", "ignore").decode("ascii").replace('"', '') or "document"
    return Response(content=content, media_type=content_type, headers={"Content-Disposition": f'inline; filename="{safe_name}"'})


# --- Requirements ---

@router.post("/trips/{trip_id}/document-requirements", response_model=RequirementResponse, status_code=201)
def create_requirement(trip_id: str, request: RequirementCreateRequest, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return add_trip_requirement(db, trip_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/document-requirements", response_model=List[RequirementResponse])
def get_requirements(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return list_trip_requirements(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/document-requirements/{requirement_id}", status_code=200)
def delete_requirement(requirement_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    from models.document import TripDocumentRequirementTable
    req = db.query(TripDocumentRequirementTable).filter(TripDocumentRequirementTable.requirement_id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(req)
    db.commit()
    return {"message": "Requirement deleted"}


@router.put("/document-requirements/{requirement_id}", response_model=RequirementResponse)
def update_requirement(requirement_id: str, request: RequirementCreateRequest, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    from models.document import TripDocumentRequirementTable
    req = db.query(TripDocumentRequirementTable).filter(TripDocumentRequirementTable.requirement_id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    req.document_type = request.document_type.value
    req.mandatory = request.mandatory
    db.commit()
    db.refresh(req)
    return RequirementResponse.model_validate(req)


# --- Summaries ---

@router.get("/trips/{trip_id}/document-summary", response_model=DocumentSummaryResponse)
def document_summary(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_document_summary(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/travellers/{traveller_id}/readiness", response_model=TravellerReadinessResponse)
def traveller_readiness(traveller_id: str, db: Session = Depends(get_db), user: UserTable = Depends(get_current_user)):
    try:
        return get_traveller_readiness(db, traveller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/document-stats", response_model=TripDocumentStatsResponse)
def trip_document_stats(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_trip_document_stats(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trips/{trip_id}/all-documents")
def trip_all_documents(trip_id: str, db: Session = Depends(get_db), trip: TripTable = Depends(require_trip_access)):
    try:
        return get_trip_all_documents(db, trip_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
