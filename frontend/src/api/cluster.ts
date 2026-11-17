
import { http } from "@/utils/http";

/** 集群概览 */
export interface ClusterOverview {
  nodes: {
    total: number;
    ready: number;
    not_ready: number;
  };
  pods: {
    total: number;
    running: number;
    pending: number;
    failed: number;
    succeeded: number;
    unknown: number;
  };
}

/** Kubernetes 节点 */
export interface ClusterNode {
  name: string;
  status: string;
  roles: string[];
  internal_ip: string;
  kubelet_version: string;
  capacity: {
    cpu: string;
    memory: string;
  };
  allocatable: {
    cpu: string;
    memory: string;
  };
}

/** 获取集群概览 */
export function getClusterOverview() {
  return http.get<ClusterOverview, unknown>("/api/v1/cluster/overview");
}

/** 获取节点列表 */
export function getClusterNodes() {
  return http.get<ClusterNode[], unknown>("/api/v1/cluster/nodes");
}
