import csv
import io
import logging
from typing import List

from sqlalchemy.orm import Session

from models.group_trip import (
    TravellerCreateRequest,
    TravellerUpdateRequest,
    TravellerResponse,
    CSVUploadResponse,
)
from repositories.traveller_repository import (
    add_traveller,
    add_travellers_bulk,
    get_travellers_by_trip,
    get_traveller_by_id,
    update_traveller as repo_update_traveller,
    delete_traveller,
    delete_travellers_bulk,
)
from repositories.trip_repository import get_trip_by_id

logger = logging.getLogger(__name__)

REQUIRED_CSV_COLUMNS = {"first_name", "last_name", "phone", "email"}
OPTIONAL_CSV_COLUMNS = {
    "gender", "department", "city", "date_of_birth", "age",
    "emergency_contact_name", "emergency_contact_phone", "emergency_relationship",
    "medical_conditions", "allergies", "special_requirements",
    "dietary_preferences", "passport_number", "nationality", "participation_status",
}
VALID_CSV_COLUMNS = REQUIRED_CSV_COLUMNS | OPTIONAL_CSV_COLUMNS


def create_traveller(db: Session, trip_id: str, request: TravellerCreateRequest) -> TravellerResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    traveller = add_traveller(db, trip_id, request)
    return TravellerResponse.model_validate(traveller)


def list_travellers(db: Session, trip_id: str) -> List[TravellerResponse]:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    travellers = get_travellers_by_trip(db, trip_id)
    return [TravellerResponse.model_validate(t) for t in travellers]


def get_single_traveller(db: Session, traveller_id: str) -> TravellerResponse:
    traveller = get_traveller_by_id(db, traveller_id)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")
    return TravellerResponse.model_validate(traveller)


def update_traveller(db: Session, traveller_id: str, request: TravellerUpdateRequest) -> TravellerResponse:
    traveller = repo_update_traveller(db, traveller_id, request)
    if not traveller:
        raise ValueError(f"Traveller not found: {traveller_id}")
    return TravellerResponse.model_validate(traveller)


def remove_traveller(db: Session, traveller_id: str) -> bool:
    deleted = delete_traveller(db, traveller_id)
    if not deleted:
        raise ValueError(f"Traveller not found: {traveller_id}")
    return True


def remove_travellers_bulk(db: Session, trip_id: str, traveller_ids: List[str]) -> int:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")
    if not traveller_ids:
        raise ValueError("No traveller IDs provided")
    count = delete_travellers_bulk(db, trip_id, traveller_ids)
    logger.info(f"Bulk deleted {count}/{len(traveller_ids)} travellers from trip {trip_id}")
    return count


def upload_travellers_csv(db: Session, trip_id: str, file_content: bytes) -> CSVUploadResponse:
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError(f"Trip not found: {trip_id}")

    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Invalid file encoding. Please upload a UTF-8 CSV file.")

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV file is empty or has no headers.")

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_CSV_COLUMNS - headers
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    valid_travellers: List[TravellerCreateRequest] = []
    errors: List[str] = []
    total = 0

    for i, row in enumerate(reader, start=2):
        total += 1
        cleaned = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

        first_name = cleaned.get("first_name", "")
        last_name = cleaned.get("last_name", "")
        phone = cleaned.get("phone", "")
        email = cleaned.get("email", "")

        if not first_name or not last_name or not phone or not email:
            errors.append(f"Row {i}: missing required field (first_name, last_name, phone, or email)")
            continue

        try:
            age_raw = cleaned.get("age", "")
            age_val = int(age_raw) if age_raw else None
        except ValueError:
            age_val = None

        valid_travellers.append(
            TravellerCreateRequest(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                gender=cleaned.get("gender") or None,
                department=cleaned.get("department") or None,
                city=cleaned.get("city") or None,
                date_of_birth=cleaned.get("date_of_birth") or None,
                age=age_val,
                emergency_contact_name=cleaned.get("emergency_contact_name") or None,
                emergency_contact_phone=cleaned.get("emergency_contact_phone") or None,
                emergency_relationship=cleaned.get("emergency_relationship") or None,
                medical_conditions=cleaned.get("medical_conditions") or None,
                allergies=cleaned.get("allergies") or None,
                special_requirements=cleaned.get("special_requirements") or None,
                dietary_preferences=cleaned.get("dietary_preferences") or None,
                passport_number=cleaned.get("passport_number") or None,
                nationality=cleaned.get("nationality") or None,
                participation_status=cleaned.get("participation_status") or "INVITED",
            )
        )

    if valid_travellers:
        add_travellers_bulk(db, trip_id, valid_travellers)

    logger.info(f"CSV upload for trip {trip_id}: {len(valid_travellers)}/{total} successful")

    return CSVUploadResponse(
        total_rows=total,
        successful=len(valid_travellers),
        failed=len(errors),
        errors=errors if errors else None,
    )
