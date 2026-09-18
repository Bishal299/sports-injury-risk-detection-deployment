import csv

from app.services.reports.csv_generator import FRAME_LEVEL_COLUMNS, generate_csv_report
from app.services.reports.ml_dataset import ML_DATASET_COLUMNS, export_ml_dataset


def _sample_biomechanics_payload():
    joint_data = {
        "timeline": [0.0, 0.033, 0.066],
        "summary": {
            "right_knee": {"avg_angle": 168.0, "min_angle": 160.0, "max_angle": 176.0, "rom": 16.0},
            "left_knee": {"avg_angle": 170.0, "min_angle": 162.0, "max_angle": 178.0, "rom": 16.0},
        },
        "time_series": {
            "right_knee": [170.0, 168.0, 166.0],
            "left_knee": [172.0, 170.0, 168.0],
            "right_hip": [160.0, 158.0, 156.0],
            "left_hip": [161.0, 159.0, 157.0],
            "right_ankle": [90.0, 91.0, 92.0],
            "left_ankle": [89.0, 90.0, 91.0],
        },
    }
    valgus_data = {
        "right": {"avg_normalized_valgus": 0.04, "peak_normalized_valgus": 0.06},
        "left": {"avg_normalized_valgus": 0.03, "peak_normalized_valgus": 0.05},
        "time_series": {"right": [0.03, 0.04, 0.05], "left": [0.02, 0.03, 0.04]},
    }
    hip_data = {
        "score": 88.0,
        "mean_pelvic_tilt_deg": 4.0,
        "max_pelvic_tilt_deg": 6.0,
        "time_series": {"pelvic_tilt": [3.0, 4.0, 5.0], "normalized_midpoint_y": [0.5, 0.51, 0.52]},
    }
    trunk_data = {
        "score": 91.0,
        "avg_trunk_lean_deg": 8.0,
        "max_trunk_lean_deg": 10.0,
        "time_series": {"lean": [7.0, 8.0, 9.0], "lateral_lean": [1.0, -1.0, 0.5]},
    }
    balance_data = {
        "score": 84.0,
        "avg_base_of_support": 0.27,
        "time_series": {"com_x": [0.1, 0.11, 0.12], "com_y": [0.7, 0.71, 0.72], "bos_width": [0.25, 0.27, 0.29]},
    }
    stride_data = {
        "normalized_stride_length": 1.2,
        "stride_asymmetry_pct": 3.5,
        "time_series": {"stride_separation": [1.1, 1.2, 1.3]},
    }
    landing_data = {
        "score": 79.0,
        "knee_flexion_deg": 22.0,
        "hip_flexion_deg": 24.0,
        "landing_window": {"start_frame": 1, "end_frame": 2},
    }
    force_data = {
        "avg_force_n": 1400.0,
        "peak_force_n": 1650.0,
        "peak_force_bw": 2.1,
        "time_series_force": [1300.0, 1450.0, 1500.0],
        "time_series_force_bw": [1.7, 1.9, 2.0],
    }
    frames_landmarks = [
        {"frame_number": 0, "validity": {"pose_valid": True, "left_leg_valid": True, "right_leg_valid": True, "trunk_valid": True}},
        {"frame_number": 1, "validity": {"pose_valid": True, "left_leg_valid": True, "right_leg_valid": True, "trunk_valid": True}},
        {"frame_number": 2, "validity": {"pose_valid": False, "left_leg_valid": False, "right_leg_valid": True, "trunk_valid": True}},
    ]
    metadata = {
        "video_id": 101,
        "athlete_id": 202,
        "sport": "Basketball",
        "activity": "Jump Landing Assessment",
        "height_cm": 188.5,
        "weight_kg": 82.5,
        "fps": 30.0,
    }
    feature_quality = {"total_frames": 3, "valid_pose_frames": 2, "fps": 30.0}
    return {
        "joint_data": joint_data,
        "valgus_data": valgus_data,
        "hip_data": hip_data,
        "trunk_data": trunk_data,
        "balance_data": balance_data,
        "stride_data": stride_data,
        "landing_data": landing_data,
        "force_data": force_data,
        "frames_landmarks": frames_landmarks,
        "metadata": metadata,
        "feature_quality": feature_quality,
    }


def test_biomechanics_csv_generation_uses_dynamic_metadata(tmp_path):
    payload = _sample_biomechanics_payload()
    csv_path = tmp_path / "video_101_timeseries.csv"

    generate_csv_report(
        output_csv_path=str(csv_path),
        joint_data=payload["joint_data"],
        valgus_data=payload["valgus_data"],
        hip_data=payload["hip_data"],
        trunk_data=payload["trunk_data"],
        balance_data=payload["balance_data"],
        stride_data=payload["stride_data"],
        landing_data=payload["landing_data"],
        force_data=payload["force_data"],
        frames_landmarks=payload["frames_landmarks"],
        metadata=payload["metadata"],
    )

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == FRAME_LEVEL_COLUMNS
    assert len(rows) == 3
    assert rows[0]["video_id"] == "101"
    assert rows[0]["athlete_id"] == "202"
    assert rows[0]["sport"] == "Basketball"
    assert rows[0]["height_cm"] == "188.5"
    assert rows[0]["weight_kg"] == "82.5"
    assert rows[0]["pose_valid"] == "TRUE"
    assert rows[2]["pose_valid"] == "FALSE"
    assert rows[1]["movement_phase"] == "landing"


def test_ml_dataset_export_is_single_row_and_deduplicates_master(tmp_path):
    payload = _sample_biomechanics_payload()
    output_csv = tmp_path / "video_101_ml.csv"
    master_csv = tmp_path / "ml_dataset.csv"

    for _ in range(2):
        export_ml_dataset(
            output_ml_csv_path=str(output_csv),
            joint_data=payload["joint_data"],
            valgus_data=payload["valgus_data"],
            hip_data=payload["hip_data"],
            trunk_data=payload["trunk_data"],
            balance_data=payload["balance_data"],
            stride_data=payload["stride_data"],
            landing_data=payload["landing_data"],
            force_data=payload["force_data"],
            metadata=payload["metadata"],
            feature_quality=payload["feature_quality"],
            master_ml_csv_path=str(master_csv),
        )

    with output_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == ML_DATASET_COLUMNS
    assert len(rows) == 1
    assert rows[0]["video_id"] == "101"
    assert rows[0]["height_cm"] == "188.5"
    assert rows[0]["weight_kg"] == "82.5"
    assert rows[0]["valid_frame_ratio"] == "0.667"

    with master_csv.open(newline="", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))

    assert [row["video_id"] for row in master_rows].count("101") == 1
