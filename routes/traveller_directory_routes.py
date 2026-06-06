"""Phase 17 — Traveller Directory & Groups API routes."""
import csv
import io
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from database import get_db
from services.auth_service import get_current_user
from models.traveller_directory import (
    TravellerMasterCreate, TravellerMasterUpdate, TravellerMasterResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupDetailResponse,
    TripTravellerResponse,
)
from services.traveller_directory_service import (
    create_master_traveller, list_master_travellers, get_master_traveller,
    update_master_traveller, delete_master_traveller, enrich_master_response,
    create_group, list_groups, get_group_detail, update_group, delete_group,
    add_members_to_group, remove_member_from_group,
    add_group_to_trip, add_traveller_to_trip, remove_traveller_from_trip,
    list_trip_travellers,
)

router = APIRouter(tags=["Traveller Directory"])


# --------------- Traveller Master ---------------

@router.get("/travellers/master", response_model=List[TravellerMasterResponse])
def api_list_master_travellers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    records = list_master_travellers(db, user.organization_id, search)
    return [enrich_master_response(db, r) for r in records]


@router.post("/travellers/master", response_model=TravellerMasterResponse, status_code=201)
def api_create_master_traveller(
    data: TravellerMasterCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    record = create_master_traveller(db, user.organization_id, data)
    return enrich_master_response(db, record)


@router.get("/travellers/master/{master_id}", response_model=TravellerMasterResponse)
def api_get_master_traveller(
    master_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    record = get_master_traveller(db, user.organization_id, master_id)
    if not record:
        raise HTTPException(status_code=404, detail="Traveller not found")
    return enrich_master_response(db, record)


@router.put("/travellers/master/{master_id}", response_model=TravellerMasterResponse)
def api_update_master_traveller(
    master_id: str,
    data: TravellerMasterUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    record = update_master_traveller(db, user.organization_id, master_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Traveller not found")
    return enrich_master_response(db, record)


@router.delete("/travellers/master/{master_id}", status_code=204)
def api_delete_master_traveller(
    master_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not delete_master_traveller(db, user.organization_id, master_id):
        raise HTTPException(status_code=404, detail="Traveller not found")


@router.post("/travellers/master/import-csv", status_code=201)
async def api_import_master_travellers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Import master travellers from CSV. Expected columns: first_name, last_name, phone, email, gender, city, nationality."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        fname = (row.get("first_name") or "").strip()
        lname = (row.get("last_name") or "").strip()
        if not fname or not lname:
            errors.append(f"Row {i}: missing first_name or last_name")
            continue
        data = TravellerMasterCreate(
            first_name=fname,
            last_name=lname,
            phone=(row.get("phone") or "").strip() or None,
            email=(row.get("email") or "").strip() or None,
            gender=(row.get("gender") or "").strip() or None,
            city=(row.get("city") or "").strip() or None,
            nationality=(row.get("nationality") or "").strip() or None,
        )
        create_master_traveller(db, user.organization_id, data)
        created += 1
    return {"total_rows": created + len(errors), "successful": created, "failed": len(errors), "errors": errors[:20]}


# --------------- Groups ---------------

@router.get("/groups", response_model=List[GroupResponse])
def api_list_groups(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_groups(db, user.organization_id)


@router.post("/groups", response_model=GroupResponse, status_code=201)
def api_create_group(data: GroupCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    group = create_group(db, user.organization_id, data)
    return GroupResponse(
        group_id=group.group_id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        member_count=0,
        created_at=group.created_at,
    )


@router.get("/groups/{group_id}", response_model=GroupDetailResponse)
def api_get_group(group_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    detail = get_group_detail(db, user.organization_id, group_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Group not found")
    return detail


@router.put("/groups/{group_id}", response_model=GroupResponse)
def api_update_group(group_id: str, data: GroupUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    group = update_group(db, user.organization_id, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    from services.traveller_directory_service import get_group as _get_group
    from models.traveller_directory import GroupMemberTable
    count = db.query(GroupMemberTable).filter(GroupMemberTable.group_id == group_id).count()
    return GroupResponse(
        group_id=group.group_id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        member_count=count,
        created_at=group.created_at,
    )


@router.delete("/groups/{group_id}", status_code=204)
def api_delete_group(group_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not delete_group(db, user.organization_id, group_id):
        raise HTTPException(status_code=404, detail="Group not found")


# --------------- Group Membership ---------------

@router.post("/groups/{group_id}/members")
def api_add_group_members(
    group_id: str,
    master_ids: List[str],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        added = add_members_to_group(db, user.organization_id, group_id, master_ids)
        return {"added": added}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/groups/{group_id}/members/{master_id}", status_code=204)
def api_remove_group_member(
    group_id: str,
    master_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not remove_member_from_group(db, user.organization_id, group_id, master_id):
        raise HTTPException(status_code=404, detail="Member not found in group")


@router.post("/groups/{group_id}/add-traveller", response_model=TravellerMasterResponse, status_code=201)
def api_create_traveller_in_group(
    group_id: str,
    data: TravellerMasterCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a master traveller and add to group in one step."""
    from services.traveller_directory_service import create_and_add_to_group, get_group
    group = get_group(db, user.organization_id, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    record = create_and_add_to_group(db, user.organization_id, group_id, data)
    return enrich_master_response(db, record)


@router.post("/groups/{group_id}/import-csv", status_code=201)
async def api_import_csv_into_group(
    group_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Import CSV: create master travellers and add them to the group automatically."""
    from services.traveller_directory_service import create_and_add_to_group, get_group
    group = get_group(db, user.organization_id, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        fname = (row.get("first_name") or "").strip()
        lname = (row.get("last_name") or "").strip()
        if not fname or not lname:
            errors.append(f"Row {i}: missing first_name or last_name")
            continue
        data = TravellerMasterCreate(
            first_name=fname,
            last_name=lname,
            phone=(row.get("phone") or "").strip() or None,
            email=(row.get("email") or "").strip() or None,
            gender=(row.get("gender") or "").strip() or None,
            city=(row.get("city") or "").strip() or None,
            nationality=(row.get("nationality") or "").strip() or None,
        )
        create_and_add_to_group(db, user.organization_id, group_id, data)
        created += 1
    return {"total_rows": created + len(errors), "successful": created, "failed": len(errors), "errors": errors[:20]}


# --------------- Trip Integration ---------------

@router.post("/trips/{trip_id}/groups/{group_id}")
def api_add_group_to_trip(
    trip_id: str,
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        result = add_group_to_trip(db, user.organization_id, trip_id, group_id)
        return {"group_id": group_id, "trip_id": trip_id, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/directory-travellers/{master_id}")
def api_add_traveller_to_trip(
    trip_id: str,
    master_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    row = add_traveller_to_trip(db, trip_id, master_id, via="manual")
    if not row:
        raise HTTPException(status_code=400, detail="Failed to add traveller")
    return {"id": row.id, "trip_id": trip_id, "master_id": master_id}


@router.delete("/trips/{trip_id}/directory-travellers/{master_id}", status_code=204)
def api_remove_traveller_from_trip(
    trip_id: str,
    master_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not remove_traveller_from_trip(db, trip_id, master_id):
        raise HTTPException(status_code=404, detail="Traveller not in trip")


@router.get("/trips/{trip_id}/directory-travellers", response_model=List[TripTravellerResponse])
def api_list_trip_travellers(
    trip_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_trip_travellers(db, trip_id)
