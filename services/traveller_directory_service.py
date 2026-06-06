"""Phase 17 — Traveller Directory & Groups service."""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.traveller_directory import (
    TravellerMasterTable, TravellerGroupTable, GroupMemberTable, TripTravellerTable,
    TravellerMasterCreate, TravellerMasterUpdate, TravellerMasterResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupDetailResponse,
    TripTravellerResponse,
)


# --------------- Traveller Master ---------------

def create_master_traveller(db: Session, org_id: str, data: TravellerMasterCreate) -> TravellerMasterTable:
    record = TravellerMasterTable(
        master_id=str(uuid.uuid4()),
        organization_id=org_id,
        **data.model_dump(exclude_none=True),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_master_travellers(db: Session, org_id: str, search: Optional[str] = None) -> List[TravellerMasterTable]:
    q = db.query(TravellerMasterTable).filter(TravellerMasterTable.organization_id == org_id)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (TravellerMasterTable.first_name.ilike(like)) |
            (TravellerMasterTable.last_name.ilike(like)) |
            (TravellerMasterTable.phone.ilike(like)) |
            (TravellerMasterTable.email.ilike(like))
        )
    return q.order_by(TravellerMasterTable.first_name).all()


def get_master_traveller(db: Session, org_id: str, master_id: str) -> Optional[TravellerMasterTable]:
    return db.query(TravellerMasterTable).filter(
        TravellerMasterTable.master_id == master_id,
        TravellerMasterTable.organization_id == org_id,
    ).first()


def update_master_traveller(db: Session, org_id: str, master_id: str, data: TravellerMasterUpdate) -> Optional[TravellerMasterTable]:
    record = get_master_traveller(db, org_id, master_id)
    if not record:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record


def delete_master_traveller(db: Session, org_id: str, master_id: str) -> bool:
    record = get_master_traveller(db, org_id, master_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_traveller_groups_for_master(db: Session, master_id: str) -> List[str]:
    """Return group names for a master traveller."""
    rows = db.query(TravellerGroupTable.name).join(
        GroupMemberTable, GroupMemberTable.group_id == TravellerGroupTable.group_id
    ).filter(GroupMemberTable.master_id == master_id).all()
    return [r[0] for r in rows]


def enrich_master_response(db: Session, record: TravellerMasterTable) -> TravellerMasterResponse:
    resp = TravellerMasterResponse.model_validate(record)
    resp.groups = get_traveller_groups_for_master(db, record.master_id)
    return resp


# --------------- Groups ---------------

def create_group(db: Session, org_id: str, data: GroupCreate) -> TravellerGroupTable:
    group = TravellerGroupTable(
        group_id=str(uuid.uuid4()),
        organization_id=org_id,
        name=data.name,
        description=data.description,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_groups(db: Session, org_id: str) -> List[GroupResponse]:
    groups = db.query(TravellerGroupTable).filter(
        TravellerGroupTable.organization_id == org_id
    ).order_by(TravellerGroupTable.name).all()
    results = []
    for g in groups:
        count = db.query(GroupMemberTable).filter(GroupMemberTable.group_id == g.group_id).count()
        results.append(GroupResponse(
            group_id=g.group_id,
            organization_id=g.organization_id,
            name=g.name,
            description=g.description,
            member_count=count,
            created_at=g.created_at,
        ))
    return results


def get_group(db: Session, org_id: str, group_id: str) -> Optional[TravellerGroupTable]:
    return db.query(TravellerGroupTable).filter(
        TravellerGroupTable.group_id == group_id,
        TravellerGroupTable.organization_id == org_id,
    ).first()


def update_group(db: Session, org_id: str, group_id: str, data: GroupUpdate) -> Optional[TravellerGroupTable]:
    group = get_group(db, org_id, group_id)
    if not group:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(group, k, v)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, org_id: str, group_id: str) -> bool:
    group = get_group(db, org_id, group_id)
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


def get_group_detail(db: Session, org_id: str, group_id: str) -> Optional[GroupDetailResponse]:
    group = get_group(db, org_id, group_id)
    if not group:
        return None
    members_rows = db.query(TravellerMasterTable).join(
        GroupMemberTable, GroupMemberTable.master_id == TravellerMasterTable.master_id
    ).filter(GroupMemberTable.group_id == group_id).all()
    members = [enrich_master_response(db, m) for m in members_rows]
    return GroupDetailResponse(
        group_id=group.group_id,
        organization_id=group.organization_id,
        name=group.name,
        description=group.description,
        member_count=len(members),
        created_at=group.created_at,
        members=members,
    )


# --------------- Group Membership ---------------

def add_members_to_group(db: Session, org_id: str, group_id: str, master_ids: List[str]) -> int:
    group = get_group(db, org_id, group_id)
    if not group:
        raise ValueError("Group not found")
    added = 0
    for mid in master_ids:
        exists = db.query(GroupMemberTable).filter(
            GroupMemberTable.group_id == group_id,
            GroupMemberTable.master_id == mid,
        ).first()
        if not exists:
            db.add(GroupMemberTable(id=str(uuid.uuid4()), group_id=group_id, master_id=mid))
            added += 1
    db.commit()
    return added


def remove_member_from_group(db: Session, org_id: str, group_id: str, master_id: str) -> bool:
    group = get_group(db, org_id, group_id)
    if not group:
        return False
    row = db.query(GroupMemberTable).filter(
        GroupMemberTable.group_id == group_id,
        GroupMemberTable.master_id == master_id,
    ).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


# --------------- Trip Integration ---------------

def add_group_to_trip(db: Session, org_id: str, trip_id: str, group_id: str) -> dict:
    """Add all members of a group to a trip. Creates legacy traveller records so
    they show in the existing Travellers tab and work with rooms/docs/etc."""
    from models.group_trip import TravellerTable
    group = get_group(db, org_id, group_id)
    if not group:
        raise ValueError("Group not found")
    masters = db.query(TravellerMasterTable).join(
        GroupMemberTable, GroupMemberTable.master_id == TravellerMasterTable.master_id
    ).filter(GroupMemberTable.group_id == group_id).all()
    added = 0
    skipped = 0
    for m in masters:
        # Check trip_travellers mapping
        exists = db.query(TripTravellerTable).filter(
            TripTravellerTable.trip_id == trip_id,
            TripTravellerTable.master_id == m.master_id,
        ).first()
        if exists:
            skipped += 1
            continue
        # Create mapping
        db.add(TripTravellerTable(
            id=str(uuid.uuid4()),
            trip_id=trip_id,
            master_id=m.master_id,
            added_via=f"group:{group_id}",
        ))
        # Also check if legacy traveller already exists (by phone or email match)
        legacy_exists = False
        if m.phone:
            legacy_exists = db.query(TravellerTable).filter(
                TravellerTable.trip_id == trip_id,
                TravellerTable.phone == m.phone,
            ).first() is not None
        if not legacy_exists and m.email:
            legacy_exists = db.query(TravellerTable).filter(
                TravellerTable.trip_id == trip_id,
                TravellerTable.email == m.email,
            ).first() is not None
        if not legacy_exists:
            db.add(TravellerTable(
                traveller_id=str(uuid.uuid4()),
                trip_id=trip_id,
                first_name=m.first_name,
                last_name=m.last_name,
                phone=m.phone or "",
                email=m.email or "",
                gender=m.gender,
                city=m.city,
                nationality=m.nationality,
                date_of_birth=m.date_of_birth,
                emergency_contact_name=m.emergency_contact_name,
                emergency_contact_phone=m.emergency_contact_phone,
                medical_conditions=m.medical_conditions,
                participation_status="INVITED",
            ))
        added += 1
    db.commit()
    return {"added": added, "skipped": skipped, "total": len(masters)}


def create_and_add_to_group(db: Session, org_id: str, group_id: str, data: TravellerMasterCreate) -> TravellerMasterTable:
    """Create a master traveller and add to group in one step."""
    record = create_master_traveller(db, org_id, data)
    db.add(GroupMemberTable(id=str(uuid.uuid4()), group_id=group_id, master_id=record.master_id))
    db.commit()
    return record


def add_traveller_to_trip(db: Session, trip_id: str, master_id: str, via: str = "manual") -> Optional[TripTravellerTable]:
    """Add single master traveller to trip."""
    exists = db.query(TripTravellerTable).filter(
        TripTravellerTable.trip_id == trip_id,
        TripTravellerTable.master_id == master_id,
    ).first()
    if exists:
        return exists
    row = TripTravellerTable(id=str(uuid.uuid4()), trip_id=trip_id, master_id=master_id, added_via=via)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def remove_traveller_from_trip(db: Session, trip_id: str, master_id: str) -> bool:
    row = db.query(TripTravellerTable).filter(
        TripTravellerTable.trip_id == trip_id,
        TripTravellerTable.master_id == master_id,
    ).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def list_trip_travellers(db: Session, trip_id: str) -> List[TripTravellerResponse]:
    rows = db.query(TripTravellerTable).filter(TripTravellerTable.trip_id == trip_id).all()
    results = []
    for r in rows:
        master = db.query(TravellerMasterTable).filter(TravellerMasterTable.master_id == r.master_id).first()
        resp = TripTravellerResponse(
            id=r.id,
            trip_id=r.trip_id,
            master_id=r.master_id,
            added_via=r.added_via,
            added_at=r.added_at,
            traveller=enrich_master_response(db, master) if master else None,
        )
        results.append(resp)
    return results
