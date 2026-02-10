import math


def price_to_tick(price: float) -> int:
    """Convert price to tick index.

    Uses the Uniswap v3 / Cetus CLMM convention: tick = floor(log(price) / log(1.0001)).
    """
    if price <= 0:
        raise ValueError("price must be positive")
    return math.floor(math.log(price) / math.log(1.0001))


def tick_to_price(tick: int) -> float:
    """Convert tick index to price."""
    return 1.0001 ** tick


def align_tick_down(tick: int, spacing: int) -> int:
    """Align tick down to nearest spacing multiple.

    For negative ticks this rounds towards negative infinity.
    """
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    # Python's floor division naturally rounds toward negative infinity,
    # which is the correct behaviour for aligning down.
    return (tick // spacing) * spacing


def align_tick_up(tick: int, spacing: int) -> int:
    """Align tick up to nearest spacing multiple.

    For positive ticks this rounds towards positive infinity.
    """
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    if tick % spacing == 0:
        return tick
    # For both positive and negative ticks we want the next multiple
    # of spacing that is >= tick.
    return ((tick // spacing) + 1) * spacing
