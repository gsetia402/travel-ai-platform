"""
Multi-tenant isolation tests.
Verifies that Organization A cannot access Organization B's data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app


SQLALCHEMY_TEST_URL = "sqlite:///./test_multitenant.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def register_org(name: str, email: str) -> dict:
    resp = client.post("/auth/register", json={
        "full_name": f"{name} Admin",
        "email": email,
        "phone": "9999999999",
        "password": "password123",
        "organization_name": name,
        "organization_type": "TRAVEL_AGENCY",
        "role": "ADMIN",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_trip(token: str, trip_name: str = "Test Trip") -> dict:
    resp = client.post("/trips", json={
        "trip_name": trip_name,
        "organization_name": "Test Org",
        "destination": "Goa",
        "start_date": "2026-07-01",
        "end_date": "2026-07-05",
        "days": 5,
        "traveller_count": 10,
        "budget": 100000,
    }, headers=auth_header(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestMultiTenantIsolation:
    """Organization A cannot access Organization B's trips."""

    def test_org_a_cannot_see_org_b_trips(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        # Org A creates a trip
        trip_a = create_trip(org_a["access_token"], "Trip A")

        # Org B creates a trip
        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A can only see their own trips
        resp = client.get("/trips", headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 200
        trips = resp.json()
        trip_ids = [t["trip_id"] for t in trips]
        assert trip_a["trip_id"] in trip_ids
        assert trip_b["trip_id"] not in trip_ids

        # Org B can only see their own trips
        resp = client.get("/trips", headers=auth_header(org_b["access_token"]))
        assert resp.status_code == 200
        trips = resp.json()
        trip_ids = [t["trip_id"] for t in trips]
        assert trip_b["trip_id"] in trip_ids
        assert trip_a["trip_id"] not in trip_ids

    def test_org_a_cannot_get_org_b_trip_by_id(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A tries to access Org B's trip
        resp = client.get(f"/trips/{trip_b['trip_id']}", headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 403

    def test_org_a_cannot_update_org_b_trip(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A tries to update Org B's trip
        resp = client.put(f"/trips/{trip_b['trip_id']}", json={
            "trip_name": "Hacked Trip"
        }, headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 403

    def test_org_a_cannot_delete_org_b_trip(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A tries to delete Org B's trip
        resp = client.delete(f"/trips/{trip_b['trip_id']}", headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 403

    def test_org_a_cannot_access_org_b_travellers(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A tries to list Org B's travellers
        resp = client.get(f"/trips/{trip_b['trip_id']}/travellers", headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 403

    def test_org_a_cannot_add_traveller_to_org_b_trip(self):
        org_a = register_org("Org A", "admin@orga.com")
        org_b = register_org("Org B", "admin@orgb.com")

        trip_b = create_trip(org_b["access_token"], "Trip B")

        # Org A tries to add traveller to Org B's trip
        resp = client.post(f"/trips/{trip_b['trip_id']}/travellers", json={
            "first_name": "Hack",
            "last_name": "Attempt",
            "phone": "1234567890",
            "email": "hack@test.com",
        }, headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 403

    def test_unauthenticated_request_returns_401(self):
        resp = client.get("/trips")
        assert resp.status_code == 401

    def test_org_can_access_own_trip(self):
        org_a = register_org("Org A", "admin@orga.com")
        trip_a = create_trip(org_a["access_token"], "Trip A")

        resp = client.get(f"/trips/{trip_a['trip_id']}", headers=auth_header(org_a["access_token"]))
        assert resp.status_code == 200
        assert resp.json()["trip_id"] == trip_a["trip_id"]
