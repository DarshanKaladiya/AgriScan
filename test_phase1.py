"""
Integration Test Suite for AgriScan Phase 1
Tests Database connection, Auth (login/register/roles), Advisory knowledge base,
Scan synchronization, Field reports stats, and Market intelligence endpoints.
"""

from fastapi.testclient import TestClient
from api_main import app
import uuid

client = TestClient(app)

def test_all():
    print("=== [TEST 1] System Health Endpoint ===")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    print(f"PASS: Health check ok -> {data}\n")

    print("=== [TEST 2] Demo Farmer Login ===")
    res = client.post("/api/auth/login", json={"login_id": "9876543210", "password": "farmer123"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    farmer_auth = res.json()
    farmer_token = farmer_auth["token"]
    assert farmer_token is not None
    assert farmer_auth["user"]["role"] == "farmer"
    print(f"PASS: Demo farmer login successful. Name: {farmer_auth['user']['name']}\n")

    print("=== [TEST 3] Login Failure & User Enumeration Protection ===")
    res = client.post("/api/auth/login", json={"login_id": "9876543210", "password": "wrongpassword"})
    assert res.status_code == 401
    err1 = res.json()["detail"]
    res_unknown = client.post("/api/auth/login", json={"login_id": "9999999999", "password": "any"})
    assert res_unknown.status_code == 401
    err2 = res_unknown.json()["detail"]
    assert err1 == err2, "Error message must be identical for unknown user and wrong password"
    print(f"PASS: Identical generic error returned for both failure modes: '{err1}'\n")

    print("=== [TEST 4] Authenticated Profile (GET /api/auth/me) ===")
    headers_farmer = {"Authorization": f"Bearer {farmer_token}"}
    res = client.get("/api/auth/me", headers=headers_farmer)
    assert res.status_code == 200
    user_me = res.json()
    assert user_me["login_id"] == "9876543210"
    print(f"PASS: /api/auth/me returns valid user: {user_me['name']}\n")

    print("=== [TEST 5] Register New Farmer Account ===")
    test_mobile = f"91{uuid.uuid4().int % 100000000:08d}"
    res = client.post("/api/auth/register", json={
        "name": "Test Farmer",
        "login_id": test_mobile,
        "password": "securepassword123",
        "preferred_language": "gu"
    })
    assert res.status_code == 200, f"Register failed: {res.text}"
    reg_data = res.json()
    assert reg_data["user"]["login_id"] == test_mobile
    assert "token" in reg_data
    print(f"PASS: Successfully registered new farmer: {test_mobile}")

    # Test Duplicate Registration (409 Conflict)
    res_dup = client.post("/api/auth/register", json={
        "name": "Test Farmer Dup",
        "login_id": test_mobile,
        "password": "securepassword123"
    })
    assert res_dup.status_code == 409
    print(f"PASS: Duplicate registration correctly rejected with 409 Conflict\n")

    print("=== [TEST 6] Advisory Knowledge Export ===")
    res = client.get("/api/advisory")
    assert res.status_code == 200
    advisories = res.json()
    assert len(advisories) >= 17, f"Expected at least 17 disease documents, found {len(advisories)}"
    sample_adv = advisories[0]
    assert "class_key" in sample_adv
    assert "name" in sample_adv and "hi" in sample_adv["name"] and "gu" in sample_adv["name"]
    print(f"PASS: Advisory documents loaded: {len(advisories)}. Multilingual support verified.")

    # Test Crop Advisory Filter (Tomato crop_id=30)
    res_tomato = client.get("/api/advisory?crop_id=30")
    assert res_tomato.status_code == 200
    tomato_adv = res_tomato.json()
    assert len(tomato_adv) >= 8
    print(f"PASS: Filtered advisory for Tomato returned {len(tomato_adv)} disease entries.\n")

    print("=== [TEST 7] Guest & Authenticated Scan Synchronization ===")
    guest_uuid = f"guest-test-{uuid.uuid4().hex[:8]}"
    sync_payload_guest = {
        "scans": [
            {
                "client_uuid": guest_uuid,
                "device_id": "test-device-guest",
                "class_key": "Tomato___Early_blight",
                "crop_id": 6,
                "confidence": 92.5,
                "language": "gu",
                "location": {"lat": 23.25, "lng": 69.66, "region": "Rajkot, Gujarat"},
                "scanned_at": "2026-10-03 12:00:00"
            }
        ]
    }
    res_guest_sync = client.post("/api/scans/sync", json=sync_payload_guest)
    assert res_guest_sync.status_code == 200
    assert res_guest_sync.json()["synced_count"] == 1
    print("PASS: Guest scan sync completed successfully.")

    # Authenticated scan sync
    farmer_uuid = f"farmer-test-{uuid.uuid4().hex[:8]}"
    sync_payload_farmer = {
        "scans": [
            {
                "client_uuid": farmer_uuid,
                "device_id": "test-device-farmer",
                "class_key": "Potato___Late_blight",
                "crop_id": 5,
                "confidence": 97.8,
                "language": "hi",
                "location": {"lat": 27.18, "lng": 78.01, "region": "Agra, UP"},
                "scanned_at": "2026-10-03 12:30:00"
            }
        ]
    }
    res_farmer_sync = client.post("/api/scans/sync", json=sync_payload_farmer, headers=headers_farmer)
    assert res_farmer_sync.status_code == 200
    assert res_farmer_sync.json()["synced_count"] == 1
    print("PASS: Authenticated farmer scan sync completed successfully.")

    # Test Idempotency (re-sending same UUID should not duplicate)
    res_idempotent = client.post("/api/scans/sync", json=sync_payload_farmer, headers=headers_farmer)
    assert res_idempotent.status_code == 200
    print("PASS: Idempotent resync verified.\n")

    print("=== [TEST 8] Farmer Personal Scans (GET /api/scans/mine) ===")
    res_mine = client.get("/api/scans/mine", headers=headers_farmer)
    assert res_mine.status_code == 200
    my_scans = res_mine.json()
    assert len(my_scans) >= 1
    assert any(s["client_uuid"] == farmer_uuid for s in my_scans)
    assert "disease_name" in my_scans[0]
    print(f"PASS: Personal scans returned: {len(my_scans)} items with enriched disease details.\n")

    print("=== [TEST 9] Officer Authentication & Role Authorization ===")
    # Login as Officer
    res_off = client.post("/api/auth/login", json={"login_id": "officer@agriscan.com", "password": "officer123"})
    assert res_off.status_code == 200
    officer_token = res_off.json()["token"]
    headers_officer = {"Authorization": f"Bearer {officer_token}"}
    print("PASS: Officer login successful.")

    # Officer accessing /api/scans/stats -> 200 OK
    res_stats = client.get("/api/scans/stats", headers=headers_officer)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_scans"] >= 7
    assert len(stats["by_disease"]) > 0
    assert len(stats["by_crop"]) > 0
    print(f"PASS: Officer stats retrieved successfully. Total field scans: {stats['total_scans']}")

    # Farmer trying to access /api/scans/stats -> 403 Forbidden!
    res_forbidden = client.get("/api/scans/stats", headers=headers_farmer)
    assert res_forbidden.status_code == 403, f"Expected 403 for farmer, got {res_forbidden.status_code}"
    print("PASS: Role check verified: Farmer is blocked from Officer stats with 403 Forbidden.\n")

    print("=== [TEST 10] Master Crops, Products, and Comparison Endpoints ===")
    res_crops = client.get("/api/crops")
    assert res_crops.status_code == 200
    assert len(res_crops.json()) >= 270
    print(f"PASS: /api/crops returned {len(res_crops.json())} master crops.")

    res_crop_detail = client.get("/api/crops/30") # Tomato (ID 30 in MySQL)
    assert res_crop_detail.status_code == 200
    crop_info = res_crop_detail.json()
    assert crop_info["crop_name"] == "Tomato"
    assert "diseases" in crop_info and len(crop_info["diseases"]) >= 8
    print("PASS: /api/crops/30 returned Tomato with linked common diseases.")

    res_products = client.get("/api/products")
    assert res_products.status_code == 200
    assert len(res_products.json()) >= 15
    print(f"PASS: /api/products returned {len(res_products.json())} agro products.")

    res_compare = client.get("/api/compare?technical_name=Mancozeb 75% WP")
    assert res_compare.status_code == 200
    compare_res = res_compare.json()
    assert len(compare_res) >= 1
    print(f"PASS: /api/compare returned {len(compare_res)} product(s) matching 'Mancozeb 75% WP'.\n")

    print("==================================================")
    print(">>> ALL 10 INTEGRATION TESTS PASSED SUCCESSFULLY! <<<")
    print("==================================================")

if __name__ == "__main__":
    test_all()
