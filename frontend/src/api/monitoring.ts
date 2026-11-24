import { http } from "@/utils/http";

export type MonitoringRange = "15m" | "1h" | "6h" | "24h";

export interface MonitoringPoint {
  timestamp: number;
  value: number;
}

export interface MonitoringMetric {
  current: number | null;
  unit: string;
  points: MonitoringPoint[];
}

export interface MonitoringOverview {
  range: MonitoringRange;
  updated_at: number;
  cpu: MonitoringMetric;
  memory: MonitoringMetric;
}

/** 获取集群监控数据 */
export function getMonitoringOverview(range: MonitoringRange = "1h") {
  return http.get<MonitoringOverview, unknown>(
    "/api/v1/monitoring/overview",
    {
      params: { range }
    }
  );
}
