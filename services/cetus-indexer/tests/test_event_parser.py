from cetus_indexer.event_parser import (
    PoolInfo,
    sqrt_price_x64_to_price,
    parse_swap_event,
)

POOL_ID = "0xtest_pool"


def test_sqrt_price_x64_to_price_sui_usdc():
    """Test raw price conversion: coin_a=SUI(9), coin_b=USDC(6) → price ~3.50."""
    sqrt_price = 0.05916079783099616 * (2**64)
    price = sqrt_price_x64_to_price(int(sqrt_price), 9, 6)
    assert abs(price - 3.50) < 0.01, f"Expected ~3.50, got {price}"


def test_sqrt_price_x64_to_price_identity():
    """When decimals are equal and sqrtPrice=1, price should be 1."""
    sqrt_price_x64 = 2**64
    price = sqrt_price_x64_to_price(sqrt_price_x64, 6, 6)
    assert abs(price - 1.0) < 1e-10


def test_sqrt_price_x64_inverted():
    """For USDC(6)/SUI(9) pool, raw price ≈0.286, inverted ≈3.50."""
    # 1 USDC ≈ 0.286 SUI when SUI=$3.50
    # sqrtPrice = sqrt(0.286 / 10^(6-9)) = sqrt(286) ≈ 16.91
    sqrt_val = 16.911534525 * (2**64)
    raw = sqrt_price_x64_to_price(int(sqrt_val), 6, 9)
    assert abs(raw - 0.286) < 0.01, f"Raw should be ~0.286, got {raw}"
    inverted = 1.0 / raw
    assert abs(inverted - 3.50) < 0.1, f"Inverted should be ~3.50, got {inverted}"


def test_parse_swap_event_no_invert():
    """Pool without price inversion."""
    sqrt_price = int(0.05916079783099616 * (2**64))
    event_node = {
        "json": {
            "pool": POOL_ID,
            "atob": True,
            "amount_in": "1000000000",
            "amount_out": "3500000",
            "after_sqrt_price": str(sqrt_price),
            "before_sqrt_price": str(sqrt_price),
            "fee_amount": "3000000",
            "steps": "1",
        },
        "txDigest": "abc123",
        "eventSeq": 0,
        "timestamp": 1700000000000,
    }

    configs = {POOL_ID: PoolInfo(decimals_a=9, decimals_b=6, invert_price=False)}
    record = parse_swap_event(event_node, configs)

    assert record is not None
    assert abs(record.price - 3.50) < 0.01


def test_parse_swap_event_with_invert():
    """Pool with price inversion (USDC/SUI → display as SUI price)."""
    # sqrtPriceX64 for USDC/SUI pool where SUI≈$1.80
    # raw price (USDC in SUI) ≈ 0.555, inverted ≈ 1.80
    sqrt_val = int(23.57 * (2**64))
    event_node = {
        "json": {
            "pool": POOL_ID,
            "atob": True,
            "amount_in": "18000000",
            "amount_out": "10000000000",
            "after_sqrt_price": str(sqrt_val),
            "before_sqrt_price": str(sqrt_val),
            "fee_amount": "54000",
            "steps": "1",
        },
        "txDigest": "inv_tx",
        "eventSeq": 0,
        "timestamp": 1700000000000,
    }

    configs = {POOL_ID: PoolInfo(decimals_a=6, decimals_b=9, invert_price=True)}
    record = parse_swap_event(event_node, configs)

    assert record is not None
    assert record.price > 1.0, f"Inverted price should be >1, got {record.price}"
    assert abs(record.price - 1.80) < 0.1


def test_parse_swap_event_unknown_pool():
    event_node = {
        "json": {
            "pool": "0xunknown",
            "atob": True,
            "amount_in": "1000",
            "amount_out": "500",
            "after_sqrt_price": "1000000000000000000",
            "before_sqrt_price": "1000000000000000000",
            "fee_amount": "10",
            "steps": "1",
        },
        "txDigest": "xyz",
        "eventSeq": 0,
        "timestamp": 0,
    }

    record = parse_swap_event(event_node, {})
    assert record is None


def test_parse_swap_event_btoa_volumes():
    """B→A direction: volume_a from amount_out, volume_b from amount_in."""
    sqrt_price = int(0.05916079783099616 * (2**64))
    event_node = {
        "json": {
            "pool": POOL_ID,
            "atob": False,
            "amount_in": "7000000",  # 7 USDC in (coin B)
            "amount_out": "2000000000",  # 2 SUI out (coin A)
            "after_sqrt_price": str(sqrt_price),
            "before_sqrt_price": str(sqrt_price),
            "fee_amount": "21000",
            "steps": "1",
        },
        "txDigest": "btoa_tx",
        "eventSeq": 1,
        "timestamp": 1700000000000,
    }

    configs = {POOL_ID: PoolInfo(decimals_a=9, decimals_b=6)}
    record = parse_swap_event(event_node, configs)

    assert record is not None
    assert record.atob is False
    assert abs(record.volume_a - 2.0) < 0.001
    assert abs(record.volume_b - 7.0) < 0.001
