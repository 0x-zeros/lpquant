from app.research.benchmarks import BASELINE_CASES, default_baseline_cases


def test_default_baseline_cases_cover_expected_pairs_and_horizons():
    cases = default_baseline_cases()

    assert len(cases) == 12
    assert cases == BASELINE_CASES

    pairs = {case.request.pair for case in cases}
    assert pairs == {"BTC/USDC", "SOL/USDC", "SUI/USDC"}

    pair_intervals = {(case.request.pair, case.request.interval) for case in cases}
    assert ("BTC/USDC", "4h") in pair_intervals
    assert ("BTC/USDC", "1d") in pair_intervals
    assert ("SOL/USDC", "4h") in pair_intervals
    assert ("SUI/USDC", "4h") in pair_intervals

    scenario_suffixes = {case.name.split("_", 3)[-1] for case in cases}
    assert scenario_suffixes == {
        "neutral_balanced",
        "bullish_carry",
        "bearish_defensive",
    }
