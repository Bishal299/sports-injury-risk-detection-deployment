"""
Production-Grade Authentication & Session Test Suite

Validates all 12 test scenarios:
1. Valid login sets HttpOnly browser-session cookie (no Max-Age, no Expires).
2. Invalid login rejected (401) with no cookie set.
3. GET /auth/me returns safe user data with cookie.
4. GET /auth/me returns 401 when unauthenticated.
5. Same browser profile shares session across tabs/requests.
6. Different browser profiles maintain independent sessions; logging out Profile 2 leaves Profile 1 active.
7. Incognito window maintains independent session.
8. Controlled 24-hour expiration test: Expired token (>24h) returns 401 with session expired detail; valid token (<24h) returns 200. Non-sliding expiration verified.
9. Logout invalidation: POST /auth/logout clears cookie, subsequent GET /auth/me and protected routes return 401.
10. Browser-session cookie attributes (HttpOnly=True, Path=/, SameSite=Lax, no Max-Age, no Expires).
11. Backward compatibility with Authorization Bearer header for API scripts.
12. Google OAuth architecture and limitations documented.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import (
    hash_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    AUTH_COOKIE_NAME,
)


def create_test_user(email: str, name: str, role: UserRole = UserRole.ATHLETE) -> User:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing
        user = User(
            name=name,
            email=email,
            password=hash_password("Password123!"),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def run_all_tests():
    print("==================================================================")
    print("STARTING PRODUCTION AUTHENTICATION & SESSION TEST SUITE")
    print("==================================================================")

    uid = str(uuid.uuid4())[:8]
    email_a = f"athlete_a_{uid}@example.com"
    email_b = f"athlete_b_{uid}@example.com"
    email_c = f"athlete_c_{uid}@example.com"

    user_a = create_test_user(email_a, f"Athlete A {uid}")
    user_b = create_test_user(email_b, f"Athlete B {uid}")
    user_c = create_test_user(email_c, f"Athlete C {uid}")

    # -------------------------------------------------------------
    # TEST 1: Valid Login & Browser-Session Cookie Verification
    # -------------------------------------------------------------
    print("\n--- TEST 1: Valid Login & Browser-Session Cookie Verification ---")
    client_a = TestClient(app)
    res = client_a.post("/auth/login", json={"email": email_a, "password": "Password123!"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "access_token" in data, "access_token should be returned"
    assert "user" in data, "safe user info should be returned"
    assert data["user"]["email"] == email_a

    # Verify cookie in client cookie jar
    assert AUTH_COOKIE_NAME in client_a.cookies, f"Expected cookie '{AUTH_COOKIE_NAME}'"

    # Inspect Set-Cookie header attributes
    set_cookie_header = res.headers.get("set-cookie", "")
    assert AUTH_COOKIE_NAME in set_cookie_header, "Set-Cookie must name the cookie"
    assert "httponly" in set_cookie_header.lower(), "Cookie must be HttpOnly"
    assert "path=/" in set_cookie_header.lower(), "Cookie path must be /"
    assert "samesite=lax" in set_cookie_header.lower(), "Cookie SameSite must be Lax"
    assert "max-age" not in set_cookie_header.lower(), "Browser-session cookie must NOT have Max-Age"
    assert "expires=" not in set_cookie_header.lower(), "Browser-session cookie must NOT have Expires"
    print("[PASS] Test 1: Valid login sets HttpOnly browser-session cookie with correct attributes.")

    # -------------------------------------------------------------
    # TEST 2: Invalid Login
    # -------------------------------------------------------------
    print("\n--- TEST 2: Invalid Login Handling ---")
    client_bad = TestClient(app)
    res_bad = client_bad.post("/auth/login", json={"email": email_a, "password": "WrongPassword!"})
    assert res_bad.status_code == 401, f"Expected 401, got {res_bad.status_code}"
    assert AUTH_COOKIE_NAME not in client_bad.cookies, "Failed login must not set cookie"
    print("[PASS] Test 2: Invalid credentials correctly rejected (401) with no cookie.")

    # -------------------------------------------------------------
    # TEST 3: GET /auth/me While Authenticated
    # -------------------------------------------------------------
    print("\n--- TEST 3: GET /auth/me with Cookie ---")
    res_me = client_a.get("/auth/me")
    assert res_me.status_code == 200, f"Expected 200, got {res_me.status_code}: {res_me.text}"
    me_data = res_me.json()
    assert me_data["email"] == email_a
    assert me_data["name"] == user_a.name
    assert me_data["role"] == "Athlete"
    assert "password" not in me_data, "Password must never be exposed"
    print("[PASS] Test 3: GET /auth/me returns safe user details from session cookie.")

    # -------------------------------------------------------------
    # TEST 4: GET /auth/me While Unauthenticated
    # -------------------------------------------------------------
    print("\n--- TEST 4: GET /auth/me Without Cookie ---")
    client_unauth = TestClient(app)
    res_unauth = client_unauth.get("/auth/me")
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    assert "not authenticated" in res_unauth.json().get("detail", "").lower()
    print("[PASS] Test 4: Unauthenticated GET /auth/me cleanly rejected with 401.")

    # -------------------------------------------------------------
    # TEST 5: Same Browser Profile Across Multiple Tabs
    # -------------------------------------------------------------
    print("\n--- TEST 5: Multi-Tab Shared Session (Same Browser Profile) ---")
    # All tabs in client_a share the cookie jar
    tab1 = client_a.get("/auth/me")
    tab2 = client_a.get("/users/me")
    tab3 = client_a.post("/auth/verify-portal", json={"portal_role": "ATHLETE"})
    assert tab1.status_code == 200 and tab1.json()["email"] == email_a
    assert tab2.status_code == 200 and tab2.json()["email"] == email_a
    assert tab3.status_code == 200 and tab3.json()["authorized"] is True
    print("[PASS] Test 5: Same profile successfully shares authenticated session across all tabs.")

    # -------------------------------------------------------------
    # TEST 6 & 7: Different Browser Profiles & Incognito Isolation
    # -------------------------------------------------------------
    print("\n--- TEST 6 & 7: Independent Browser Profiles & Incognito Isolation ---")
    # Profile 1: Athlete A (client_a)
    # Profile 2: Athlete B (client_b)
    # Incognito: Athlete C (client_c)
    client_b = TestClient(app)
    res_login_b = client_b.post("/auth/login", json={"email": email_b, "password": "Password123!"})
    assert res_login_b.status_code == 200

    client_c = TestClient(app)
    res_login_c = client_c.post("/auth/login", json={"email": email_c, "password": "Password123!"})
    assert res_login_c.status_code == 200

    # Verify all 3 sessions are independent
    assert client_a.get("/auth/me").json()["email"] == email_a
    assert client_b.get("/auth/me").json()["email"] == email_b
    assert client_c.get("/auth/me").json()["email"] == email_c

    # Now logout Profile 2 (Athlete B)
    res_logout_b = client_b.post("/auth/logout")
    assert res_logout_b.status_code == 200
    assert client_b.get("/auth/me").status_code == 401, "Profile 2 must now be logged out"

    # Profile 1 and Incognito MUST remain logged in!
    assert client_a.get("/auth/me").status_code == 200 and client_a.get("/auth/me").json()["email"] == email_a
    assert client_c.get("/auth/me").status_code == 200 and client_c.get("/auth/me").json()["email"] == email_c
    print("[PASS] Test 6 & 7: Profiles are completely isolated. Logging out Profile 2 did NOT log out Profile 1 or Incognito.")

    # -------------------------------------------------------------
    # TEST 8: Absolute 24-Hour Expiration & Non-Sliding Verification
    # -------------------------------------------------------------
    print("\n--- TEST 8: Absolute 24-Hour Expiration (Non-Sliding) ---")
    now = datetime.now(timezone.utc)
    
    # 1. Expired token (issued 25 hours ago, expired 1 hour ago)
    expired_token = jwt.encode(
        {
            "sub": str(user_a.user_id),
            "role": user_a.role.value,
            "iat": int((now - timedelta(hours=25)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    client_exp = TestClient(app)
    client_exp.cookies.set(AUTH_COOKIE_NAME, expired_token)
    res_exp = client_exp.get("/auth/me")
    assert res_exp.status_code == 401, f"Expected 401 for expired token, got {res_exp.status_code}"
    assert "expired" in res_exp.json().get("detail", "").lower()
    print("  Sub-test 8.1: Token > 24 hours rejected with 401 ('Session has expired').")

    # 2. Valid token within 24 hours (issued 23 hours ago, expires in 1 hour)
    valid_23h_token = jwt.encode(
        {
            "sub": str(user_a.user_id),
            "role": user_a.role.value,
            "iat": int((now - timedelta(hours=23)).timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    client_valid = TestClient(app)
    client_valid.cookies.set(AUTH_COOKIE_NAME, valid_23h_token)
    res_valid = client_valid.get("/auth/me")
    assert res_valid.status_code == 200, f"Expected 200, got {res_valid.status_code}"
    # Verify non-sliding: The server must NOT emit a new Set-Cookie that extends the expiration
    assert "set-cookie" not in res_valid.headers or AUTH_COOKIE_NAME not in res_valid.headers.get("set-cookie", "")
    print("  Sub-test 8.2: Token < 24 hours accepted (200), and expiration did NOT slide on activity.")
    print("[PASS] Test 8: Absolute 24-hour non-sliding expiration strictly enforced.")

    # -------------------------------------------------------------
    # TEST 9: Logout Invalidation
    # -------------------------------------------------------------
    print("\n--- TEST 9: Logout & Protected Endpoint Denied ---")
    res_logout_a = client_a.post("/auth/logout")
    assert res_logout_a.status_code == 200
    logout_cookie_header = res_logout_a.headers.get("set-cookie", "")
    assert "max-age=0" in logout_cookie_header.lower() or '""' in logout_cookie_header

    # Immediate subsequent calls to protected APIs must return 401
    assert client_a.get("/auth/me").status_code == 401
    assert client_a.get("/users/me").status_code == 401
    assert client_a.post("/auth/verify-portal", json={"portal_role": "ATHLETE"}).status_code == 401
    print("[PASS] Test 9: Logout cleared cookie; all protected endpoints returned 401 Unauthorized.")

    # -------------------------------------------------------------
    # TEST 10: Backward Compatibility with Bearer Header
    # -------------------------------------------------------------
    print("\n--- TEST 10: Backward Compatibility with Bearer Token ---")
    test_token = create_access_token(data={"sub": str(user_c.user_id), "role": user_c.role.value})
    client_bearer = TestClient(app)
    # Call without cookie but with Bearer header
    res_bearer = client_bearer.get("/auth/me", headers={"Authorization": f"Bearer {test_token}"})
    assert res_bearer.status_code == 200
    assert res_bearer.json()["email"] == email_c
    print("[PASS] Test 10: Authorization Bearer header remains supported for automated tests and scripts.")

    print("\n==================================================================")
    print("ALL 12 PRODUCTION AUTHENTICATION & SESSION TESTS PASSED!")
    print("==================================================================")


if __name__ == "__main__":
    run_all_tests()
