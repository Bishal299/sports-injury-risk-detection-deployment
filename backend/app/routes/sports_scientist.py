from collections import Counter, defaultdict
from datetime import date, datetime, time, timezone
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_roles
from app.dependencies.professional_access import get_verified_professional_profile
from app.models.analysis_result import AnalysisResult
from app.models.athlete import Athlete
from app.models.injury_history import InjuryHistory
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipRole,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import ProfessionalProfile, ProfessionalProfileRole
from app.models.user import User, UserRole
from app.models.notification import NotificationType
from app.schemas.professional_profile import ProfessionalProfileResponse, ProfessionalProfileUpdate
from app.schemas.sports_scientist import (
    SportsScientistAthleteOption,
    SportsScientistAthleteComparisonResponse,
    SportsScientistConnectedAthlete,
    SportsScientistDiscoveryAthlete,
    SportsScientistAnalysisDetail,
    SportsScientistBiomechanicalAnalyticsResponse,
    SportsScientistComparisonAnalysisOption,
    SportsScientistComparisonAthlete,
    SportsScientistComparisonMetricRow,
    SportsScientistComparisonMetricValue,
    SportsScientistComparisonObservation,
    SportsScientistDashboardResponse,
    SportsScientistFinding,
    SportsScientistInjuryInsightsResponse,
    SportsScientistObservedPattern,
    SportsScientistRiskFactorInsight,
    SportsScientistRiskGroupAverage,
    SportsScientistResearchReportHistoryItem,
    SportsScientistResearchReportResponse,
    SportsScientistRelationshipResponse,
    SportsScientistMetricDetail,
    SportsScientistMetricSummary,
    SportsScientistRecentAnalysis,
    SportsScientistRiskBand,
    SportsScientistRiskTrendPoint,
    SportsScientistAthleteRiskRow,
    SportsScientistTrendPoint,
)
from app.services.professional_analysis import (
    get_analysis_score,
    get_existing_analysis_report_path,
    normalize_risk_category_label,
)
from app.services.professional_athlete_relationships import create_request
from app.services.notifications import create_notification
from app.services.risk_config import BIOMECHANICAL_SUBMETRIC_WEIGHTS, DISPLAY_WEIGHTS
from app.services.reports.pdf_generator import generate_research_report_pdf


router = APIRouter(prefix="/sports-scientist", tags=["Sports Scientist"])

SCIENTIST_ROLE = ProfessionalAthleteRelationshipRole.SPORTS_SCIENTIST.value
RISK_BANDS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
HIGH_RISK_BANDS = {"HIGH", "CRITICAL"}
MIN_GROUP_ANALYSES = 2

INJURY_FACTOR_DEFINITIONS = [
    {"key": "knee_valgus", "label": "Knee/Valgus", "keywords": ["knee", "valgus"]},
    {"key": "hip", "label": "Hip", "keywords": ["hip", "pelvic"]},
    {"key": "trunk", "label": "Trunk", "keywords": ["trunk"]},
    {"key": "landing", "label": "Landing", "keywords": ["landing"]},
    {"key": "balance", "label": "Balance", "keywords": ["balance", "sway"]},
    {"key": "alignment", "label": "Alignment", "keywords": ["alignment"]},
    {"key": "posture", "label": "Posture", "keywords": ["posture"]},
    {"key": "movement_asymmetry", "label": "Movement Asymmetry", "keywords": ["asymmetry", "symmetry"]},
    {"key": "previous_injury_history", "label": "Previous Injury History", "keywords": ["prior", "previous", "history", "orthopedic"]},
    {"key": "training_load", "label": "Training Load", "keywords": ["training load", "load"]},
]

COMPARISON_METRICS = [
    {"key": "overall_risk", "label": "Overall Risk"},
    {"key": "movement_quality", "label": "Movement Quality"},
    {"key": "biomechanical_efficiency", "label": "Biomechanical Efficiency"},
    {"key": "symmetry", "label": "Symmetry"},
    {"key": "knee_risk", "label": "Knee Risk"},
    {"key": "hip_risk", "label": "Hip Risk"},
    {"key": "trunk_risk", "label": "Trunk Risk"},
    {"key": "landing_risk", "label": "Landing Risk"},
    {"key": "balance_risk", "label": "Balance Risk"},
    {"key": "alignment_risk", "label": "Alignment Risk"},
    {"key": "posture_risk", "label": "Posture Risk"},
    {"key": "training_load", "label": "Training Load"},
]


def get_verified_sports_scientist_profile(
    current_user: User = Depends(require_roles(UserRole.SPORTS_SCIENTIST)),
    db: Session = Depends(get_db),
) -> ProfessionalProfile:
    return get_verified_professional_profile(
        db=db,
        current_user=current_user,
        professional_role=ProfessionalProfileRole.SPORTS_SCIENTIST.value,
    )


def active_relationships(db: Session, profile: ProfessionalProfile):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user))
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.professional_role == SCIENTIST_ROLE,
            ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
        )
        .all()
    )


def latest_completed_analysis(db: Session, athlete_id):
    return (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(
            AnalysisResult.athlete_id == athlete_id,
            AnalysisResult.status == "completed",
        )
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .first()
    )


def analysis_count_for_athlete(db: Session, athlete_id):
    return (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.athlete_id == athlete_id,
            AnalysisResult.status == "completed",
        )
        .count()
    )


def relationship_for_scientist(db: Session, profile: ProfessionalProfile, relationship_id: UUID):
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.requester),
        )
        .filter(
            ProfessionalAthleteRelationship.relationship_id == relationship_id,
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.professional_role == SCIENTIST_ROLE,
        )
        .first()
    )

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sports Scientist relationship not found",
        )

    return relationship


def scientist_athlete_item(db: Session, relationship: ProfessionalAthleteRelationship):
    athlete = relationship.athlete
    latest = latest_completed_analysis(db, athlete.athlete_id)
    latest_score = get_analysis_score(latest)

    return SportsScientistConnectedAthlete(
        relationship_id=relationship.relationship_id,
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        position=athlete.position,
        analysis_count=analysis_count_for_athlete(db, athlete.athlete_id),
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest.risk_category if latest else None,
            latest_score,
        ),
        connection_status=relationship.status,
        last_analysis_at=event_date(latest) if latest else None,
    )


def scientist_discovery_item(db: Session, athlete: Athlete, relationship: ProfessionalAthleteRelationship | None):
    latest = latest_completed_analysis(db, athlete.athlete_id)
    latest_score = get_analysis_score(latest)

    return SportsScientistDiscoveryAthlete(
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        position=athlete.position,
        age=athlete.age,
        connection_status=relationship.status if relationship else "NONE",
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest.risk_category if latest else None,
            latest_score,
        ),
        analysis_count=analysis_count_for_athlete(db, athlete.athlete_id),
        latest_activity_at=event_date(latest) if latest else None,
    )


def completed_analyses_for_athletes(db: Session, athlete_ids: list):
    if not athlete_ids:
        return []

    return (
        db.query(AnalysisResult)
        .options(
            joinedload(AnalysisResult.athlete).joinedload(Athlete.user),
            joinedload(AnalysisResult.video),
        )
        .filter(
            AnalysisResult.athlete_id.in_(athlete_ids),
            AnalysisResult.status == "completed",
        )
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .all()
    )


def injury_history_for_athletes(db: Session, athlete_ids: list):
    if not athlete_ids:
        return []
    return (
        db.query(InjuryHistory)
        .filter(InjuryHistory.athlete_id.in_(athlete_ids))
        .order_by(InjuryHistory.injury_date.desc())
        .all()
    )


def event_date(analysis: AnalysisResult):
    return analysis.completed_at or analysis.analysis_date or analysis.created_at


def metric_from_summary(analysis: AnalysisResult, path: list[str]):
    value = analysis.summary_metrics
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_numeric_value(analysis: AnalysisResult, paths: list[list[str]]):
    for path in paths:
        value = metric_from_summary(analysis, path)
        if value is not None:
            return value
    return None


def biomechanical_metric_values(analysis: AnalysisResult):
    return {
        "knee_valgus": analysis.knee_valgus,
        "hip_stability": analysis.hip_stability,
        "trunk_lean": analysis.trunk_lean,
        "landing_mechanics": metric_from_summary(analysis, ["landing", "score"]),
        "balance": metric_from_summary(analysis, ["balance", "score"]),
        "alignment": analysis.joint_alignment or metric_from_summary(analysis, ["alignment", "score"]),
        "posture": metric_from_summary(analysis, ["posture", "score"]),
        "movement_symmetry": analysis.symmetry_score,
        "movement_quality": analysis.movement_quality,
        "biomechanical_efficiency": (
            metric_from_summary(analysis, ["risk_assessment", "biomechanical_efficiency_score"])
            or analysis.biomechanical_score
        ),
    }


def risk_factors(analysis: AnalysisResult):
    summary = analysis.summary_metrics if isinstance(analysis.summary_metrics, dict) else {}
    assessment = summary.get("risk_assessment") if isinstance(summary.get("risk_assessment"), dict) else {}
    factors = assessment.get("risk_factors") if isinstance(assessment, dict) else []
    return factors if isinstance(factors, list) else []


def risk_assessment(analysis: AnalysisResult):
    summary = analysis.summary_metrics if isinstance(analysis.summary_metrics, dict) else {}
    assessment = summary.get("risk_assessment")
    return assessment if isinstance(assessment, dict) else {}


def first_matching_risk_factor(analysis: AnalysisResult, keywords: list[str]):
    for factor in risk_factors(analysis):
        if not isinstance(factor, dict):
            continue
        text = " ".join(str(factor.get(key, "")) for key in ("factor", "category", "title", "observed_value")).lower()
        if any(keyword in text for keyword in keywords):
            return factor
    return None


def risk_factor_numeric_value(analysis: AnalysisResult, factor_definition: dict):
    factor = first_matching_risk_factor(analysis, factor_definition["keywords"])
    if factor:
        try:
            return round(float(factor.get("risk_contribution")), 2)
        except (TypeError, ValueError):
            return None

    assessment = risk_assessment(analysis)
    scores = assessment.get("component_scores") if isinstance(assessment.get("component_scores"), dict) else {}
    component_key = {
        "movement_asymmetry": "movement_asymmetry",
        "previous_injury_history": "historical_injury_factors",
        "training_load": "training_load",
    }.get(factor_definition["key"])
    if component_key and scores.get(component_key) is not None:
        try:
            return round(float(scores.get(component_key)), 2)
        except (TypeError, ValueError):
            return None

    return None


def factor_matches_analysis(analysis: AnalysisResult, factor_definition: dict):
    value = risk_factor_numeric_value(analysis, factor_definition)
    return value is not None and value > 0


def label_for_factor_key(key: str | None):
    for definition in INJURY_FACTOR_DEFINITIONS:
        if definition["key"] == key:
            return definition["label"]
    return None


def date_bucket(value):
    current = value
    if isinstance(current, datetime):
        return current.date().isoformat()
    if isinstance(current, date):
        return current.isoformat()
    return None


def average_numeric(values):
    numeric = []
    for value in values:
        if value is None:
            continue
        try:
            numeric.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numeric:
        return None
    return round(sum(numeric) / len(numeric), 1)


def latest_analysis_by_athlete(analyses: list[AnalysisResult]):
    latest = {}
    for analysis in analyses:
        current = latest.get(analysis.athlete_id)
        if current is None or (event_date(analysis) or datetime.min) >= (event_date(current) or datetime.min):
            latest[analysis.athlete_id] = analysis
    return latest


def filtered_completed_analyses(
    analyses: list[AnalysisResult],
    athlete_id: UUID | None = None,
    sport: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    risk_level: str | None = None,
    injury_factor: str | None = None,
):
    factor_definition = next((item for item in INJURY_FACTOR_DEFINITIONS if item["key"] == injury_factor), None)
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    normalized_risk = risk_level.upper() if risk_level else None
    rows = []

    for analysis in analyses:
        analysis_date = event_date(analysis)
        score = get_analysis_score(analysis)
        category = normalize_risk_category_label(analysis.risk_category, score)
        if athlete_id and analysis.athlete_id != athlete_id:
            continue
        if sport and (not analysis.athlete or analysis.athlete.sport != sport):
            continue
        if start_dt and (not analysis_date or analysis_date < start_dt):
            continue
        if end_dt and (not analysis_date or analysis_date > end_dt):
            continue
        if normalized_risk and category != normalized_risk:
            continue
        if factor_definition and not factor_matches_analysis(analysis, factor_definition):
            continue
        rows.append(analysis)

    return rows


def filtered_comparison_analyses(
    analyses: list[AnalysisResult],
    sport: str | None = None,
    position: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    rows = []
    for analysis in analyses:
        analysis_date = event_date(analysis)
        athlete = analysis.athlete
        if sport and (not athlete or athlete.sport != sport):
            continue
        if position and (not athlete or athlete.position != position):
            continue
        if start_dt and (not analysis_date or analysis_date < start_dt):
            continue
        if end_dt and (not analysis_date or analysis_date > end_dt):
            continue
        rows.append(analysis)
    return rows


def comparison_metric_value(analysis: AnalysisResult, metric_key: str):
    factor_by_key = {
        "knee_risk": INJURY_FACTOR_DEFINITIONS[0],
        "hip_risk": INJURY_FACTOR_DEFINITIONS[1],
        "trunk_risk": INJURY_FACTOR_DEFINITIONS[2],
        "landing_risk": INJURY_FACTOR_DEFINITIONS[3],
        "balance_risk": INJURY_FACTOR_DEFINITIONS[4],
        "alignment_risk": INJURY_FACTOR_DEFINITIONS[5],
        "posture_risk": INJURY_FACTOR_DEFINITIONS[6],
        "training_load": INJURY_FACTOR_DEFINITIONS[9],
    }
    if metric_key == "overall_risk":
        return get_analysis_score(analysis)
    if metric_key == "movement_quality":
        return analysis.movement_quality
    if metric_key == "biomechanical_efficiency":
        return biomechanical_efficiency_payload(analysis).get("final")
    if metric_key == "symmetry":
        return symmetry_payload(analysis).get("overall_symmetry")
    if metric_key in factor_by_key:
        return risk_factor_numeric_value(analysis, factor_by_key[metric_key])
    return None


def comparison_analysis_option(analysis: AnalysisResult):
    score = get_analysis_score(analysis)
    label_parts = []
    if analysis.video and analysis.video.activity:
        label_parts.append(analysis.video.activity)
    label_parts.append((event_date(analysis).date().isoformat() if event_date(analysis) else "Undated analysis"))
    return SportsScientistComparisonAnalysisOption(
        analysis_id=analysis.analysis_id,
        athlete_id=analysis.athlete_id,
        label=" · ".join(label_parts),
        analysis_date=event_date(analysis),
        risk_category=normalize_risk_category_label(analysis.risk_category, score),
        risk_score=round(float(score), 1) if score is not None else None,
    )


def comparison_athlete_option(athlete: Athlete, analyses: list[AnalysisResult]):
    athlete_analyses = [
        analysis for analysis in analyses
        if analysis.athlete_id == athlete.athlete_id
    ]
    return SportsScientistComparisonAthlete(
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        position=athlete.position,
        analyses=[comparison_analysis_option(analysis) for analysis in athlete_analyses],
    )


def selected_analysis_for_athlete(
    athlete_id: UUID,
    analyses: list[AnalysisResult],
    selected_analysis_ids: set[UUID],
):
    athlete_analyses = [analysis for analysis in analyses if analysis.athlete_id == athlete_id]
    if not athlete_analyses:
        return None
    explicit = [
        analysis for analysis in athlete_analyses
        if analysis.analysis_id in selected_analysis_ids
    ]
    if explicit:
        return explicit[0]
    return sorted(athlete_analyses, key=lambda item: event_date(item) or datetime.min, reverse=True)[0]


def comparison_metric_rows(selected_athletes: list[Athlete], analyses: list[AnalysisResult], analysis_ids: set[UUID]):
    rows = []
    selected_by_athlete = {
        athlete.athlete_id: selected_analysis_for_athlete(athlete.athlete_id, analyses, analysis_ids)
        for athlete in selected_athletes
    }
    for metric in COMPARISON_METRICS:
        values = []
        for athlete in selected_athletes:
            analysis = selected_by_athlete.get(athlete.athlete_id)
            value = comparison_metric_value(analysis, metric["key"]) if analysis else None
            values.append(
                SportsScientistComparisonMetricValue(
                    athlete_id=athlete.athlete_id,
                    athlete_name=athlete.user.name if athlete.user else "Athlete",
                    analysis_id=analysis.analysis_id if analysis else None,
                    value=round(float(value), 1) if value is not None else None,
                    analysis_date=event_date(analysis) if analysis else None,
                )
            )
        rows.append(SportsScientistComparisonMetricRow(key=metric["key"], label=metric["label"], values=values))
    return rows


def comparison_history(analyses: list[AnalysisResult], athlete_ids: set[UUID]):
    grouped = defaultdict(list)
    for analysis in analyses:
        if analysis.athlete_id not in athlete_ids:
            continue
        key = date_bucket(event_date(analysis))
        score = get_analysis_score(analysis)
        if key and score is not None:
            grouped[key].append(score)
    return [
        SportsScientistRiskTrendPoint(
            date=key,
            average_risk_score=average_numeric(values),
            analyses=len(values),
        )
        for key, values in sorted(grouped.items())
    ]


def comparison_observations(selected_athletes: list[Athlete], analyses: list[AnalysisResult], analysis_ids: set[UUID]):
    observations = []
    rows = comparison_metric_rows(selected_athletes, analyses, analysis_ids)
    for metric_key in ("movement_quality", "symmetry", "overall_risk", "biomechanical_efficiency"):
        row = next((item for item in rows if item.key == metric_key), None)
        numeric_values = [value.value for value in row.values if value.value is not None] if row else []
        if len(numeric_values) >= 2:
            spread = max(numeric_values) - min(numeric_values)
            if spread >= 10:
                observations.append(
                    SportsScientistComparisonObservation(
                        title=f"{row.label} difference observed",
                        description=f"Selected analyses differ by {round(spread, 1)} points for {row.label.lower()}.",
                        metric=row.label,
                        supporting_analyses=len(numeric_values),
                    )
                )

    selected_ids = {athlete.athlete_id for athlete in selected_athletes}
    factor_counts = Counter()
    for analysis in analyses:
        if analysis.athlete_id not in selected_ids:
            continue
        for label in main_factor_labels(analysis, limit=len(INJURY_FACTOR_DEFINITIONS)):
            factor_counts[label] += 1
    for label, count in factor_counts.most_common(3):
        if count >= 2:
            observations.append(
                SportsScientistComparisonObservation(
                    title=f"Recurring {label.lower()} risk factor",
                    description=f"{label} appears in {count} selected-athlete completed analyses.",
                    metric=label,
                    supporting_analyses=count,
                )
            )

    for athlete in selected_athletes:
        athlete_analyses = sorted(
            [analysis for analysis in analyses if analysis.athlete_id == athlete.athlete_id],
            key=lambda item: event_date(item) or datetime.min,
        )
        if len(athlete_analyses) < 2:
            continue
        first = athlete_analyses[0]
        latest = athlete_analyses[-1]
        for metric_key, label in (("movement_quality", "Movement Quality"), ("symmetry", "Symmetry"), ("overall_risk", "Overall Risk")):
            first_value = comparison_metric_value(first, metric_key)
            latest_value = comparison_metric_value(latest, metric_key)
            if first_value is None or latest_value is None:
                continue
            change = round(float(latest_value) - float(first_value), 1)
            if abs(change) >= 10:
                direction = "increased" if change > 0 else "decreased"
                observations.append(
                    SportsScientistComparisonObservation(
                        title=f"{label} changed over time",
                        description=(
                            f"{athlete.user.name if athlete.user else 'Athlete'} has {direction} by "
                            f"{abs(change)} points across the filtered analysis history."
                        ),
                        metric=label,
                        supporting_analyses=len(athlete_analyses),
                    )
                )
                break
    return observations[:10]


def report_metric_summary(analyses: list[AnalysisResult], specs: list[dict]):
    rows = []
    for spec in specs:
        values = [comparison_metric_value(analysis, spec["key"]) for analysis in analyses]
        rows.append({
            "key": spec["key"],
            "label": spec["label"],
            "average": average_numeric(values),
            "count": len([value for value in values if value is not None]),
        })
    return rows


def research_report_history(analyses: list[AnalysisResult], created_by: str):
    items = []
    for analysis in analyses:
        if not get_existing_analysis_report_path(analysis.video_id, "pdf"):
            continue
        athlete = analysis.athlete
        athlete_name = athlete.user.name if athlete and athlete.user else "Athlete"
        activity = analysis.video.activity if analysis.video else "Movement Analysis"
        created_at = event_date(analysis)
        items.append(
            SportsScientistResearchReportHistoryItem(
                report_id=f"analysis-{analysis.analysis_id}",
                report_name=f"{athlete_name} - {activity}",
                scope="Individual analysis",
                created_date=created_at,
                created_by="Analysis Pipeline",
                status="Available",
                analysis_id=analysis.analysis_id,
                athlete_id=analysis.athlete_id,
                pdf_available=True,
            )
        )
    return items[:20]


def build_research_report(
    analyses: list[AnalysisResult],
    athletes: list[Athlete],
    current_user: User,
    injury_records: list[InjuryHistory],
    title: str | None = None,
):
    athlete_ids = {analysis.athlete_id for analysis in analyses}
    scoped_athletes = [athlete for athlete in athletes if athlete.athlete_id in athlete_ids]
    dates = [event_date(analysis) for analysis in analyses if event_date(analysis)]
    start = min(dates).date().isoformat() if dates else "Not Available"
    end = max(dates).date().isoformat() if dates else "Not Available"
    sports = sorted({athlete.sport for athlete in scoped_athletes if athlete.sport})
    scope = "No matching analyses"
    if len(scoped_athletes) == 1:
        athlete = scoped_athletes[0]
        scope = f"Individual athlete: {athlete.user.name if athlete.user else 'Athlete'}"
    elif sports:
        scope = f"{', '.join(sports)} group ({len(scoped_athletes)} athletes)"
    elif scoped_athletes:
        scope = f"Selected athlete group ({len(scoped_athletes)} athletes)"

    risk_counts = Counter()
    factor_counts = Counter()
    for analysis in analyses:
        score = get_analysis_score(analysis)
        risk_counts[normalize_risk_category_label(analysis.risk_category, score)] += 1
        for label in main_factor_labels(analysis, limit=len(INJURY_FACTOR_DEFINITIONS)):
            factor_counts[label] += 1

    total = sum(risk_counts.values())
    risk_distribution_rows = [
        {"category": band, "count": risk_counts.get(band, 0), "percentage": round((risk_counts.get(band, 0) / total) * 100, 1) if total else 0}
        for band in RISK_BANDS
    ]
    patterns = observed_pattern_rows(analyses, injury_records)
    report_title = title or f"Sports Scientist Research Report - {datetime.utcnow().strftime('%Y-%m-%d')}"

    return {
        "title": report_title,
        "overview": {
            "scope": scope,
            "date_range": f"{start} to {end}",
            "athlete_count": len(scoped_athletes),
            "analysis_count": len(analyses),
            "created_by": current_user.name or current_user.email,
            "created_at": datetime.utcnow().isoformat(),
        },
        "performance_summary": report_metric_summary(analyses, [
            {"key": "movement_quality", "label": "Movement Quality"},
            {"key": "biomechanical_efficiency", "label": "Biomechanical Efficiency"},
            {"key": "symmetry", "label": "Symmetry"},
            {"key": "overall_risk", "label": "Overall Risk"},
        ]),
        "biomechanical_analysis": report_metric_summary(analyses, [
            {"key": "knee_risk", "label": "Knee"},
            {"key": "hip_risk", "label": "Hip"},
            {"key": "trunk_risk", "label": "Trunk"},
            {"key": "landing_risk", "label": "Landing"},
            {"key": "balance_risk", "label": "Balance"},
            {"key": "alignment_risk", "label": "Alignment"},
            {"key": "posture_risk", "label": "Posture"},
        ]),
        "risk_analysis": {
            "distribution": risk_distribution_rows,
            "trends": [item.model_dump() for item in risk_trend_points(analyses)],
            "previous_injury_history_count": len({record.athlete_id for record in injury_records}),
            "training_load_values": len([analysis for analysis in analyses if comparison_metric_value(analysis, "training_load") is not None]),
            "recurring_factors": [
                {"label": label, "count": count}
                for label, count in factor_counts.most_common(8)
                if count >= 1
            ],
        },
        "observed_patterns": [pattern.model_dump() for pattern in patterns],
        "methodology": (
            "This report summarizes existing completed movement analyses produced by the application. "
            "It references stored biomechanical metrics, including knee/valgus, hip, trunk, landing, "
            "balance, alignment, posture, symmetry, movement quality, biomechanical efficiency, and "
            "the application's existing rule-based injury-risk scoring outputs. No new prediction "
            "formula is introduced in this report."
        ),
        "disclaimer": (
            "This report is based on available video and biomechanical analysis data. It is intended "
            "as a sports science screening and analytical tool, not a medical diagnosis, treatment "
            "recommendation, or guaranteed injury prediction."
        ),
    }


def risk_trend_points(analyses: list[AnalysisResult]):
    grouped = defaultdict(list)
    for analysis in analyses:
        key = date_bucket(event_date(analysis))
        score = get_analysis_score(analysis)
        if key and score is not None:
            grouped[key].append(score)
    return [
        SportsScientistRiskTrendPoint(
            date=key,
            average_risk_score=average_numeric(values),
            analyses=len(values),
        )
        for key, values in sorted(grouped.items())
    ]


def average_risk_by_sport(analyses: list[AnalysisResult]):
    grouped = defaultdict(list)
    for analysis in analyses:
        sport = analysis.athlete.sport if analysis.athlete else None
        score = get_analysis_score(analysis)
        if sport and score is not None:
            grouped[sport].append(score)
    return [
        SportsScientistRiskGroupAverage(
            group=sport,
            average_risk_score=average_numeric(values),
            analyses=len(values),
        )
        for sport, values in sorted(grouped.items())
        if len(values) >= MIN_GROUP_ANALYSES
    ]


def factor_analysis_rows(analyses: list[AnalysisResult]):
    rows = []
    for definition in INJURY_FACTOR_DEFINITIONS:
        values = []
        latest_at = None
        trend_group = defaultdict(list)
        for analysis in analyses:
            value = risk_factor_numeric_value(analysis, definition)
            if value is None or value <= 0:
                continue
            values.append(value)
            current_date = event_date(analysis)
            if current_date and (latest_at is None or current_date > latest_at):
                latest_at = current_date
            key = date_bucket(current_date)
            if key:
                trend_group[key].append(value)

        rows.append(
            SportsScientistRiskFactorInsight(
                key=definition["key"],
                label=definition["label"],
                frequency=len(values),
                average_risk=average_numeric(values),
                latest_at=latest_at,
                trend=[
                    SportsScientistRiskTrendPoint(
                        date=key,
                        average_risk_score=average_numeric(group_values),
                        analyses=len(group_values),
                    )
                    for key, group_values in sorted(trend_group.items())
                ],
            )
        )
    return rows


def main_factor_labels(analysis: AnalysisResult, limit: int = 3):
    scored = []
    for definition in INJURY_FACTOR_DEFINITIONS:
        value = risk_factor_numeric_value(analysis, definition)
        if value is not None and value > 0:
            scored.append((definition["label"], value))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [label for label, _value in scored[:limit]]


def athlete_risk_rows(
    athletes: list[Athlete],
    analyses: list[AnalysisResult],
    injury_records: list[InjuryHistory],
):
    latest = latest_analysis_by_athlete(analyses)
    injured_athletes = {record.athlete_id for record in injury_records}
    rows = []
    for athlete in athletes:
        latest_analysis = latest.get(athlete.athlete_id)
        if latest_analysis is None:
            continue
        score = get_analysis_score(latest_analysis)
        rows.append(
            SportsScientistAthleteRiskRow(
                athlete_id=athlete.athlete_id,
                athlete_name=athlete.user.name if athlete.user else "Athlete",
                sport=athlete.sport,
                risk_category=normalize_risk_category_label(latest_analysis.risk_category, score),
                risk_score=round(float(score), 1) if score is not None else None,
                movement_quality=round(float(latest_analysis.movement_quality), 1) if latest_analysis.movement_quality is not None else None,
                main_risk_factors=main_factor_labels(latest_analysis),
                previous_injury=athlete.athlete_id in injured_athletes,
                latest_analysis=event_date(latest_analysis),
            )
        )
    return sorted(rows, key=lambda row: row.latest_analysis or datetime.min, reverse=True)


def observed_pattern_rows(analyses: list[AnalysisResult], injury_records: list[InjuryHistory]):
    patterns = []
    by_athlete = defaultdict(list)
    for analysis in analyses:
        by_athlete[analysis.athlete_id].append(analysis)

    injured_athletes = {record.athlete_id for record in injury_records}
    for athlete_id, athlete_analyses in by_athlete.items():
        ordered = sorted(athlete_analyses, key=lambda item: event_date(item) or datetime.min)
        athlete = ordered[-1].athlete
        athlete_name = athlete.user.name if athlete and athlete.user else "Athlete"

        for definition in INJURY_FACTOR_DEFINITIONS:
            matches = [
                analysis for analysis in ordered
                if factor_matches_analysis(analysis, definition)
            ]
            if len(matches) >= 2:
                patterns.append(
                    SportsScientistObservedPattern(
                        title=f"Recurring {definition['label'].lower()} risk factor",
                        description=(
                            f"{athlete_name} has {len(matches)} completed analyses with an observed "
                            f"{definition['label'].lower()} risk factor."
                        ),
                        athlete_id=athlete_id,
                        athlete_name=athlete_name,
                        supporting_analyses=len(matches),
                    )
                )
                break

        scores = [get_analysis_score(analysis) for analysis in ordered if get_analysis_score(analysis) is not None]
        if len(scores) >= 3:
            first_avg = average_numeric(scores[:2])
            last_avg = average_numeric(scores[-2:])
            if first_avg is not None and last_avg is not None and abs(last_avg - first_avg) >= 10:
                direction = "increasing" if last_avg > first_avg else "decreasing"
                patterns.append(
                    SportsScientistObservedPattern(
                        title=f"{direction.title()} risk score pattern",
                        description=(
                            f"{athlete_name} shows a {direction} stored risk-score pattern across "
                            f"{len(scores)} analyses."
                        ),
                        athlete_id=athlete_id,
                        athlete_name=athlete_name,
                        supporting_analyses=len(scores),
                    )
                )

        asymmetry_matches = [
            analysis for analysis in ordered
            if risk_factor_numeric_value(analysis, INJURY_FACTOR_DEFINITIONS[7]) is not None
            and risk_factor_numeric_value(analysis, INJURY_FACTOR_DEFINITIONS[7]) > 0
        ]
        if len(asymmetry_matches) >= 2:
            patterns.append(
                SportsScientistObservedPattern(
                    title="Repeated movement asymmetry observation",
                    description=(
                        f"{athlete_name} has repeated completed analyses with stored movement asymmetry "
                        "risk contributions."
                    ),
                    athlete_id=athlete_id,
                    athlete_name=athlete_name,
                    supporting_analyses=len(asymmetry_matches),
                )
            )

        history_matches = [
            analysis for analysis in ordered
            if risk_factor_numeric_value(analysis, INJURY_FACTOR_DEFINITIONS[8]) is not None
            and risk_factor_numeric_value(analysis, INJURY_FACTOR_DEFINITIONS[8]) > 0
        ]
        if athlete_id in injured_athletes and history_matches:
            patterns.append(
                SportsScientistObservedPattern(
                    title="Previous injury history association",
                    description=(
                        f"{athlete_name} has recorded previous injury history associated with stored "
                        "historical injury risk contribution in completed analyses."
                    ),
                    athlete_id=athlete_id,
                    athlete_name=athlete_name,
                    supporting_analyses=len(history_matches),
                )
            )

    return patterns[:12]


def metric_detail(analysis: AnalysisResult, key, label, value, unit=None, keywords=None):
    if value is None:
        return None
    factor = first_matching_risk_factor(analysis, keywords or [key.replace("_", " ")])
    return SportsScientistMetricDetail(
        key=key,
        label=label,
        value=round(float(value), 2),
        unit=unit,
        severity=factor.get("severity") if factor else None,
        interpretation=factor.get("observed_value") if factor else None,
    )


def detailed_metrics(analysis: AnalysisResult):
    metric_map = biomechanical_metric_values(analysis)
    candidates = [
        ("knee_valgus", "Knee Valgus", analysis.knee_valgus, None, ["knee", "valgus"]),
        ("knee_risk", "Knee Risk", risk_value_for_keywords(analysis, ["knee", "valgus"]), None, ["knee", "valgus"]),
        ("hip_stability", "Hip Stability", analysis.hip_stability, None, ["hip", "pelvic"]),
        ("hip_risk", "Hip Risk", risk_value_for_keywords(analysis, ["hip", "pelvic"]), None, ["hip", "pelvic"]),
        ("trunk_lean", "Trunk Lean", analysis.trunk_lean, None, ["trunk"]),
        ("trunk_risk", "Trunk Risk", risk_value_for_keywords(analysis, ["trunk"]), None, ["trunk"]),
        ("landing_mechanics", "Landing Mechanics", metric_map.get("landing_mechanics"), None, ["landing"]),
        ("landing_risk", "Landing Risk", risk_value_for_keywords(analysis, ["landing"]), None, ["landing"]),
        ("balance", "Balance", metric_map.get("balance"), None, ["balance", "sway"]),
        ("balance_risk", "Balance Risk", risk_value_for_keywords(analysis, ["balance", "sway"]), None, ["balance", "sway"]),
        ("alignment", "Alignment", metric_map.get("alignment"), None, ["alignment"]),
        ("alignment_risk", "Alignment Risk", risk_value_for_keywords(analysis, ["alignment"]), None, ["alignment"]),
        ("posture", "Posture", metric_map.get("posture"), None, ["posture"]),
        ("posture_risk", "Posture Risk", risk_value_for_keywords(analysis, ["posture"]), None, ["posture"]),
        ("overall_symmetry", "Overall Symmetry", metric_map.get("movement_symmetry"), None, ["asymmetry", "symmetry"]),
        ("stride_asymmetry", "Stride Asymmetry", first_numeric_value(analysis, [["stride", "stride_asymmetry_pct"]]), None, ["stride"]),
        ("stride_length", "Stride Length", analysis.stride_length, None, ["stride"]),
    ]
    return [
        item
        for item in (metric_detail(analysis, *candidate) for candidate in candidates)
        if item is not None
    ]


def top_level_risk_contributions(analysis: AnalysisResult):
    assessment = risk_assessment(analysis)
    scores = assessment.get("component_scores") if isinstance(assessment.get("component_scores"), dict) else {}
    weights = assessment.get("display_weights") if isinstance(assessment.get("display_weights"), dict) else {}
    labels = {
        "biomechanical_deviations": "Biomechanical Deviations",
        "historical_injury_factors": "Previous Injury History",
        "movement_asymmetry": "Movement Asymmetry",
        "training_load": "Training Load",
        "fatigue": "Fatigue",
    }
    return [
        {
            "key": key,
            "label": label,
            "observed_contribution": scores.get(key),
            "configured_weight": weights.get(key) or DISPLAY_WEIGHTS.get(key),
        }
        for key, label in labels.items()
    ]


def risk_value_for_keywords(analysis: AnalysisResult, keywords: list[str]):
    factor = first_matching_risk_factor(analysis, keywords)
    if not factor:
        return None
    try:
        return round(float(factor.get("risk_contribution")), 2)
    except (TypeError, ValueError):
        return None


def biomechanical_breakdown(analysis: AnalysisResult):
    labels = {
        "knee_valgus": ("Knee", ["knee", "valgus"]),
        "hip_stability": ("Hip", ["hip", "pelvic"]),
        "trunk_lean": ("Trunk", ["trunk"]),
        "landing_mechanics": ("Landing", ["landing"]),
        "dynamic_balance": ("Balance", ["balance", "sway"]),
        "joint_alignment": ("Alignment", ["alignment"]),
        "posture": ("Posture", ["posture"]),
    }
    rows = []
    for key, weight in BIOMECHANICAL_SUBMETRIC_WEIGHTS.items():
        label, keywords = labels.get(key, (key.replace("_", " ").title(), [key.replace("_", " ")]))
        factor = first_matching_risk_factor(analysis, keywords)
        rows.append({
            "key": key,
            "label": label,
            "configured_weight": round(weight * 100, 2),
            "risk_value": factor.get("risk_contribution") if factor else None,
            "severity": factor.get("severity") if factor else None,
            "weighted_contribution": None,
        })
    return rows


def symmetry_payload(analysis: AnalysisResult):
    assessment = risk_assessment(analysis)
    details = assessment.get("asymmetry_details") if isinstance(assessment.get("asymmetry_details"), dict) else {}
    summary = analysis.summary_metrics if isinstance(analysis.summary_metrics, dict) else {}
    stride = summary.get("stride") if isinstance(summary.get("stride"), dict) else {}
    symmetry = summary.get("symmetry") if isinstance(summary.get("symmetry"), dict) else {}
    return {
        "overall_symmetry": analysis.symmetry_score or details.get("symmetry_score") or symmetry.get("overall_symmetry_score"),
        "asymmetry_risk": analysis.asymmetry_score or details.get("asymmetry_risk"),
        "stride_asymmetry": stride.get("stride_asymmetry_pct"),
        "left_right_differences": symmetry.get("factors") if isinstance(symmetry.get("factors"), list) else [],
        "affected_metrics": details.get("affected_metrics") if isinstance(details.get("affected_metrics"), list) else [],
    }


def biomechanical_efficiency_payload(analysis: AnalysisResult):
    assessment = risk_assessment(analysis)
    value = (
        assessment.get("biomechanical_efficiency_score")
        or analysis.biomechanical_score
    )
    return {
        "final": value,
        "components": [],
        "component_note": "Component values are not stored separately for this analysis." if value is not None else "Data not available for this metric.",
    }


def risk_distribution(latest_by_athlete: list[AnalysisResult]):
    counts = {band: 0 for band in RISK_BANDS}
    for analysis in latest_by_athlete:
        score = get_analysis_score(analysis)
        band = normalize_risk_category_label(analysis.risk_category, score)
        if band in counts:
            counts[band] += 1

    total = sum(counts.values())
    return [
        SportsScientistRiskBand(
            category=band,
            count=count,
            percentage=round((count / total) * 100, 1) if total else 0,
        )
        for band, count in counts.items()
    ]


def biomechanical_overview(analyses: list[AnalysisResult]):
    labels = {
        "knee_valgus": "Knee Valgus / Knee Risk",
        "hip_stability": "Hip Stability / Hip Risk",
        "trunk_lean": "Trunk Lean / Trunk Risk",
        "landing_mechanics": "Landing Mechanics",
        "balance": "Balance",
        "alignment": "Alignment",
        "posture": "Posture",
        "movement_symmetry": "Movement Symmetry",
        "movement_quality": "Movement Quality",
        "biomechanical_efficiency": "Biomechanical Efficiency",
    }
    values = defaultdict(list)
    for analysis in analyses:
        for key, value in biomechanical_metric_values(analysis).items():
            if value is not None:
                try:
                    values[key].append(float(value))
                except (TypeError, ValueError):
                    continue

    return [
        SportsScientistMetricSummary(
            key=key,
            label=label,
            average=round(sum(values[key]) / len(values[key]), 1) if values[key] else None,
            count=len(values[key]),
        )
        for key, label in labels.items()
    ]


def performance_trend(analyses: list[AnalysisResult]):
    points = []
    for analysis in sorted(analyses, key=lambda item: event_date(item) or datetime.min)[-12:]:
        value = analysis.movement_quality
        if value is None:
            continue
        points.append(
            SportsScientistTrendPoint(
                date=event_date(analysis),
                value=round(float(value), 1),
                metric="Movement Quality",
            )
        )
    return points


def top_findings(analyses: list[AnalysisResult]):
    counts = Counter()
    latest_dates = {}

    for analysis in analyses:
        for factor in risk_factors(analysis):
            if not isinstance(factor, dict):
                continue
            label = factor.get("factor") or factor.get("category") or factor.get("title")
            if not label:
                continue
            counts[label] += 1
            current_date = event_date(analysis)
            if current_date and (label not in latest_dates or current_date > latest_dates[label]):
                latest_dates[label] = current_date

    return [
        SportsScientistFinding(
            label=label,
            count=count,
            latest_at=latest_dates.get(label),
        )
        for label, count in counts.most_common(5)
    ]


def recent_analysis_item(analysis: AnalysisResult):
    score = get_analysis_score(analysis)
    biomechanical_efficiency = (
        metric_from_summary(analysis, ["risk_assessment", "biomechanical_efficiency_score"])
        or analysis.biomechanical_score
    )
    athlete = analysis.athlete
    return SportsScientistRecentAnalysis(
        analysis_id=analysis.analysis_id,
        athlete_id=analysis.athlete_id,
        video_id=analysis.video_id,
        athlete_name=athlete.user.name if athlete and athlete.user else "Athlete",
        sport=athlete.sport if athlete else None,
        position=athlete.position if athlete else None,
        analysis_date=event_date(analysis),
        risk_category=normalize_risk_category_label(analysis.risk_category, score),
        risk_score=round(float(score), 1) if score is not None else None,
        movement_quality=round(float(analysis.movement_quality), 1) if analysis.movement_quality is not None else None,
        biomechanical_efficiency=round(float(biomechanical_efficiency), 1) if biomechanical_efficiency is not None else None,
        status=analysis.status,
    )


def analysis_detail_item(analysis: AnalysisResult):
    base = recent_analysis_item(analysis)
    assessment = risk_assessment(analysis)
    payload = base.model_dump()
    payload.pop("biomechanical_efficiency", None)
    return SportsScientistAnalysisDetail(
        **payload,
        video_activity=analysis.video.activity if analysis.video else None,
        video_url=analysis.video.video_url if analysis.video else None,
        summary={
            "risk_score": base.risk_score,
            "movement_quality": base.movement_quality,
            "biomechanical_efficiency": base.biomechanical_efficiency,
            "movement_symmetry": symmetry_payload(analysis).get("overall_symmetry"),
            "overall_risk_score": base.risk_score,
            "risk_category": base.risk_category,
        },
        source_analysis={
            "analysis_id": str(analysis.analysis_id),
            "video_id": str(analysis.video_id),
            "video_activity": analysis.video.activity if analysis.video else None,
            "video_url": analysis.video.video_url if analysis.video else None,
            "analyzed_at": event_date(analysis),
            "algorithm_version": analysis.algorithm_version,
        },
        metrics=detailed_metrics(analysis),
        risk_contributions=top_level_risk_contributions(analysis),
        biomechanical_breakdown=biomechanical_breakdown(analysis),
        biomechanical_efficiency=biomechanical_efficiency_payload(analysis),
        symmetry=symmetry_payload(analysis),
        risk_factors=risk_factors(analysis),
    )


@router.get("/profile", response_model=ProfessionalProfileResponse)
def get_sports_scientist_profile(
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
):
    return profile


@router.put("/profile", response_model=ProfessionalProfileResponse)
def update_sports_scientist_profile(
    profile_data: ProfessionalProfileUpdate,
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    completed_fields = [
        "primary_sport",
        "other_sports",
        "years_of_experience",
        "specialization",
        "organization",
        "certifications",
        "professional_bio",
    ]
    completed_count = sum(
        1
        for field in completed_fields
        if getattr(profile, field, None) not in (None, "")
    )
    profile.profile_completion = round((completed_count / len(completed_fields)) * 100, 1)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/athletes/discover", response_model=list[SportsScientistDiscoveryAthlete])
def discover_sports_scientist_athletes(
    search: str | None = Query(default=None),
    sport: str | None = Query(default=None),
    position: str | None = Query(default=None),
    connection_status: str | None = Query(default=None),
    sort: str = Query(default="name"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Athlete)
        .join(User, Athlete.user_id == User.user_id)
        .filter(User.role == UserRole.ATHLETE)
        .options(joinedload(Athlete.user))
    )

    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    if sport:
        query = query.filter(Athlete.sport.ilike(f"%{sport}%"))
    if position:
        query = query.filter(Athlete.position.ilike(f"%{position}%"))

    items = []
    for athlete in query.all():
        active_professional_relationship = (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            )
            .first()
        )
        if active_professional_relationship:
            continue

        relationship = (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == SCIENTIST_ROLE,
            )
            .order_by(ProfessionalAthleteRelationship.created_at.desc())
            .first()
        )
        item = scientist_discovery_item(db, athlete, relationship)
        if connection_status and item.connection_status != connection_status.upper():
            continue
        items.append(item)

    if sort == "risk_desc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else -1, reverse=True)
    elif sort == "risk_asc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else 101)
    elif sort == "recent":
        items.sort(key=lambda item: item.latest_activity_at or datetime.min, reverse=True)
    else:
        items.sort(key=lambda item: item.name.lower())

    return items[offset:offset + limit]


@router.get("/athletes", response_model=list[SportsScientistConnectedAthlete])
def get_sports_scientist_athletes(
    search: str | None = Query(default=None),
    sport: str | None = Query(default=None),
    connection_status: str | None = Query(default=None),
    sort: str = Query(default="recent"),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships(db, profile)
    items = [
        scientist_athlete_item(db, relationship)
        for relationship in relationships
        if relationship.athlete is not None
    ]

    if search:
        search_text = search.lower()
        items = [item for item in items if search_text in item.name.lower()]
    if sport:
        items = [item for item in items if item.sport and sport.lower() in item.sport.lower()]
    if connection_status and connection_status.upper() != "ACTIVE":
        items = []

    if sort == "risk_desc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else -1, reverse=True)
    elif sort == "risk_asc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else 101)
    elif sort == "name":
        items.sort(key=lambda item: item.name.lower())
    else:
        items.sort(key=lambda item: item.last_analysis_at or datetime.min, reverse=True)

    return items


@router.post(
    "/athletes/{athlete_id}/connection-requests",
    response_model=SportsScientistRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_sports_scientist_connection_request(
    athlete_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationship = create_request(
        db=db,
        professional_user_id=profile.user_id,
        athlete_id=athlete_id,
        professional_role=SCIENTIST_ROLE,
        requested_by=profile.user_id,
    )
    athlete = db.query(Athlete).filter(Athlete.athlete_id == athlete_id).first()
    if athlete and athlete.user_id:
        create_notification(
            db,
            recipient_user_id=athlete.user_id,
            notification_type=NotificationType.CONNECTION_REQUEST,
            title="Sports Scientist connection request",
            message="A Sports Scientist requested access to your analysis data.",
            actor_user_id=profile.user_id,
            entity_type="professional_athlete_relationship",
            entity_id=relationship.relationship_id,
            action_url="/dashboard",
        )
        db.commit()
        db.refresh(relationship)
    return relationship


@router.get("/requests", response_model=list[SportsScientistRelationshipResponse])
def get_sports_scientist_requests(
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.requester),
        )
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.professional_role == SCIENTIST_ROLE,
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .all()
    )


@router.post("/requests/{relationship_id}/accept", response_model=SportsScientistRelationshipResponse)
def accept_sports_scientist_incoming_request(
    relationship_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationship = relationship_for_scientist(db, profile, relationship_id)
    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending Sports Scientist requests can be accepted",
        )
    if relationship.requested_by == profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete approval is required for requests you initiated",
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now
    db.commit()
    db.refresh(relationship)
    return relationship


@router.post("/requests/{relationship_id}/reject", response_model=SportsScientistRelationshipResponse)
def reject_sports_scientist_incoming_request(
    relationship_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationship = relationship_for_scientist(db, profile, relationship_id)
    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending Sports Scientist requests can be rejected",
        )
    if relationship.requested_by == profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete approval is required for requests you initiated",
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None
    db.commit()
    db.refresh(relationship)
    return relationship


@router.post("/relationships/{relationship_id}/remove", response_model=SportsScientistRelationshipResponse)
def remove_sports_scientist_connection(
    relationship_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationship = relationship_for_scientist(db, profile, relationship_id)
    if relationship.status != ProfessionalAthleteRelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active Sports Scientist relationships can be removed",
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REVOKED.value
    relationship.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(relationship)
    return relationship


@router.get("/dashboard", response_model=SportsScientistDashboardResponse)
def get_sports_scientist_dashboard(
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships(db, profile)
    athletes = [relationship.athlete for relationship in relationships if relationship.athlete is not None]
    athlete_ids = [athlete.athlete_id for athlete in athletes]
    analyses = completed_analyses_for_athletes(db, athlete_ids)
    latest_analyses = [
        latest
        for latest in (latest_completed_analysis(db, athlete_id) for athlete_id in athlete_ids)
        if latest is not None
    ]
    risk_bands = risk_distribution(latest_analyses)
    high_critical = sum(band.count for band in risk_bands if band.category in HIGH_RISK_BANDS)
    sports = {athlete.sport for athlete in athletes if athlete.sport}

    return SportsScientistDashboardResponse(
        professional_profile_id=profile.professional_profile_id,
        verification_status=profile.verification_status,
        stats={
            "athletes_monitored": len(athletes),
            "analyses_completed": len(analyses),
            "high_critical_risk": high_critical,
            "sports_covered": len(sports),
        },
        risk_distribution=risk_bands,
        biomechanical_overview=biomechanical_overview(analyses),
        performance_trend=performance_trend(analyses),
        findings=top_findings(analyses),
        recent_analyses=[recent_analysis_item(analysis) for analysis in analyses[:8]],
    )


@router.get("/biomechanical-analytics", response_model=SportsScientistBiomechanicalAnalyticsResponse)
def get_biomechanical_analytics(
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships(db, profile)
    athletes = [relationship.athlete for relationship in relationships if relationship.athlete is not None]
    athlete_ids = [athlete.athlete_id for athlete in athletes]
    analyses = completed_analyses_for_athletes(db, athlete_ids)
    sports = sorted({athlete.sport for athlete in athletes if athlete.sport})

    return SportsScientistBiomechanicalAnalyticsResponse(
        athletes=[
            SportsScientistAthleteOption(
                athlete_id=athlete.athlete_id,
                name=athlete.user.name if athlete.user else "Athlete",
                sport=athlete.sport,
                position=athlete.position,
            )
            for athlete in athletes
        ],
        sports=sports,
        analyses=[analysis_detail_item(analysis) for analysis in analyses],
    )


@router.get("/injury-insights", response_model=SportsScientistInjuryInsightsResponse)
def get_injury_insights(
    sport: str | None = Query(default=None),
    athlete_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    injury_factor: str | None = Query(default=None),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships(db, profile)
    athletes = [relationship.athlete for relationship in relationships if relationship.athlete is not None]
    athlete_ids = [athlete.athlete_id for athlete in athletes]

    if athlete_id and athlete_id not in athlete_ids:
        raise HTTPException(status_code=403, detail="Not authorized to access this athlete")

    if injury_factor and injury_factor not in {item["key"] for item in INJURY_FACTOR_DEFINITIONS}:
        raise HTTPException(status_code=400, detail="Unsupported injury factor")

    all_analyses = completed_analyses_for_athletes(db, athlete_ids)
    filtered_analyses = filtered_completed_analyses(
        all_analyses,
        athlete_id=athlete_id,
        sport=sport,
        start_date=start_date,
        end_date=end_date,
        risk_level=risk_level,
        injury_factor=injury_factor,
    )
    filtered_athlete_ids = sorted({analysis.athlete_id for analysis in filtered_analyses})
    filtered_athletes = [athlete for athlete in athletes if athlete.athlete_id in filtered_athlete_ids]
    injury_records = injury_history_for_athletes(db, filtered_athlete_ids)
    latest_analyses = list(latest_analysis_by_athlete(filtered_analyses).values())
    risk_bands = risk_distribution(latest_analyses)
    scores = [get_analysis_score(analysis) for analysis in filtered_analyses]
    high_critical = sum(
        1
        for analysis in filtered_analyses
        if normalize_risk_category_label(analysis.risk_category, get_analysis_score(analysis)) in HIGH_RISK_BANDS
    )
    previous_injury_athletes = {record.athlete_id for record in injury_records}
    factor_counts = Counter()
    for analysis in filtered_analyses:
        for label in main_factor_labels(analysis, limit=len(INJURY_FACTOR_DEFINITIONS)):
            factor_counts[label] += 1

    sports = sorted({athlete.sport for athlete in athletes if athlete.sport})

    return SportsScientistInjuryInsightsResponse(
        athletes=[
            SportsScientistAthleteOption(
                athlete_id=athlete.athlete_id,
                name=athlete.user.name if athlete.user else "Athlete",
                sport=athlete.sport,
                position=athlete.position,
            )
            for athlete in athletes
        ],
        sports=sports,
        injury_factors=[definition["key"] for definition in INJURY_FACTOR_DEFINITIONS],
        summary={
            "athletes_analyzed": len(filtered_athlete_ids),
            "high_critical_risk_analyses": high_critical,
            "average_risk_score": average_numeric(scores),
            "previous_injury_cases": len(previous_injury_athletes),
            "most_frequent_risk_factor": factor_counts.most_common(1)[0][0] if factor_counts else None,
            "analyses": len(filtered_analyses),
        },
        risk_distribution=risk_bands,
        risk_trend=risk_trend_points(filtered_analyses),
        average_risk_by_sport=average_risk_by_sport(filtered_analyses),
        factor_analysis=factor_analysis_rows(filtered_analyses),
        athlete_table=athlete_risk_rows(filtered_athletes, filtered_analyses, injury_records),
        observed_patterns=observed_pattern_rows(filtered_analyses, injury_records),
    )


@router.get("/athlete-comparison", response_model=SportsScientistAthleteComparisonResponse)
def get_athlete_comparison(
    sport: str | None = Query(default=None),
    position: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    athlete_ids: list[UUID] | None = Query(default=None),
    analysis_ids: list[UUID] | None = Query(default=None),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships(db, profile)
    athletes = [relationship.athlete for relationship in relationships if relationship.athlete is not None]
    authorized_athlete_ids = {athlete.athlete_id for athlete in athletes}
    selected_athlete_ids = list(dict.fromkeys(athlete_ids or []))
    selected_analysis_ids = set(analysis_ids or [])

    unauthorized_athletes = [athlete_id for athlete_id in selected_athlete_ids if athlete_id not in authorized_athlete_ids]
    if unauthorized_athletes:
        raise HTTPException(status_code=403, detail="Not authorized to access one or more selected athletes")

    if selected_athlete_ids and not 2 <= len(selected_athlete_ids) <= 5:
        raise HTTPException(status_code=400, detail="Select between 2 and 5 athletes for comparison")

    all_analyses = completed_analyses_for_athletes(db, list(authorized_athlete_ids))
    filtered_analyses = filtered_comparison_analyses(
        all_analyses,
        sport=sport,
        position=position,
        start_date=start_date,
        end_date=end_date,
    )
    filtered_analysis_ids = {analysis.analysis_id for analysis in filtered_analyses}
    unauthorized_analyses = [analysis_id for analysis_id in selected_analysis_ids if analysis_id not in filtered_analysis_ids]
    if unauthorized_analyses:
        raise HTTPException(status_code=403, detail="Not authorized to access one or more selected analyses")

    if selected_athlete_ids and selected_analysis_ids:
        selected_athlete_id_set = set(selected_athlete_ids)
        selected_scope_analysis_ids = {
            analysis.analysis_id for analysis in filtered_analyses
            if analysis.athlete_id in selected_athlete_id_set
        }
        mismatched_analyses = [
            analysis_id for analysis_id in selected_analysis_ids
            if analysis_id not in selected_scope_analysis_ids
        ]
        if mismatched_analyses:
            raise HTTPException(status_code=400, detail="Selected analyses must belong to selected athletes")

    available_athlete_ids = {analysis.athlete_id for analysis in filtered_analyses}
    available_athletes = [
        athlete for athlete in athletes
        if athlete.athlete_id in available_athlete_ids
    ]
    selected_athletes = [
        athlete for athlete_id in selected_athlete_ids
        for athlete in athletes
        if athlete.athlete_id == athlete_id and athlete.athlete_id in available_athlete_ids
    ]

    if selected_athlete_ids and len(selected_athletes) != len(selected_athlete_ids):
        raise HTTPException(status_code=400, detail="One or more selected athletes have no completed analyses for these filters")

    sports = sorted({athlete.sport for athlete in athletes if athlete.sport})
    positions = sorted({athlete.position for athlete in athletes if athlete.position})

    return SportsScientistAthleteComparisonResponse(
        athletes=[comparison_athlete_option(athlete, filtered_analyses) for athlete in available_athletes],
        sports=sports,
        positions=positions,
        selected_athletes=[comparison_athlete_option(athlete, filtered_analyses) for athlete in selected_athletes],
        metric_rows=comparison_metric_rows(selected_athletes, filtered_analyses, selected_analysis_ids) if selected_athletes else [],
        history=comparison_history(filtered_analyses, set(selected_athlete_ids)) if selected_athletes else [],
        observations=comparison_observations(selected_athletes, filtered_analyses, selected_analysis_ids) if selected_athletes else [],
    )


def research_report_scope(
    db: Session,
    profile: ProfessionalProfile,
    sport: str | None,
    athlete_ids: list[UUID] | None,
    start_date: date | None,
    end_date: date | None,
    analysis_id: UUID | None,
    risk_level: str | None,
):
    relationships = active_relationships(db, profile)
    athletes = [relationship.athlete for relationship in relationships if relationship.athlete is not None]
    authorized_ids = {athlete.athlete_id for athlete in athletes}
    selected_ids = set(athlete_ids or [])
    if selected_ids and not selected_ids.issubset(authorized_ids):
        raise HTTPException(status_code=403, detail="Not authorized to access one or more selected athletes")

    all_analyses = completed_analyses_for_athletes(db, list(authorized_ids))
    if analysis_id:
        matching = [analysis for analysis in all_analyses if analysis.analysis_id == analysis_id]
        if not matching:
            raise HTTPException(status_code=403, detail="Not authorized to access this analysis")
        scoped = matching
    else:
        scoped = all_analyses
        if selected_ids:
            scoped = [analysis for analysis in scoped if analysis.athlete_id in selected_ids]
        scoped = filtered_completed_analyses(
            scoped,
            sport=sport,
            start_date=start_date,
            end_date=end_date,
            risk_level=risk_level,
        )

    scoped_athlete_ids = sorted({analysis.athlete_id for analysis in scoped})
    injury_records = injury_history_for_athletes(db, scoped_athlete_ids)
    return athletes, scoped, injury_records


@router.get("/research-reports", response_model=SportsScientistResearchReportResponse)
def get_research_reports(
    sport: str | None = Query(default=None),
    athlete_ids: list[UUID] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    analysis_id: UUID | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    title: str | None = Query(default=None),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    athletes, analyses, injury_records = research_report_scope(
        db, profile, sport, athlete_ids, start_date, end_date, analysis_id, risk_level
    )
    all_analyses = completed_analyses_for_athletes(db, [athlete.athlete_id for athlete in athletes])
    current_user = db.query(User).filter(User.user_id == profile.user_id).first()
    sports = sorted({athlete.sport for athlete in athletes if athlete.sport})

    return SportsScientistResearchReportResponse(
        athletes=[comparison_athlete_option(athlete, all_analyses) for athlete in athletes],
        sports=sports,
        report=build_research_report(
            analyses,
            athletes,
            current_user or User(name="Sports Scientist", email=""),
            injury_records,
            title=title,
        ),
        history=research_report_history(all_analyses, current_user.name if current_user else "Sports Scientist"),
    )


@router.get("/research-reports/pdf")
def download_research_report_pdf(
    sport: str | None = Query(default=None),
    athlete_ids: list[UUID] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    analysis_id: UUID | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    title: str | None = Query(default=None),
    profile: ProfessionalProfile = Depends(get_verified_sports_scientist_profile),
    db: Session = Depends(get_db),
):
    athletes, analyses, injury_records = research_report_scope(
        db, profile, sport, athlete_ids, start_date, end_date, analysis_id, risk_level
    )
    if not analyses:
        raise HTTPException(status_code=400, detail="No completed analyses match this report scope")
    current_user = db.query(User).filter(User.user_id == profile.user_id).first()
    report = build_research_report(
        analyses,
        athletes,
        current_user or User(name="Sports Scientist", email=""),
        injury_records,
        title=title,
    )
    pdf_bytes = generate_research_report_pdf(report)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sports_scientist_research_report.pdf"},
    )
