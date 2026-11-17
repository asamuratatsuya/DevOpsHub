
import { http } from "@/utils/http";

export interface Deployment {
  name: string;
  namespace: string;
  replicas: {
    desired: number;
    current: number;
    updated: number;
    ready: number;
    available: number;
  };
  strategy: string | null;
  images: string[];
  selector: Record<string, string>;
  generation: number;
  observed_generation: number | null;
  conditions: {
    type: string;
    status: string;
    reason: string | null;
    message: string | null;
  }[];
  created_at: string | null;
}

export interface ClusterPod {
  name: string;
  namespace: string;
  status: string;
  node_name: string | null;
  pod_ip: string | null;
  restart_count: number;
  ready_containers: number;
  total_containers: number;
  created_at: string | null;
}

export interface PodDetail extends ClusterPod {
  host_ip: string | null;
  containers: {
    name: string;
    image: string;
    ready: boolean;
    restart_count: number;
    state: string;
    state_reason: string | null;
  }[];
  owners: {
    kind: string;
    name: string;
  }[];
}

export function getDeploymentList(namespace?: string) {
  return http.get<Deployment[], unknown>("/api/v1/deployments", {
    params: namespace ? { namespace } : {}
  });
}

export function getDeploymentDetail(namespace: string, name: string) {
  return http.get<Deployment, unknown>(
    `/api/v1/deployments/${namespace}/${name}`
  );
}

export function scaleDeployment(
  namespace: string,
  name: string,
  replicas: number
) {
  return http.request<{ name: string; namespace: string; replicas: number }>(
    "patch",
    `/api/v1/deployments/${namespace}/${name}/scale`,
    { data: { replicas } }
  );
}

export function restartDeployment(namespace: string, name: string) {
  return http.post(
    `/api/v1/deployments/${namespace}/${name}/restart`
  );
}

export function getClusterPodList() {
  return http.get<ClusterPod[], unknown>("/api/v1/cluster/pods");
}

export function getPodDetail(namespace: string, name: string) {
  return http.get<PodDetail, unknown>(
    `/api/v1/pods/${namespace}/${name}`
  );
}

export function getPodLogs(namespace: string, name: string) {
  return http.get<string, unknown>(
    `/api/v1/pods/${namespace}/${name}/logs`
  );
}
