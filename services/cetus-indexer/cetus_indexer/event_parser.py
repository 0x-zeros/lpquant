from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SwapRecord:
    tx_digest: str
    event_seq: int
    pool_id: str
    timestamp_ms: int
    price: float
    volume_a: float
    volume_b: float
    atob: bool
    sqrt_price_x64: str


@dataclass(frozen=True, slots=True)
class PoolInfo:
    """Pool decimals and price configuration."""

    decimals_a: int
    decimals_b: int
    invert_price: bool = False


def sqrt_price_x64_to_price(
    sqrt_price_x64: int,
    decimals_a: int,
    decimals_b: int,
) -> float:
    """Convert Cetus sqrtPriceX64 to human-readable price.

    Returns price of coin_a in terms of coin_b:
    price = (sqrtPriceX64 / 2^64)^2 * 10^(decimalsA - decimalsB)
    """
    sqrt_price = sqrt_price_x64 / (2**64)
    return sqrt_price**2 * (10 ** (decimals_a - decimals_b))


def parse_swap_event(
    event_node: dict,
    pool_configs: dict[str, PoolInfo],
) -> SwapRecord | None:
    """Parse a GraphQL event node into a SwapRecord.

    Args:
        event_node: A node from the GraphQL events query.
        pool_configs: Mapping of pool_id → PoolInfo.

    Returns:
        SwapRecord or None if the pool is unknown.
    """
    json_data = event_node.get("json") or {}
    pool_id = json_data.get("pool")
    if not pool_id:
        return None

    # Normalize pool_id to full 0x-prefixed hex
    if not pool_id.startswith("0x"):
        pool_id = "0x" + pool_id

    info = pool_configs.get(pool_id)
    if info is None:
        return None

    after_sqrt_price = int(json_data["after_sqrt_price"])
    price = sqrt_price_x64_to_price(
        after_sqrt_price, info.decimals_a, info.decimals_b
    )
    if info.invert_price and price > 0:
        price = 1.0 / price

    amount_in = int(json_data["amount_in"])
    amount_out = int(json_data["amount_out"])
    atob = json_data["atob"]

    # Compute human-readable volumes
    if atob:
        volume_a = amount_in / (10**info.decimals_a)
        volume_b = amount_out / (10**info.decimals_b)
    else:
        volume_a = amount_out / (10**info.decimals_a)
        volume_b = amount_in / (10**info.decimals_b)

    tx_digest = event_node.get("txDigest", "")
    event_seq = int(event_node.get("eventSeq", 0))
    timestamp_ms = int(event_node.get("timestamp", 0))

    return SwapRecord(
        tx_digest=tx_digest,
        event_seq=event_seq,
        pool_id=pool_id,
        timestamp_ms=timestamp_ms,
        price=price,
        volume_a=volume_a,
        volume_b=volume_b,
        atob=atob,
        sqrt_price_x64=str(after_sqrt_price),
    )
