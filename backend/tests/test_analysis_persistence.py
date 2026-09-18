import uuid

from app.models.analysis_result import AnalysisResult


def test_analysis_result_stores_historical_snapshot_fields():
    analysis = AnalysisResult(
        analysis_id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        athlete_id=uuid.uuid4(),
        status="completed",
        progress=100,
        stage="Feature extraction complete",
        algorithm_version="1.0-phase1-filtered",
        historical_score=35.0,
        biomechanical_score=42.0,
        asymmetry_score=18.0,
        training_load_score=12.0,
        composite_risk_score=31.5,
        risk_category="Moderate Risk",
    )

    assert analysis.historical_score == 35.0
    assert analysis.composite_risk_score == 31.5
    assert analysis.risk_category == "Moderate Risk"
