
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from kubernetes.client.exceptions import ApiException

from app.services.kubernetes import (
    KubernetesUnavailableError,
    get_pod_detail,
    get_pod_logs,
)


router = APIRouter(
    prefix="/api/v1/pods",
    tags=["Kubernetes Pods"],
)


def handle_kubernetes_error(exc: Exception):
    """将 Kubernetes API 错误转换为 HTTP 错误。"""
    if isinstance(exc, KubernetesUnavailableError):
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ApiException):
        if exc.status == 404:
            raise HTTPException(
                status_code=404,
                detail="Pod not found",
            ) from exc

        if exc.status == 403:
            raise HTTPException(
                status_code=403,
                detail="Permission denied by Kubernetes RBAC",
            ) from exc

        if exc.status == 400:
            raise HTTPException(
                status_code=400,
                detail=exc.reason or "Invalid Kubernetes API request",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail=f"Kubernetes API request failed: "
                   f"{exc.reason or 'Unknown error'}",
        ) from exc

    raise exc


# Pod 详情
@router.get("/{namespace}/{pod_name}")
def pod_detail(namespace: str, pod_name: str):
    try:
        return get_pod_detail(namespace, pod_name)
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# Pod 日志
@router.get(
    "/{namespace}/{pod_name}/logs",
    response_class=PlainTextResponse,
)
def pod_logs(
    namespace: str,
    pod_name: str,
    container: str | None = Query(default=None, min_length=1),
    tail_lines: int = Query(default=100, ge=1, le=1000),
    timestamps: bool = Query(default=True),
):
    try:
        logs = get_pod_logs(
            namespace=namespace,
            name=pod_name,
            container=container,
            tail_lines=tail_lines,
            timestamps=timestamps,
        )
        return PlainTextResponse(
            content=logs,
            media_type="text/plain; charset=utf-8",
        )
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)
