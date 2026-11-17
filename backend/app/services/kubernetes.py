
from functools import lru_cache

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from datetime import datetime, timezone


class KubernetesUnavailableError(RuntimeError):
    """Kubernetes configuration is unavailable."""


@lru_cache(maxsize=1)
def _load_kubernetes_config() -> None:
    """加载 Kubernetes 配置，优先使用集群内 ServiceAccount。"""
    try:
        config.load_incluster_config()
    except ConfigException:
        try:
            config.load_kube_config()
        except ConfigException as exc:
            raise KubernetesUnavailableError(
                "Kubernetes configuration is unavailable"
            ) from exc


@lru_cache(maxsize=1)
def get_core_v1_api() -> client.CoreV1Api:
    _load_kubernetes_config()
    return client.CoreV1Api()


@lru_cache(maxsize=1)
def get_apps_v1_api() -> client.AppsV1Api:
    _load_kubernetes_config()
    return client.AppsV1Api()


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

def _format_deployment(deployment) -> dict:
    """整理 Deployment 信息。"""
    spec = deployment.spec
    status = deployment.status

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": {
            "desired": spec.replicas or 0,
            "current": status.replicas or 0,
            "updated": status.updated_replicas or 0,
            "ready": status.ready_replicas or 0,
            "available": status.available_replicas or 0,
        },
        "strategy": (
            spec.strategy.type
            if spec.strategy
            else None
        ),
        "images": [
            container.image
            for container in (spec.template.spec.containers or [])
        ],
        "selector": (
            spec.selector.match_labels or {}
            if spec.selector
            else {}
        ),
        "generation": deployment.metadata.generation,
        "observed_generation": status.observed_generation,
        "conditions": [
            {
                "type": condition.type,
                "status": condition.status,
                "reason": condition.reason,
                "message": condition.message,
            }
            for condition in (status.conditions or [])
        ],
        "created_at": (
            deployment.metadata.creation_timestamp.isoformat()
            if deployment.metadata.creation_timestamp
            else None
        ),
    }


def get_deployments(namespace: str | None = None) -> list[dict]:
    """获取 Deployment 列表，可按 namespace 筛选。"""
    api = get_apps_v1_api()

    if namespace:
        deployments = api.list_namespaced_deployment(
            namespace=namespace
        ).items
    else:
        deployments = api.list_deployment_for_all_namespaces().items

    result = [_format_deployment(item) for item in deployments]

    return sorted(
        result,
        key=lambda item: (item["namespace"], item["name"]),
    )


def get_deployment(namespace: str, name: str) -> dict:
    """获取指定 Deployment 的详情。"""
    api = get_apps_v1_api()

    deployment = api.read_namespaced_deployment(
        name=name,
        namespace=namespace,
    )

    return _format_deployment(deployment)

 
def scale_deployment(
    namespace: str,
    name: str,
    replicas: int,
) -> dict:
    """调整 Deployment 副本数。"""
    api = get_apps_v1_api()

    deployment = api.patch_namespaced_deployment_scale(
        name=name,
        namespace=namespace,
        body={
            "spec": {
                "replicas": replicas,
            }
        },
    )

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
    }


def restart_deployment(namespace: str, name: str) -> dict:
    """触发 Deployment 滚动重启。"""
    api = get_apps_v1_api()

    restarted_at = datetime.now(timezone.utc).isoformat()

    deployment = api.patch_namespaced_deployment(
        name=name,
        namespace=namespace,
        body={
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": restarted_at,
                        }
                    }
                }
            }
        },
    )

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "restarted_at": restarted_at,
        "message": "Deployment restart triggered",
    }


def get_pod_detail(namespace: str, name: str) -> dict:
    """获取指定 Pod 的详细信息。"""
    api = get_core_v1_api()
    pod = api.read_namespaced_pod(
        name=name,
        namespace=namespace,
    )

    container_statuses = {
        item.name: item
        for item in (pod.status.container_statuses or [])
    }

    containers = []

    for container in (pod.spec.containers or []):
        status = container_statuses.get(container.name)

        state = "Unknown"
        state_reason = None

        if status and status.state:
            if status.state.running:
                state = "Running"
            elif status.state.waiting:
                state = "Waiting"
                state_reason = status.state.waiting.reason
            elif status.state.terminated:
                state = "Terminated"
                state_reason = status.state.terminated.reason

        containers.append({
            "name": container.name,
            "image": container.image,
            "ready": status.ready if status else False,
            "restart_count": status.restart_count if status else 0,
            "state": state,
            "state_reason": state_reason,
        })

    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "status": pod.status.phase or "Unknown",
        "pod_ip": pod.status.pod_ip,
        "host_ip": pod.status.host_ip,
        "node_name": pod.spec.node_name,
        "restart_count": sum(
            item.restart_count or 0
            for item in container_statuses.values()
        ),
        "ready_containers": sum(
            1 for item in container_statuses.values() if item.ready
        ),
        "total_containers": len(containers),
        "containers": containers,
        "owners": [
            {
                "kind": owner.kind,
                "name": owner.name,
            }
            for owner in (pod.metadata.owner_references or [])
        ],
        "created_at": (
            pod.metadata.creation_timestamp.isoformat()
            if pod.metadata.creation_timestamp
            else None
        ),
    }


def get_pod_logs(
    namespace: str,
    name: str,
    container: str | None = None,
    tail_lines: int = 100,
    timestamps: bool = True,
) -> str:
    """获取指定 Pod 的容器日志。"""
    api = get_core_v1_api()

    return api.read_namespaced_pod_log(
        name=name,
        namespace=namespace,
        container=container,
        tail_lines=tail_lines,
        timestamps=timestamps,
    )


def get_cluster_node(name: str) -> dict:
    """获取指定 Kubernetes 节点的详细信息。"""
    api = get_core_v1_api()
    node = api.read_node(name=name)

    node_status = node.status
    node_info = node_status.node_info
    spec = node.spec

    addresses = node_status.addresses or []
    capacity = node_status.capacity or {}
    allocatable = node_status.allocatable or {}

    internal_ip = next(
        (
            item.address
            for item in addresses
            if item.type == "InternalIP"
        ),
        None,
    )

    external_ip = next(
        (
            item.address
            for item in addresses
            if item.type == "ExternalIP"
        ),
        None,
    )

    def format_conditions():
        result = []

        for condition in (node_status.conditions or []):
            result.append({
                "type": condition.type,
                "status": condition.status,
                "reason": condition.reason,
                "message": condition.message,
                "last_heartbeat_time": (
                    condition.last_heartbeat_time.isoformat()
                    if condition.last_heartbeat_time else None
                ),
                "last_transition_time": (
                    condition.last_transition_time.isoformat()
                    if condition.last_transition_time else None
                ),
            })

        return result

    return {
        "name": node.metadata.name,
        "status": _get_node_status(node),
        "roles": _get_node_roles(node),
        "addresses": [
            {
                "type": item.type,
                "address": item.address,
            }
            for item in addresses
        ],
        "internal_ip": internal_ip,
        "external_ip": external_ip,
        "kubernetes": {
            "kubelet_version": (
                node_info.kubelet_version if node_info else None
            ),
            "kube_proxy_version": (
                node_info.kube_proxy_version if node_info else None
            ),
            "container_runtime_version": (
                node_info.container_runtime_version if node_info else None
            ),
            "os_image": node_info.os_image if node_info else None,
            "operating_system": (
                node_info.operating_system if node_info else None
            ),
            "architecture": (
                node_info.architecture if node_info else None
            ),
            "kernel_version": (
                node_info.kernel_version if node_info else None
            ),
        },
        "capacity": {
            "cpu": capacity.get("cpu"),
            "memory": capacity.get("memory"),
            "pods": capacity.get("pods"),
            "ephemeral_storage": capacity.get("ephemeral-storage"),
        },
        "allocatable": {
            "cpu": allocatable.get("cpu"),
            "memory": allocatable.get("memory"),
            "pods": allocatable.get("pods"),
            "ephemeral_storage": allocatable.get("ephemeral-storage"),
        },
        "unschedulable": spec.unschedulable or False,
        "taints": [
            {
                "key": item.key,
                "value": item.value,
                "effect": item.effect,
            }
            for item in (spec.taints or [])
        ],
        "conditions": format_conditions(),
        "created_at": (
            node.metadata.creation_timestamp.isoformat()
            if node.metadata.creation_timestamp
            else None
        ),
    }

