"""Concentrated-liquidity LP vs HODL back-test engine.

Simulates a Uniswap-v3 / Cetus CLMM position over a historical price series
and computes performance metrics + chart series data.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.schemas import BacktestMetrics


# ---------------------------------------------------------------------------
# Core concentrated-liquidity math helpers
# ---------------------------------------------------------------------------

def _compute_liquidity(capital: float, p0: float, pa: float, pb: float) -> float:
    """Derive liquidity *L* for a given capital and range [pa, pb].

    Assumes the position is opened at price *p0* which lies inside [pa, pb]
    and the capital is split so that the two token sides have equal USD value
    at the moment of entry.

    L = capital / (sqrt(P0) - sqrt(Pa) + P0 * (1/sqrt(P0) - 1/sqrt(Pb)))
    """
    sqrt_p0 = math.sqrt(p0)
    sqrt_pa = math.sqrt(pa)
    sqrt_pb = math.sqrt(pb)

    denominator = (sqrt_p0 - sqrt_pa) + p0 * (1.0 / sqrt_p0 - 1.0 / sqrt_pb)
    if denominator <= 0:
        # Fallback: if p0 is at the boundary the formula degenerates.
        # Use a rough approximation.
        denominator = 1e-18
    return capital / denominator


def _lp_value(L: float, price: float, pa: float, pb: float) -> float:
    """Compute the USD value of the LP position at a given *price*.

    Follows the standard CL formulas:
    - In range  [pa, pb]: x = L*(1/sqrt(P) - 1/sqrt(Pb)),  y = L*(sqrt(P) - sqrt(Pa))
    - Below pa: all token-X  => value = L * (1/sqrt(Pa) - 1/sqrt(Pb)) * P
    - Above pb: all token-Y  => value = L * (sqrt(Pb) - sqrt(Pa))
    """
    sqrt_pa = math.sqrt(pa)
    sqrt_pb = math.sqrt(pb)

    if price <= pa:
        # Entirely in token X
        x = L * (1.0 / sqrt_pa - 1.0 / sqrt_pb)
        return x * price
    elif price >= pb:
        # Entirely in token Y
        y = L * (sqrt_pb - sqrt_pa)
        return y
    else:
        sqrt_p = math.sqrt(price)
        x = L * (1.0 / sqrt_p - 1.0 / sqrt_pb)
        y = L * (sqrt_p - sqrt_pa)
        return x * price + y


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_backtest(
    closes: np.ndarray,
    timestamps: np.ndarray,
    pa: float,
    pb: float,
    p0: float,
    capital: float,
    fee_rate: float,
) -> dict[str, Any]:
    """Run an LP-vs-HODL back-test over the given price series.

    Parameters
    ----------
    closes : array of close prices
    timestamps : array of epoch-ms timestamps (same length as *closes*)
    pa, pb : lower / upper price bounds of the CL range
    p0 : price at position entry (first close or current_price)
    capital : initial capital in USD
    fee_rate : pool fee rate (e.g. 0.0025 for 25 bps) -- used for
        capital-efficiency metric but **not** for fee-accrual simulation
        (we keep the back-test conservative / fee-free so that the metrics
         reflect pure position performance).

    Returns
    -------
    dict with keys ``"metrics"`` (:class:`BacktestMetrics`) and
    ``"series"`` (lists of lp_values, hodl_values, il_pct, prices,
    timestamps).
    """
    n = len(closes)
    if n == 0:
        raise ValueError("closes array is empty")

    # Ensure pa < pb and both are positive
    pa = max(pa, 1e-18)
    pb = max(pb, pa + 1e-18)

    # Clamp p0 into range for liquidity calculation
    p0_clamped = max(min(p0, pb), pa)

    L = _compute_liquidity(capital, p0_clamped, pa, pb)

    # Pre-allocate series arrays
    lp_values = np.empty(n, dtype=np.float64)
    hodl_values = np.empty(n, dtype=np.float64)
    il_pct_arr = np.empty(n, dtype=np.float64)

    # HODL baseline: 50/50 split at entry price p0
    hodl_token_x = (capital / 2.0) / p0  # amount of token X
    hodl_token_y = capital / 2.0  # amount of token Y (stablecoin side)

    in_range_count = 0
    boundary_touches = 0
    prev_in_range: bool | None = None
    peak_lp = capital
    max_drawdown = 0.0
    max_il = 0.0

    for i in range(n):
        price = float(closes[i])

        # LP value
        lp_val = _lp_value(L, price, pa, pb)
        lp_values[i] = lp_val

        # HODL value
        hodl_val = hodl_token_x * price + hodl_token_y
        hodl_values[i] = hodl_val

        # IL = (LP - HODL) / HODL  (negative when LP under-performs)
        if hodl_val > 0:
            il = (lp_val - hodl_val) / hodl_val * 100.0
        else:
            il = 0.0
        il_pct_arr[i] = il

        # Track max IL (most negative value)
        if il < max_il:
            max_il = il

        # Drawdown from LP peak
        if lp_val > peak_lp:
            peak_lp = lp_val
        dd = (peak_lp - lp_val) / peak_lp * 100.0 if peak_lp > 0 else 0.0
        if dd > max_drawdown:
            max_drawdown = dd

        # In-range tracking
        currently_in_range = pa <= price <= pb
        if currently_in_range:
            in_range_count += 1
        # Boundary touch: transition from in-range to out-of-range or vice-versa
        if prev_in_range is not None and currently_in_range != prev_in_range:
            boundary_touches += 1
        prev_in_range = currently_in_range

    in_range_pct = (in_range_count / n) * 100.0 if n > 0 else 0.0

    # LP vs HODL pct (final values)
    final_lp = float(lp_values[-1])
    final_hodl = float(hodl_values[-1])
    lp_vs_hodl_pct = (
        ((final_lp - final_hodl) / final_hodl * 100.0) if final_hodl > 0 else 0.0
    )

    # Capital efficiency: ratio of the narrow-range liquidity to the
    # equivalent full-range liquidity.  Approximated as sqrt(pb/pa).
    capital_efficiency = math.sqrt(pb / pa) if pa > 0 else 1.0

    metrics = BacktestMetrics(
        in_range_pct=round(in_range_pct, 2),
        lp_vs_hodl_pct=round(lp_vs_hodl_pct, 2),
        max_il_pct=round(abs(max_il), 2),  # report as positive number
        max_drawdown_pct=round(max_drawdown, 2),
        capital_efficiency=round(capital_efficiency, 2),
        boundary_touches=boundary_touches,
    )

    series = {
        "timestamps": timestamps.astype(int).tolist(),
        "lp_values": np.round(lp_values, 4).tolist(),
        "hodl_values": np.round(hodl_values, 4).tolist(),
        "il_pct": np.round(il_pct_arr, 4).tolist(),
        "prices": closes.tolist(),
    }

    return {"metrics": metrics, "series": series}
