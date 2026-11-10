
from fastapi import APIRouter, HTTPException
from kubernetes.client.exceptions import ApiException

from app.services.kubernetes import (
    KubernetesUnavailableError,
    get_cluster_nodes,
    get_cluster_overview,
    get_cluster_pods,
)


router = APIRouter(
    prefix="/api/v1/cluster",
    tags=["Kubernetes Cluster"],
)


def handle_kubernetes_error(exc: Exception):
    """将 Kubernetes 连接或 API 错误转换为 HTTP 503。"""
    if isinstance(exc, KubernetesUnavailableError):
        detail = str(exc)
    elif isinstance(exc, ApiException):
        detail = (
            f"Kubernetes API request failed: "
            f"{exc.reason or 'Unknown error'}"
        )
    else:
        raise exc

    raise HTTPException(
        status_code=503,
        detail=detail,
    ) from exc


# 集群概览
@router.get("/overview")
def cluster_overview():
    try:
        return get_cluster_overview()
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# 节点列表
@router.get("/nodes")
def cluster_nodes():
    try:
        return get_cluster_nodes()
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# Pod 列表
@router.get("/pods")
def cluster_pods():
    try:
        return get_cluster_pods()
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)
