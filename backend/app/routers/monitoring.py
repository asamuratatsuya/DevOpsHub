import asyncio
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings


router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["Monitoring"],
)

# 集群 CPU 总体使用率，按 CPU 核心数量加权
CPU_QUERY = """
100 * (
    1 - sum(rate(node_cpu_seconds_total{mode="idle"}[5m]))
    / count(node_cpu_seconds_total{mode="idle"})
)
"""

# 集群内存总体使用率，按内存容量加权
MEMORY_QUERY = """
100 * (
    1 - sum(node_memory_MemAvailable_bytes)
    / sum(node_memory_MemTotal_bytes)
)
"""

RANGE_OPTIONS = {
    "15m": (timedelta(minutes=15), 60),
    "1h": (timedelta(hours=1), 60),
    "6h": (timedelta(hours=6), 300),
    "24h": (timedelta(hours=24), 600),
}


async def query_prometheus(
    client: httpx.AsyncClient,
    expression: str,
    start: float,
    end: float,
    step: int,
):
    """调用 Prometheus 的区间查询 API。"""
    url = f"{settings.PROMETHEUS_URL.rstrip('/')}/api/v1/query_range"

    try:
        response = await client.get(
            url,
            params={
                "query": expression,
                "start": start,
                "end": end,
                "step": f"{step}s",
            },
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Prometheus query timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Prometheus",
        ) from exc

    if not response.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"Prometheus returned HTTP {response.status_code}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Prometheus returned an invalid response",
        ) from exc

    if payload.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail="Prometheus query failed",
        )

    return payload.get("data", {}).get("result", [])


def extract_points(results: list):
    """将 Prometheus 时间序列转换为前端图表数据。"""
    if not results:
        return []

    values = results[0].get("values", [])

    return [
        {
            "timestamp": float(timestamp),
            "value": round(float(value), 2),
        }
        for timestamp, value in values
    ]


@router.get("/overview")
async def monitoring_overview(
    range_name: Literal["15m", "1h", "6h", "24h"] = Query(
        default="1h",
        alias="range",
    ),
):
    """获取集群 CPU、内存使用率及历史趋势。"""
    duration, step = RANGE_OPTIONS[range_name]

    end = datetime.now(timezone.utc).timestamp()
    start = (datetime.now(timezone.utc) - duration).timestamp()

    async with httpx.AsyncClient(timeout=15.0) as client:
        cpu_result, memory_result = await asyncio.gather(
            query_prometheus(
                client, CPU_QUERY, start, end, step
            ),
            query_prometheus(
                client, MEMORY_QUERY, start, end, step
            ),
        )

    cpu_points = extract_points(cpu_result)
    memory_points = extract_points(memory_result)

    return {
        "range": range_name,
        "updated_at": end,
        "cpu": {
            "current": (
                cpu_points[-1]["value"] if cpu_points else None
            ),
            "unit": "percent",
            "points": cpu_points,
        },
        "memory": {
            "current": (
                memory_points[-1]["value"] if memory_points else None
            ),
            "unit": "percent",
            "points": memory_points,
        },
    }
