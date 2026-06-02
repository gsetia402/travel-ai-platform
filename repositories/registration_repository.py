import uuid
import string
import random
import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from models.registration import (
    RegistrationLinkTable,
    RegistrationFormConfigTable,
    InvitationTable,
)
from models.group_trip import TravellerTable

logger = logging.getLogger(__name__)


def _generate_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


# --- Registration Link ---

def create_registration_link(db: Session, trip_id: str, expires_at=None) -> RegistrationLinkTable:
    code = _generate_code()
    while db.query(RegistrationLinkTable).filter(RegistrationLinkTable.registration_code == code).first():
        code = _generate_code()

    link = RegistrationLinkTable(
        registration_link_id=str(uuid.uuid4()),
        trip_id=trip_id,
        registration_code=code,
        active=True,
        expires_at=expires_at,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    logger.info(f"Created registration link {code} for trip {trip_id}")
    return link


def get_link_by_trip(db: Session, trip_id: str) -> Optional[RegistrationLinkTable]:
    return (
        db.query(RegistrationLinkTable)
        .filter(RegistrationLinkTable.trip_id == trip_id)
        .order_by(RegistrationLinkTable.created_at.desc())
        .first()
    )


def get_link_by_code(db: Session, code: str) -> Optional[RegistrationLinkTable]:
    return db.query(RegistrationLinkTable).filter(RegistrationLinkTable.registration_code == code).first()


def deactivate_link(db: Session, code: str) -> Optional[RegistrationLinkTable]:
    link = get_link_by_code(db, code)
    if not link:
        return None
    link.active = False
    db.commit()
    db.refresh(link)
    logger.info(f"Deactivated registration link {code}")
    return link


def is_link_active(db: Session, trip_id: str) -> bool:
    link = get_link_by_trip(db, trip_id)
    return link is not None and link.active


# --- Form Config ---

def upsert_form_config(db: Session, trip_id: str, **kwargs) -> RegistrationFormConfigTable:
    config = db.query(RegistrationFormConfigTable).filter(RegistrationFormConfigTable.trip_id == trip_id).first()
    if config:
        for k, v in kwargs.items():
            setattr(config, k, v)
    else:
        config = RegistrationFormConfigTable(trip_id=trip_id, **kwargs)
        db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_form_config(db: Session, trip_id: str) -> Optional[RegistrationFormConfigTable]:
    return db.query(RegistrationFormConfigTable).filter(RegistrationFormConfigTable.trip_id == trip_id).first()


# --- Duplicate checks ---

def traveller_exists_by_phone(db: Session, trip_id: str, phone: str) -> bool:
    return db.query(TravellerTable).filter(
        TravellerTable.trip_id == trip_id, TravellerTable.phone == phone
    ).first() is not None


def traveller_exists_by_email(db: Session, trip_id: str, email: str) -> bool:
    return db.query(TravellerTable).filter(
        TravellerTable.trip_id == trip_id, TravellerTable.email == email
    ).first() is not None


# --- Invitation ---

def create_invitation(db: Session, trip_id: str, recipient_name: str, phone: str = None, email: str = None) -> InvitationTable:
    inv = InvitationTable(
        invitation_id=str(uuid.uuid4()),
        trip_id=trip_id,
        recipient_name=recipient_name,
        phone=phone,
        email=email,
        invitation_status="SENT",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    logger.info(f"Created invitation {inv.invitation_id} for trip {trip_id}")
    return inv


def get_invitations_by_trip(db: Session, trip_id: str) -> List[InvitationTable]:
    return (
        db.query(InvitationTable)
        .filter(InvitationTable.trip_id == trip_id)
        .order_by(InvitationTable.sent_at.desc())
        .all()
    )
