from __future__ import annotations

from app.research.features import (
    build_feature_frame,
    describe_current_regime,
    select_similar_windows,
)
from app.research.market_data import load_price_history
from app.research.optimizer import evaluate_candidates
from app.research.types import StudyRequest, StudyResult


def run_study(request: StudyRequest) -> StudyResult:
    dataset = load_price_history(
        raw_pair=request.pair,
        interval=request.interval,
        days=request.days,
    )

    min_rows = request.lookback_bars + request.horizon_bars + max(request.neighbors, 20)
    if len(dataset.frame) < min_rows:
        raise ValueError(
            f"not enough bars for this study: got {len(dataset.frame)}, need about {min_rows}; "
            "increase --days or lower lookback/horizon/neighbors"
        )

    feature_frame = build_feature_frame(
        frame=dataset.frame,
        lookback_bars=request.lookback_bars,
        interval=request.interval,
    )
    current_regime = describe_current_regime(feature_frame)
    similar_windows = select_similar_windows(
        feature_frame=feature_frame,
        horizon_bars=request.horizon_bars,
        neighbors=request.neighbors,
    )
    rankings = evaluate_candidates(
        frame=dataset.frame,
        similar_windows=similar_windows,
        interval=request.interval,
        horizon_bars=request.horizon_bars,
        capital=request.capital,
        fee_rate=request.fee_rate,
        view=request.view,
        objective=request.objective,
    )

    return StudyResult(
        request=request,
        dataset=dataset,
        feature_frame=feature_frame,
        current_regime=current_regime,
        similar_windows=similar_windows,
        rankings=rankings,
    )
