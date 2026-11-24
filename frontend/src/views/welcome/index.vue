<script setup lang="ts">
import { onBeforeUnmount, onMounted, nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  getClusterOverview,
  getClusterNodes,
  type ClusterOverview,
  type ClusterNode
} from "@/api/cluster";
import { getProjectList } from "@/api/project";

import * as echarts from "echarts";
import {
  getMonitoringOverview,
  type MonitoringOverview,
  type MonitoringRange
} from "@/api/monitoring";

defineOptions({ name: "Welcome" });

const loading = ref(false);
const projectCount = ref(0);

const overview = ref<ClusterOverview>({
  nodes: { total: 0, ready: 0, not_ready: 0 },
  pods: {
    total: 0,
    running: 0,
    pending: 0,
    failed: 0,
    succeeded: 0,
    unknown: 0
  }
});

const nodes = ref<ClusterNode[]>([]);

// Prometheus 监控数据
const monitoringRange = ref<MonitoringRange>("1h");
const monitoringLoading = ref(false);
const monitoringData = ref<MonitoringOverview | null>(null);

const resourceChartRef = ref<HTMLDivElement | null>(null);
let resourceChart: echarts.ECharts | null = null;

const rangeOptions: { label: string; value: MonitoringRange }[] = [
  { label: "15分钟", value: "15m" },
  { label: "1小时", value: "1h" },
  { label: "6小时", value: "6h" },
  { label: "24小时", value: "24h" }
];

// 初始化并更新资源趋势图
function renderResourceChart() {
  if (!resourceChartRef.value) return;

  if (!resourceChart) {
    resourceChart = echarts.init(resourceChartRef.value);
  }

  const cpuPoints = monitoringData.value?.cpu.points ?? [];
  const memoryPoints = monitoringData.value?.memory.points ?? [];

  resourceChart.setOption(
    {
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number) => `${value.toFixed(2)}%`
      },
      legend: {
        data: ["CPU", "内存"],
        top: 0,
        right: 0,
        textStyle: { color: "#8492a6", fontSize: 12 }
      },
      grid: {
        left: 42,
        right: 16,
        top: 42,
        bottom: 28
      },
      xAxis: {
        type: "time",
        boundaryGap: false,
        axisLine: { lineStyle: { color: "#ebeef5" } },
        axisLabel: {
          color: "#a0aab8",
          fontSize: 10,
          formatter: (value: number) =>
            new Date(value).toLocaleTimeString("zh-CN", {
              hour: "2-digit",
              minute: "2-digit"
            })
        }
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: {
          color: "#a0aab8",
          formatter: "{value}%"
        },
        splitLine: {
          lineStyle: { color: "#f0f2f5" }
        }
      },
      series: [
        {
          name: "CPU",
          type: "line",
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2 },
          itemStyle: { color: "#409eff" },
          data: cpuPoints.map(item => [item.timestamp * 1000, item.value])
        },
        {
          name: "内存",
          type: "line",
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2 },
          itemStyle: { color: "#35b56a" },
          data: memoryPoints.map(item => [item.timestamp * 1000, item.value])
        }
      ]
    },
    true
  );
}

// 获取 Prometheus 数据
async function loadMonitoring(range: MonitoringRange = monitoringRange.value) {
  monitoringLoading.value = true;

  try {
    monitoringData.value = await getMonitoringOverview(range);
    await nextTick();
    renderResourceChart();
  } catch (error) {
    console.error("Prometheus 监控数据加载失败：", error);
    ElMessage.error("监控数据加载失败");
  } finally {
    monitoringLoading.value = false;
  }
}

// 切换监控时间范围
function changeMonitoringRange(range: MonitoringRange) {
  if (range === monitoringRange.value) return;

  monitoringRange.value = range;
  loadMonitoring(range);
}

// 调整窗口大小时重新适配图表
function resizeResourceChart() {
  resourceChart?.resize();
}

const router = useRouter();

const quickActions = [
  {
    title: "项目管理",
    description: "管理已接入的 GitHub 项目",
    symbol: "P",
    path: "/project/index"
  },
  {
    title: "集群概览",
    description: "查看 Kubernetes 节点与 Pod 状态",
    symbol: "K",
    path: "/cluster/index"
  }
];

function navigateTo(path: string) {
  router.push(path);
}

const statistics = [
  {
    title: "项目总数",
    unit: "个",
    description: "已接入管理的项目",
    color: "blue",
    symbol: "P",
    value: () => projectCount.value
  },
  {
    title: "Kubernetes 节点",
    unit: "个",
    description: "集群节点总数",
    color: "green",
    symbol: "N",
    value: () => overview.value.nodes.total
  },
  {
    title: "Pod 总数",
    unit: "个",
    description: "集群中的 Pod 实例",
    color: "purple",
    symbol: "P",
    value: () => overview.value.pods.total
  },
  {
    title: "运行中 Pod",
    unit: "个",
    description: "当前 Running 状态",
    color: "orange",
    symbol: "R",
    value: () => overview.value.pods.running
  }
];

async function loadData() {
  loading.value = true;

  try {
    const [projects, overviewData, nodeData] = await Promise.all([
      getProjectList(),
      getClusterOverview(),
      getClusterNodes()
    ]);

    projectCount.value = projects.length;
    overview.value = overviewData;
    nodes.value = nodeData;
  } catch (error) {
    console.error("首页数据加载失败：", error);
    ElMessage.error("首页数据加载失败，请检查后端服务");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
  loadMonitoring();
  window.addEventListener("resize", resizeResourceChart);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeResourceChart);
  resourceChart?.dispose();
  resourceChart = null;
});
</script>

<template>
  <div v-loading="loading" class="devops-dashboard">
    <!-- 欢迎区域 -->
    <section class="welcome-header">
      <div>
        <div class="welcome-label">DEVOPS MANAGEMENT PLATFORM</div>
        <h1>欢迎使用 DevOpsHub</h1>
        <p>统一管理自动化构建、应用交付与 Kubernetes 集群。</p>
      </div>

      <div class="cluster-status">
        <span class="status-dot" />
        <span>集群数据概览</span>
      </div>
    </section>

    <!-- 数据统计卡片 -->
    <section class="statistics-grid">
      <div v-for="item in statistics" :key="item.title" class="stat-card">
        <div class="stat-top">
          <span class="stat-title">{{ item.title }}</span>
          <div class="stat-symbol" :class="item.color">
            {{ item.symbol }}
          </div>
        </div>

        <div class="stat-number">
          {{ item.value() }}
          <span>{{ item.unit }}</span>
        </div>

        <div class="stat-description">
          {{ item.description }}
        </div>
      </div>
    </section>

    <!-- 集群概览 -->
    <section class="content-section">
      <div class="section-heading">
        <div>
          <h2>集群资源概览</h2>
          <p>Kubernetes Cluster Overview</p>
        </div>
      </div>

      <div class="cluster-grid">
        <!-- 节点状态 -->
        <div class="panel node-panel">
          <h3>集群节点</h3>

          <div v-for="node in nodes" :key="node.name" class="node-item">
            <div class="node-info">
              <div class="node-name">{{ node.name }}</div>
              <div class="node-role">
                {{ node.roles.join(" / ") || "Worker" }} ·
                {{ node.internal_ip }}
              </div>
            </div>

            <div class="node-ready">
              <span
                class="status-dot"
                :class="{ 'not-ready-dot': node.status !== 'Ready' }"
              />
              {{ node.status }}
            </div>
          </div>

          <div class="node-summary">
            <span>节点总数</span>
            <strong
              >{{ overview.nodes.ready }} /
              {{ overview.nodes.total }} Ready</strong
            >
          </div>
        </div>

        <!-- 资源使用率 -->
        <div class="panel resource-panel">
          <div class="resource-header">
            <h3>资源使用情况</h3>

            <div class="range-options">
              <button
                v-for="option in rangeOptions"
                :key="option.value"
                type="button"
                :class="{ active: monitoringRange === option.value }"
                @click="changeMonitoringRange(option.value)"
              >
                {{ option.label }}
              </button>
            </div>

            <a
              class="prometheus-link"
              href="http://192.168.128.24:30090/graph"
              target="_blank"
              rel="noopener noreferrer"
            >
              打开 Prometheus ↗
            </a>
          </div>

          <div class="resource-current">
            <div>
              <span class="metric-label">CPU 使用率</span>
              <strong class="cpu-value">
                {{
                  monitoringData?.cpu.current != null
                    ? `${monitoringData.cpu.current.toFixed(2)}%`
                    : "--"
                }}
              </strong>
            </div>

            <div>
              <span class="metric-label">内存使用率</span>
              <strong class="memory-value">
                {{
                  monitoringData?.memory.current != null
                    ? `${monitoringData.memory.current.toFixed(2)}%`
                    : "--"
                }}
              </strong>
            </div>
          </div>

          <div
            ref="resourceChartRef"
            v-loading="monitoringLoading"
            class="resource-chart"
          />

          <div class="resource-note">数据来源：Prometheus · 集群实时监控</div>
        </div>
      </div>
    </section>

    <!-- 最近部署记录 -->
    <section class="content-section">
      <div class="section-heading">
        <div>
          <h2>最近部署记录</h2>
          <p>Recent Deployment Activities</p>
        </div>
      </div>

      <div class="panel deployment-panel">
        <div class="table-wrapper">
          <table class="deployment-table">
            <thead>
              <tr>
                <th>应用名称</th>
                <th>版本</th>
                <th>部署环境</th>
                <th>部署时间</th>
                <th>状态</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td colspan="5" class="empty-cell">
                  暂无部署记录，等待接入部署历史 API
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="content-section">
      <div class="section-heading">
        <div>
          <h2>快捷入口</h2>
          <p>Quick Access</p>
        </div>
      </div>

      <div class="quick-grid">
        <div
          v-for="action in quickActions"
          :key="action.title"
          class="quick-card"
          role="button"
          tabindex="0"
          @click="navigateTo(action.path)"
          @keydown.enter="navigateTo(action.path)"
          @keydown.space.prevent="navigateTo(action.path)"
        >
          <div class="quick-symbol">{{ action.symbol }}</div>
          <div>
            <h3>{{ action.title }}</h3>
            <p>{{ action.description }}</p>
          </div>
          <span class="quick-arrow">→</span>
        </div>
      </div>
    </section>

    <div class="dashboard-footer">
      DevOpsHub · Kubernetes & GitOps Automated Delivery Platform
    </div>
  </div>
</template>

<style scoped>
.devops-dashboard {
  padding: 8px;
  color: #303133;
}

.welcome-header {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
  margin-bottom: 22px;
  background: linear-gradient(120deg, #fff 0%, #eef5ff 100%);
  border: 1px solid #e5edf8;
  border-radius: 10px;
}

.welcome-label {
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  color: #409eff;
  letter-spacing: 2px;
}

.welcome-header h1 {
  margin: 0 0 10px;
  font-size: 27px;
  font-weight: 700;
  color: #24344d;
}

.welcome-header p {
  margin: 0;
  font-size: 14px;
  color: #8492a6;
}

.cluster-status,
.node-ready {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: #3c9b68;
}

.cluster-status {
  flex-shrink: 0;
  padding: 10px 15px;
  background: #eaf8f0;
  border-radius: 20px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #35b56a;
  border-radius: 50%;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 26px;
}

.stat-card,
.panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 9px;
}

.stat-card {
  padding: 20px;
  transition:
    box-shadow 0.2s,
    transform 0.2s;
}

.stat-card:hover,
.quick-card:hover {
  box-shadow: 0 6px 20px rgb(30 60 90 / 8%);
  transform: translateY(-3px);
}

.stat-top,
.resource-heading,
.node-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-title {
  font-size: 14px;
  color: #8492a6;
}

.stat-symbol,
.quick-symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  font-size: 17px;
  font-weight: 700;
  border-radius: 9px;
}

.blue {
  color: #409eff;
  background: #eaf3ff;
}

.green {
  color: #35a76b;
  background: #e9f8ef;
}

.purple {
  color: #8964df;
  background: #f1edff;
}

.orange {
  color: #e69a32;
  background: #fff5e7;
}

.stat-number {
  margin-top: 17px;
  font-size: 30px;
  font-weight: 700;
  color: #26364d;
}

.stat-number span {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 400;
  color: #8492a6;
}

.stat-description {
  margin-top: 8px;
  font-size: 12px;
  color: #a0aab8;
}

.content-section {
  margin-bottom: 27px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 650;
  color: #303f55;
}

.section-heading p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #a0aab8;
}

.demo-label {
  padding: 5px 10px;
  font-size: 11px;
  color: #b27b26;
  background: #fff6e8;
  border-radius: 5px;
}

.cluster-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.panel {
  padding: 21px;
}

.panel h3 {
  margin: 0 0 19px;
  font-size: 15px;
  color: #35445a;
}

.node-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.node-name {
  font-size: 13px;
  font-weight: 600;
  color: #35445a;
}

.node-role {
  margin-top: 4px;
  font-size: 11px;
  color: #a0aab8;
}

.node-summary {
  display: flex;
  justify-content: space-between;
  margin-top: 17px;
  font-size: 12px;
  color: #8794a5;
}

.node-summary strong {
  color: #35a76b;
}

.resource-item {
  margin-bottom: 21px;
}

.resource-heading {
  margin-bottom: 9px;
  font-size: 13px;
  color: #68788e;
}

.resource-heading strong {
  color: #35445a;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  background: #edf0f5;
  border-radius: 10px;
}

.progress-value {
  height: 100%;
  border-radius: 10px;
}

.progress-value.blue {
  background: #409eff;
}

.progress-value.green {
  background: #35b56a;
}

.progress-value.purple {
  background: #8964df;
}

.resource-note {
  margin-top: 10px;
  font-size: 11px;
  color: #a0aab8;
}

.deployment-panel {
  padding: 5px 20px;
}

.table-wrapper {
  overflow-x: auto;
}

.deployment-table {
  width: 100%;
  text-align: left;
  white-space: nowrap;
  border-collapse: collapse;
}

.deployment-table th {
  padding: 15px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #8492a6;
  background: #fafbfd;
}

.deployment-table td {
  padding: 16px 12px;
  font-size: 12px;
  color: #68788e;
  border-bottom: 1px solid #f0f2f5;
}

.deployment-table tbody tr:last-child td {
  border-bottom: none;
}

.app-name {
  font-weight: 600;
  color: #35445a !important;
}

.deployment-status {
  display: inline-block;
  padding: 5px 11px;
  font-size: 11px;
  border-radius: 12px;
}

.deployment-status.success {
  color: #269b60;
  background: #e9f8ef;
}

.deployment-status.failed {
  color: #e35b5b;
  background: #fff0f0;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 15px;
}

.quick-card {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 17px;
  cursor: pointer;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 9px;
  transition:
    box-shadow 0.2s,
    transform 0.2s;
}

.quick-symbol {
  flex-shrink: 0;
  color: #409eff;
  background: #eaf3ff;
}

.quick-card h3 {
  margin: 0;
  font-size: 13px;
  color: #35445a;
}

.quick-card p {
  margin: 5px 0 0;
  font-size: 11px;
  color: #a0aab8;
}

.quick-arrow {
  margin-left: auto;
  font-size: 18px;
  color: #a0aab8;
}

.dashboard-footer {
  padding: 12px 0 4px;
  font-size: 11px;
  color: #a0aab8;
  text-align: center;
}

@media (width <= 1100px) {
  .statistics-grid,
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (width <= 650px) {
  .welcome-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 22px;
  }

  .cluster-grid,
  .statistics-grid,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .welcome-header h1 {
    font-size: 22px;
  }
}

.resource-placeholder {
  display: flex;
  min-height: 150px;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #a0aab8;
  font-size: 13px;
  text-align: center;
  background: #fafbfd;
  border-radius: 8px;
}

.empty-cell {
  padding: 30px 12px !important;
  color: #a0aab8 !important;
  text-align: center;
}

.not-ready-dot {
  background: #f56c6c;
}
.resource-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.prometheus-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 500;
  color: #409eff;
  text-decoration: none;
  white-space: nowrap;
  background: #edf5ff;
  border: 1px solid #d9ecff;
  border-radius: 5px;
  transition: all 0.2s;
}

.prometheus-link:hover {
  color: #fff;
  background: #409eff;
  border-color: #409eff;
}

.resource-header h3 {
  margin: 0;
}

.range-options {
  display: flex;
  gap: 4px;
  padding: 3px;
  background: #f5f7fa;
  border-radius: 6px;
}

.range-options button {
  padding: 5px 9px;
  font-size: 11px;
  color: #8492a6;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 4px;
}

.range-options button.active {
  color: #409eff;
  background: #fff;
  box-shadow: 0 1px 4px rgb(0 0 0 / 8%);
}

.resource-current {
  display: flex;
  gap: 40px;
  margin-bottom: 12px;
}

.resource-current > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric-label {
  font-size: 12px;
  color: #8492a6;
}

.cpu-value,
.memory-value {
  font-size: 22px;
}

.cpu-value {
  color: #409eff;
}

.memory-value {
  color: #35a76b;
}

.resource-chart {
  width: 100%;
  height: 185px;
}

.resource-note {
  margin-top: 8px;
  font-size: 11px;
  color: #a0aab8;
}
</style>
