from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from kubernetes.client.exceptions import ApiException

from app.services.kubernetes import (
    KubernetesUnavailableError,
    get_deployment,
    get_deployments,
    scale_deployment,
    restart_deployment,
)


router = APIRouter(
    prefix="/api/v1/deployments",
    tags=["Kubernetes Deployments"],
)


class ScaleRequest(BaseModel):
    replicas: int = Field(ge=0, le=10)


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
                detail="Deployment not found",
            ) from exc

        if exc.status == 403:
            raise HTTPException(
                status_code=403,
                detail="Permission denied by Kubernetes RBAC",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail=f"Kubernetes API request failed: "
                   f"{exc.reason or 'Unknown error'}",
        ) from exc

    raise exc


# Deployment 列表
@router.get("")
def deployment_list(
    namespace: str | None = Query(default=None, min_length=1),
):
    try:
        return get_deployments(namespace)
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# Deployment 详情
@router.get("/{namespace}/{deployment_name}")
def deployment_detail(namespace: str, deployment_name: str):
    try:
        return get_deployment(namespace, deployment_name)
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)



# Deployment 副本数调整
@router.patch("/{namespace}/{deployment_name}/scale")
def deployment_scale(
    namespace: str,
    deployment_name: str,
    request: ScaleRequest,
):
    try:
        return scale_deployment(
            namespace,
            deployment_name,
            request.replicas,
        )
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)


# Deployment 滚动重启
@router.post("/{namespace}/{deployment_name}/restart")
def deployment_restart(namespace: str, deployment_name: str):
    try:
        return restart_deployment(namespace, deployment_name)
    except (KubernetesUnavailableError, ApiException) as exc:
        handle_kubernetes_error(exc)
