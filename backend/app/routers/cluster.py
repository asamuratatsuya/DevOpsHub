
from fastapi import APIRouter, HTTPException
from kubernetes.client.exceptions import ApiException

from app.services.kubernetes import (
    KubernetesUnavailableError,
    get_cluster_node,
    get_cluster_nodes,
    get_cluster_overview,
    get_cluster_pods,
)


router = APIRouter(
    prefix="/api/v1/cluster",
    tags=["Kubernetes Cluster"],
)


def handle_kubernetes_error(exc: Exception):
    """将 Kubernetes 连接或 API 错误转换为 HTTP 错误。"""
    if isinstance(exc, KubernetesUnavailableError):
        status_code = 503
        detail = str(exc)

    elif isinstance(exc, ApiException):
        if exc.status == 404:
            status_code = 404
            detail = "Node not found"
        elif exc.status == 403:
            status_code = 403
            detail = "Permission denied by Kubernetes RBAC"
        else:
            status_code = 503
            detail = (
                f"Kubernetes API request failed: "
                f"{exc.reason or 'Unknown error'}"
            )
    else:
        raise exc

    raise HTTPException(
        status_code=status_code,
        detail=detail,
    ) from exc


# 集群概览
@router.get("/overview")
def cluster_overview():
    try:
        return get_cluster_overview()
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# Node 详情
@router.get("/nodes/{node_name}")
def cluster_node_detail(node_name: str):
    try:
        return get_cluster_node(node_name)
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)

# node列表
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
