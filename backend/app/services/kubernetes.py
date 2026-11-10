
from functools import lru_cache

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


class KubernetesUnavailableError(RuntimeError):
    """Kubernetes configuration is unavailable."""


@lru_cache(maxsize=1)
def get_core_v1_api() -> client.CoreV1Api:
    """
    获取 Kubernetes CoreV1 API 客户端。

    优先使用集群内 ServiceAccount；
    本地开发环境则尝试使用 kubeconfig。
    """
    try:
        config.load_incluster_config()
    except ConfigException:
        try:
            config.load_kube_config()
        except ConfigException as exc:
            raise KubernetesUnavailableError(
                "Kubernetes configuration is unavailable"
            ) from exc

    return client.CoreV1Api()


def _get_node_status(node) -> str:
    """获取节点 Ready 状态。"""
    conditions = node.status.conditions or []

    for condition in conditions:
        if condition.type == "Ready":
            return "Ready" if condition.status == "True" else "NotReady"

    return "Unknown"


def _get_node_roles(node) -> list[str]:
    """获取节点角色。"""
    labels = node.metadata.labels or {}

    roles = [
        key.split("/", 1)[1]
        for key in labels
        if key.startswith("node-role.kubernetes.io/")
    ]

    return sorted(roles) if roles else ["worker"]


def get_cluster_overview() -> dict:
    """获取集群概览数据。"""
    api = get_core_v1_api()

    nodes = api.list_node().items
    pods = api.list_pod_for_all_namespaces().items

    node_ready_count = sum(
        1 for node in nodes if _get_node_status(node) == "Ready"
    )

    pod_status_counts = {
        "running": 0,
        "pending": 0,
        "failed": 0,
        "succeeded": 0,
        "unknown": 0,
    }

    for pod in pods:
        phase = (pod.status.phase or "Unknown").lower()
        if phase in pod_status_counts:
            pod_status_counts[phase] += 1
        else:
            pod_status_counts["unknown"] += 1

    return {
        "nodes": {
            "total": len(nodes),
            "ready": node_ready_count,
            "not_ready": len(nodes) - node_ready_count,
        },
        "pods": {
            "total": len(pods),
            **pod_status_counts,
        },
    }


def get_cluster_nodes() -> list[dict]:
    """获取集群节点列表。"""
    api = get_core_v1_api()
    nodes = api.list_node().items

    result = []

    for node in nodes:
        addresses = node.status.addresses or []
        internal_ip = next(
            (
                address.address
                for address in addresses
                if address.type == "InternalIP"
            ),
            None,
        )

        capacity = node.status.capacity or {}
        allocatable = node.status.allocatable or {}
        node_info = node.status.node_info

        result.append(
            {
                "name": node.metadata.name,
                "status": _get_node_status(node),
                "roles": _get_node_roles(node),
                "internal_ip": internal_ip,
                "kubelet_version": node_info.kubelet_version,
                "capacity": {
                    "cpu": capacity.get("cpu"),
                    "memory": capacity.get("memory"),
                },
                "allocatable": {
                    "cpu": allocatable.get("cpu"),
                    "memory": allocatable.get("memory"),
                },
            }
        )

    return sorted(result, key=lambda item: item["name"])


def get_cluster_pods() -> list[dict]:
    """获取所有命名空间中的 Pod 列表。"""
    api = get_core_v1_api()
    pods = api.list_pod_for_all_namespaces().items

    result = []

    for pod in pods:
        container_statuses = pod.status.container_statuses or []
        containers = pod.spec.containers or []

        restart_count = sum(
            status.restart_count or 0
            for status in container_statuses
        )

        ready_containers = sum(
            1 for status in container_statuses if status.ready
        )

        result.append(
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase or "Unknown",
                "node_name": pod.spec.node_name,
                "pod_ip": pod.status.pod_ip,
                "restart_count": restart_count,
                "ready_containers": ready_containers,
                "total_containers": len(containers),
                "created_at": (
                    pod.metadata.creation_timestamp.isoformat()
                    if pod.metadata.creation_timestamp
                    else None
                ),
            }
        )

    return sorted(
        result,
        key=lambda item: (item["namespace"], item["name"]),
    )
