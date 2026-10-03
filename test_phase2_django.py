"""
Integration Test Suite for AgriScan Phase 2 (Django Web Platform)
Tests Web UI rendering, Session-based Auth, Protected Views,
Role Enforcement, and Outbreak Surveillance.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_dashboard.settings')
django.setup()

from django.test import Client

def test_django_phase2():
    c = Client()
    print("=== [TEST 1] Landing Page / Dashboard ===")
    res = c.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    content = res.content.decode("utf-8")
    assert "AgriScan" in content
    assert "Offline AI" in content
    assert "APMC Mandi Market Pulse" in content
    print("PASS: Dashboard rendered with AgriScan branding and market pulse.\n")

    print("=== [TEST 2] Crop Health Guide & Detail with Diseases ===")
    res = c.get("/crops/")
    assert res.status_code == 200
    print("PASS: /crops/ rendered successfully.")

    res_tomato = c.get("/crop/30/") # Tomato in MySQL
    assert res_tomato.status_code == 200
    tomato_html = res_tomato.content.decode("utf-8")
    assert "Tomato" in tomato_html
    assert "Common Diseases & Pests" in tomato_html
    assert "Early Blight" in tomato_html
    print("PASS: /crop/30/ rendered Tomato with linked common diseases and remedies.\n")

    print("=== [TEST 3] Login and Signup Forms ===")
    res_login = c.get("/login/")
    assert res_login.status_code == 200
    assert "Quick Demo Accounts" in res_login.content.decode("utf-8")
    print("PASS: /login/ form rendered with 1-click demo accounts.")

    res_signup = c.get("/signup/")
    assert res_signup.status_code == 200
    assert "Create Farmer Account" in res_signup.content.decode("utf-8")
    print("PASS: /signup/ form rendered.\n")

    print("=== [TEST 4] Unauthenticated Access Redirection ===")
    res_scans_guest = c.get("/my-scans/")
    assert res_scans_guest.status_code == 302
    assert "/login/" in res_scans_guest.url
    print("PASS: Unauthenticated /my-scans/ correctly redirects to /login/.")

    res_reports_guest = c.get("/field-reports/")
    assert res_reports_guest.status_code == 302
    assert "/login/" in res_reports_guest.url
    print("PASS: Unauthenticated /field-reports/ correctly redirects to /login/.\n")

    print("=== [TEST 5] Farmer Login Flow ===")
    res_auth = c.post("/login/", {"login_id": "9876543210", "password": "farmer123"})
    assert res_auth.status_code in [302, 200], f"Login POST failed: {res_auth.status_code}"
    session = c.session
    assert "token" in session, "JWT token must be saved in Django session"
    assert session["user"]["role"] == "farmer"
    print(f"PASS: Farmer login succeeded. Session active for: {session['user']['name']}\n")

    print("=== [TEST 6] Farmer Accessing /my-scans/ ===")
    res_my_scans = c.get("/my-scans/")
    assert res_my_scans.status_code == 200
    scans_html = res_my_scans.content.decode("utf-8")
    assert "My Field Scans" in scans_html
    print("PASS: Logged-in farmer can view /my-scans/.\n")

    print("=== [TEST 7] Farmer Accessing /field-reports/ (Role Block 403) ===")
    res_blocked = c.get("/field-reports/")
    assert res_blocked.status_code == 403, f"Expected 403 for farmer, got {res_blocked.status_code}"
    assert "Access Denied" in res_blocked.content.decode("utf-8")
    print("PASS: Farmer is strictly forbidden from Officer Field Reports with 403 status.\n")

    print("=== [TEST 8] Officer Login Flow & Field Reports Access ===")
    c.get("/logout/")
    res_officer_login = c.post("/login/", {"login_id": "officer@agriscan.com", "password": "officer123"})
    assert res_officer_login.status_code in [302, 200]
    session_off = c.session
    assert session_off["user"]["role"] == "officer"
    print("PASS: Officer login succeeded.")

    res_field_reports = c.get("/field-reports/")
    assert res_field_reports.status_code == 200
    reports_html = res_field_reports.content.decode("utf-8")
    assert "Field Reports & Outbreak Analytics" in reports_html
    assert "Officer Surveillance Portal" in reports_html
    print("PASS: Officer can successfully open and view /field-reports/.\n")

    print("=== [TEST 9] Logout Flow ===")
    res_logout = c.get("/logout/")
    assert res_logout.status_code == 302
    assert "user" not in c.session
    assert "token" not in c.session
    print("PASS: Logout flushes session completely.\n")

    print("==================================================")
    print(">>> ALL 9 DJANGO PHASE 2 TESTS PASSED! <<<")
    print("==================================================")

if __name__ == "__main__":
    test_django_phase2()
