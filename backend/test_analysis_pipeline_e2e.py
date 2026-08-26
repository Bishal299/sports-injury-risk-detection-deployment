import sys
import os
import requests
from uuid import UUID

BASE_URL = "http://127.0.0.1:8000"


def run_e2e_tests():
    print("==================================================")
    print("   AI MOVEMENT ANALYSIS PIPELINE - E2E TEST SUITE  ")
    print("==================================================")

    # 1. Health check
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Root failed: {r.status_code}"
    print("[OK] Backend root API is healthy.")

    # 2. Authenticate / Login or Register test athlete
    login_payload = {
        "email": "athlete_test_pipeline@example.com",
        "password": "Password123!"
    }

    login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if login_resp.status_code != 200:
        print("Registering test athlete...")
        reg_payload = {
            "name": "Alex Morgan",
            "email": "athlete_test_pipeline@example.com",
            "password": "Password123!",
            "role": "Athlete"
        }
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        assert reg_resp.status_code in [200, 201], f"Registration failed: {reg_resp.text}"
        login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        assert login_resp.status_code == 200, f"Login after register failed: {login_resp.text}"

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Authenticated successfully with JWT Bearer token.")

    # 3. Check or Create Athlete Profile
    prof_resp = requests.get(f"{BASE_URL}/athletes/profile", headers=headers)
    if prof_resp.status_code != 200:
        print("Creating athlete profile...")
        create_prof = requests.post(
            f"{BASE_URL}/athletes/profile",
            headers=headers,
            json={
                "sport": "Soccer",
                "position": "Forward",
                "age": 24,
                "height": 175.0,
                "weight": 68.0
            }
        )
        assert create_prof.status_code in [200, 201], f"Create profile failed: {create_prof.text}"
    print("[OK] Athlete profile verified.")

    # 4. Get Athlete's Videos
    videos_resp = requests.get(f"{BASE_URL}/videos", headers=headers)
    assert videos_resp.status_code == 200, f"Fetch videos failed: {videos_resp.text}"
    videos = videos_resp.json()

    if not videos:
        # Upload a video
        print("Uploading sample video for testing...")
        sample_path = "uploads/videos/5b9e8da3-bc62-4774-b9da-6a613036e181.mp4"
        with open(sample_path, "rb") as f:
            up_resp = requests.post(
                f"{BASE_URL}/videos/upload",
                headers=headers,
                files={"file": ("test_squat.mp4", f, "video/mp4")},
                data={"activity": "Squat Jump Analysis"}
            )
        assert up_resp.status_code == 201, f"Video upload failed: {up_resp.text}"
        video = up_resp.json()
    else:
        video = videos[0]

    video_id = video["video_id"]
    print(f"[OK] Target Video ID: {video_id} ({video.get('activity')})")

    # 5. Trigger Analysis (POST /analysis/{video_id})
    print("Triggering movement analysis pipeline...")
    trigger_resp = requests.post(f"{BASE_URL}/analysis/{video_id}", headers=headers)
    assert trigger_resp.status_code in [200, 202], f"Trigger analysis failed: {trigger_resp.text}"
    print("[OK] Analysis triggered (HTTP 202 Accepted).")

    # 6. Check Analysis Status (GET /analysis/{video_id}/status)
    status_resp = requests.get(f"{BASE_URL}/analysis/{video_id}/status", headers=headers)
    assert status_resp.status_code == 200, f"Status fetch failed: {status_resp.text}"
    stat_json = status_resp.json()
    print(f"[OK] Status endpoint: status='{stat_json['status']}', stage='{stat_json['stage']}', progress={stat_json['progress']}%")

    # Run direct pipeline if background worker hasn't finished yet in local sync
    from app.services.movement.pipeline import run_movement_analysis_pipeline
    run_movement_analysis_pipeline(UUID(video_id))

    # 7. Verify Completed Analysis Results (GET /analysis/{video_id})
    res_resp = requests.get(f"{BASE_URL}/analysis/{video_id}", headers=headers)
    assert res_resp.status_code == 200, f"Analysis result fetch failed: {res_resp.text}"
    result = res_resp.json()
    assert result["status"] == "completed", f"Expected status completed, got {result['status']}"
    assert result["movement_quality"] is not None, "movement_quality is missing"
    assert result["risk_level"] in ["Low Risk", "Moderate Risk", "Elevated Risk", "High Risk"], f"Invalid risk level: {result['risk_level']}"
    assert result["summary_metrics"] is not None, "summary_metrics is missing"
    assert result["time_series_data"] is not None, "time_series_data is missing"
    assert len(result["recommendations"]) > 0, "recommendations are empty"

    print("[OK] Analysis Result retrieved successfully:")
    print(f"   - Movement Quality Score: {result['movement_quality']}/100")
    print(f"   - Injury Risk Score: {result['overall_risk_score']}/100 ({result['risk_level']})")
    print(f"   - Knee Valgus Max: {result['knee_valgus']} deg")
    print(f"   - Hip Stability: {result['hip_stability']}/100")
    print(f"   - Trunk Lean: {result['trunk_lean']} deg")
    print(f"   - Symmetry Score: {result['symmetry_score']}%")
    print(f"   - Skeleton Video: {result['skeleton_video_url']}")

    # 8. Verify CSV Report Download (GET /analysis/{video_id}/csv)
    csv_resp = requests.get(f"{BASE_URL}/analysis/{video_id}/csv", headers=headers)
    assert csv_resp.status_code == 200, f"CSV download failed: {csv_resp.status_code}"
    assert "text/csv" in csv_resp.headers.get("content-type", ""), "Wrong content type for CSV"
    assert len(csv_resp.content) > 500, f"CSV file suspiciously small ({len(csv_resp.content)} bytes)"
    print(f"[OK] CSV Report downloaded successfully ({len(csv_resp.content)} bytes).")

    # 9. Verify PDF Report Download (GET /analysis/{video_id}/pdf)
    pdf_resp = requests.get(f"{BASE_URL}/analysis/{video_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200, f"PDF download failed: {pdf_resp.status_code}"
    assert "application/pdf" in pdf_resp.headers.get("content-type", ""), "Wrong content type for PDF"
    assert len(pdf_resp.content) > 1000, f"PDF file suspiciously small ({len(pdf_resp.content)} bytes)"
    print(f"[OK] PDF Report downloaded successfully ({len(pdf_resp.content)} bytes).")

    # 10. Verify Static Skeleton Video stream
    skel_url = result["skeleton_video_url"]
    skel_resp = requests.get(skel_url)
    assert skel_resp.status_code == 200, f"Static skeleton video stream failed: {skel_resp.status_code}"
    assert len(skel_resp.content) > 10000, "Skeleton video empty or corrupt"
    print(f"[OK] Static Skeleton Video accessible at {skel_url} ({len(skel_resp.content) / (1024*1024):.2f} MB).")

    # 11. Verify Authorization Isolation (unauthorized request)
    unauth_resp = requests.get(f"{BASE_URL}/analysis/{video_id}") # no token
    assert unauth_resp.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {unauth_resp.status_code}"
    print("[OK] Authorization security enforced (unauthenticated access blocked).")

    print("\n==================================================")
    print("   ALL 11 END-TO-END TESTS PASSED SUCCESSFULLY!    ")
    print("==================================================")


if __name__ == "__main__":
    run_e2e_tests()

