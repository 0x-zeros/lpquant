from pathlib import Path

GRAPHQL_URL = "https://graphql.mainnet.sui.io/graphql"

CETUS_CLMM_PKG = (
    "0x1eabed72c53feb3805120a081dc15963c204dc8d091542592abaf7a35689b2fb"
)

SWAP_EVENT_TYPE = f"{CETUS_CLMM_PKG}::pool::SwapEvent"

DB_PATH = Path(__file__).parent.parent / "data" / "cetus_events.db"

# Known pool configurations (avoids on-chain queries for decimals)
# Pool type format: Pool<CoinA, CoinB>
# sqrtPriceX64 → price gives CoinA per CoinB (raw token units adjusted by decimals)
# invert_price: if True, display price as 1/price (e.g., show SUI in USDC instead of USDC in SUI)
KNOWN_POOLS: dict[str, dict] = {
    # USDC/SUI tick_spacing=60 (main LP pool)
    "0xb8d7d9e66a60c239e7a60110efcf8de6c705580ed924d0dde141f4a0e2c90105": {
        "symbol": "SUI/USDC",
        "coin_a": "USDC",
        "coin_b": "SUI",
        "decimals_a": 6,
        "decimals_b": 9,
        "tick_spacing": 60,
        "invert_price": True,  # display as SUI price in USDC
    },
    # USDC/SUI tick_spacing=10 (concentrated, most active)
    "0x51e883ba7c0b566a26cbc8a94cd33eb0abd418a77cc1e60ad22fd9b1f29cd2ab": {
        "symbol": "SUI/USDC-10",
        "coin_a": "USDC",
        "coin_b": "SUI",
        "decimals_a": 6,
        "decimals_b": 9,
        "tick_spacing": 10,
        "invert_price": True,
    },
    # wUSDC/SUI tick_spacing=60 (legacy wrapped USDC)
    "0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd371de688630": {
        "symbol": "SUI/wUSDC",
        "coin_a": "wUSDC",
        "coin_b": "SUI",
        "decimals_a": 6,
        "decimals_b": 9,
        "tick_spacing": 60,
        "invert_price": True,
    },
}

# Default polling interval in seconds
POLL_INTERVAL = 60

# GraphQL page size
PAGE_SIZE = 50
