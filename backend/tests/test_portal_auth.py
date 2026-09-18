import sys
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("--- Starting Login & Portal Authorization Tests ---")
    
    # 1. Test registration of a new athlete
    unique_suffix = str(uuid.uuid4())[:8]
    test_email = f"athlete_{unique_suffix}@example.com"
    test_password = "SecurePassword123!"
    test_name = f"Test Athlete {unique_suffix}"
    
    print(f"\n1. Registering new athlete: {test_email}")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "name": test_name,
        "email": test_email,
        "password": test_password,
        "role": "Athlete"
    })
    print(f"Register status: {reg_res.status_code}")
    assert reg_res.status_code == 201, f"Expected 201, got {reg_res.text}"
    user_data = reg_res.json()
    assert user_data["role"] == "Athlete", f"Expected role Athlete, got {user_data['role']}"
    print("[PASS] CASE 1 Passed: New user registered as Athlete.")

    # 2. Authenticate
    print(f"\n2. Authenticating as {test_email}")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    print(f"Login status: {login_res.status_code}")
    assert login_res.status_code == 200, f"Expected 200, got {login_res.text}"
    tokens = login_res.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("[PASS] Login succeeded and token received.")

    # 3. Verify portal ATHLETE
    print("\n3. Testing Portal: ATHLETE")
    v_res = requests.post(f"{BASE_URL}/auth/verify-portal", json={"portal_role": "ATHLETE"}, headers=headers)
    assert v_res.status_code == 200
    v_data = v_res.json()
    print("ATHLETE Portal result:", v_data)
    assert v_data["authorized"] is True
    assert v_data["default_route"] == "/dashboard"
    print("[PASS] CASE 1 Verified: Athlete portal authorized with /dashboard.")

    # 4. Verify portal COACH for normal athlete (CASE 2 & CASE 8)
    print("\n4. Testing Portal: COACH (by normal athlete)")
    v_res = requests.post(f"{BASE_URL}/auth/verify-portal", json={"portal_role": "COACH"}, headers=headers)
    assert v_res.status_code == 200
    v_data = v_res.json()
    print("COACH Portal result:", v_data)
    assert v_data["authorized"] is False
    assert "This account does not currently have active Coach access." in v_data["message"]
    assert "Professional roles require approval from an administrator." in v_data["secondary_message"]
    assert v_data["can_continue_as_athlete"] is True
    assert v_data["request_role_url"] == "/request-professional-role/coach"
    print("[PASS] CASE 2 Passed: Athlete selecting Coach is denied access with friendly error, Continue as Athlete, and Request Coach Role link.")

    # 5. Verify portal PHYSIOTHERAPIST (CASE 4 rejection)
    print("\n5. Testing Portal: PHYSIOTHERAPIST (by normal athlete)")
    v_res = requests.post(f"{BASE_URL}/auth/verify-portal", json={"portal_role": "PHYSIOTHERAPIST"}, headers=headers)
    assert v_res.status_code == 200
    v_data = v_res.json()
    print("PHYSIO Portal result:", v_data)
    assert v_data["authorized"] is False
    assert "Physiotherapist access is not active for this account." in v_data["message"]
    assert "Professional roles require approval from an administrator." in v_data["secondary_message"]
    assert v_data["can_continue_as_athlete"] is True
    assert v_data["request_role_url"] == "/request-professional-role/physiotherapist"
    print("[PASS] CASE 4 Rejection Passed: Physiotherapist access denied with specified message & actions.")

    # 6. Verify portal SPORTS_SCIENTIST (CASE 5 rejection)
    print("\n6. Testing Portal: SPORTS_SCIENTIST (by normal athlete)")
    v_res = requests.post(f"{BASE_URL}/auth/verify-portal", json={"portal_role": "SPORTS_SCIENTIST"}, headers=headers)
    assert v_res.status_code == 200
    v_data = v_res.json()
    print("SPORTS_SCIENTIST Portal result:", v_data)
    assert v_data["authorized"] is False
    assert "Sports Scientist access is not active for this account." in v_data["message"]
    assert "Professional roles require approval from an administrator." in v_data["secondary_message"]
    assert v_data["can_continue_as_athlete"] is True
    assert v_data["request_role_url"] == "/request-professional-role/sports-scientist"
    print("[PASS] CASE 5 Rejection Passed: Sports Scientist access denied with specified message & actions.")

    # 7. Verify portal ADMINISTRATOR (CASE 7: normal user denied admin)
    print("\n7. Testing Portal: ADMINISTRATOR (by normal athlete)")
    v_res = requests.post(f"{BASE_URL}/auth/verify-portal", json={"portal_role": "ADMINISTRATOR"}, headers=headers)
    assert v_res.status_code == 200
    v_data = v_res.json()
    print("ADMINISTRATOR Portal result:", v_data)
    assert v_data["authorized"] is False
    assert "Administrator access is not available for this account." in v_data["message"]
    assert v_data["secondary_message"] is None  # no sensitive info leak
    assert v_data["can_continue_as_athlete"] is True
    assert v_data["request_role_url"] is None   # cannot request admin
    print("[PASS] CASE 7 Passed: Normal user denied Admin without disclosing sensitive details.")

    # 8. Test direct dashboard route access via API without permission (CASE 10)
    print("\n8. Testing direct API access to /coach/dashboard as Athlete (CASE 10)")
    coach_api_res = requests.get(f"{BASE_URL}/coach/dashboard", headers=headers)
    print(f"Direct /coach/dashboard status: {coach_api_res.status_code}")
    assert coach_api_res.status_code == 403, f"Expected 403, got {coach_api_res.status_code}"
    print("[PASS] CASE 10 Passed: Backend directly blocks unauthorized role endpoints (403 Forbidden).")

    print("\n--- ALL BACKEND PORTAL AUTHORIZATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_tests()
