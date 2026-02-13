from __future__ import annotations

import httpx

from .config import GRAPHQL_URL, SWAP_EVENT_TYPE, PAGE_SIZE

EVENTS_QUERY = """
query SwapEvents($eventType: String!, $after: String, $first: Int!) {
  events(
    filter: { type: $eventType }
    first: $first
    after: $after
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      contents {
        json
      }
      timestamp
      sequenceNumber
      transaction {
        digest
      }
    }
  }
}
"""


async def query_swap_events(
    after_cursor: str | None = None,
    limit: int = PAGE_SIZE,
    *,
    graphql_url: str = GRAPHQL_URL,
    event_type: str = SWAP_EVENT_TYPE,
) -> tuple[list[dict], str | None, bool]:
    """Query Cetus swap events from Sui GraphQL.

    Returns:
        (events, next_cursor, has_next_page)
        Each event dict has keys: json, txDigest, eventSeq, timestamp
    """
    variables = {
        "eventType": event_type,
        "first": limit,
    }
    if after_cursor:
        variables["after"] = after_cursor

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            graphql_url,
            json={"query": EVENTS_QUERY, "variables": variables},
        )
        resp.raise_for_status()
        data = resp.json()

    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    events_data = data["data"]["events"]
    page_info = events_data["pageInfo"]

    nodes = []
    for node in events_data["nodes"]:
        contents = node.get("contents") or {}
        parsed = {
            "json": contents.get("json", {}),
            "txDigest": (node.get("transaction") or {}).get("digest", ""),
            "eventSeq": node.get("sequenceNumber", 0),
            "timestamp": _parse_timestamp(node.get("timestamp")),
        }
        nodes.append(parsed)

    return (
        nodes,
        page_info.get("endCursor"),
        page_info.get("hasNextPage", False),
    )


def _parse_timestamp(ts: str | int | None) -> int:
    """Parse timestamp to epoch milliseconds.

    Sui GraphQL may return timestamps as epoch ms (int) or ISO 8601 strings.
    """
    if ts is None:
        return 0
    if isinstance(ts, int):
        return ts
    # Try numeric string first
    try:
        return int(ts)
    except ValueError:
        pass
    # Fall back to ISO 8601
    from datetime import datetime

    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)
