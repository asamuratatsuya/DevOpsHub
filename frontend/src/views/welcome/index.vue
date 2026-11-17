<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  getClusterOverview,
  getClusterNodes,
  type ClusterOverview,
  type ClusterNode
} from "@/api/cluster";
import { getProjectList } from "@/api/project";

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

onMounted(loadData);
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
          <h3>资源使用情况</h3>

          <div class="resource-placeholder">
            暂未接入 Prometheus，资源使用率数据暂不可用。
          </div>

          <div class="resource-note">
            接入 Prometheus 后将在此展示 CPU、内存和磁盘监控数据。
          </div>
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
</style>
