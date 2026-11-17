
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  Refresh,
  Monitor,
  CircleCheck,
  Box,
  VideoPlay
} from "@element-plus/icons-vue";
import {
  getClusterOverview,
  getClusterNodes,
  type ClusterOverview,
  type ClusterNode
} from "@/api/cluster";

const loading = ref(false);

const overview = ref<ClusterOverview>({
  nodes: {
    total: 0,
    ready: 0,
    not_ready: 0
  },
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

/** 将 Kubernetes 内存单位 Ki 转换为 GiB */
function formatMemory(value: string): string {
  const memoryKi = Number.parseFloat(value);
  if (!Number.isFinite(memoryKi)) return value;

  return `${(memoryKi / 1024 / 1024).toFixed(2)} GiB`;
}

/** 获取节点角色 */
function formatRoles(roles: string[]): string {
  if (!roles || roles.length === 0) return "worker";

  return roles
    .map(role => {
      if (role === "control-plane") return "控制平面";
      if (role === "master") return "Master";
      return role;
    })
    .join(" / ");
}

/** 加载集群数据 */
async function loadData() {
  loading.value = true;

  try {
    const [overviewData, nodeData] = await Promise.all([
      getClusterOverview(),
      getClusterNodes()
    ]);

    overview.value = overviewData;
    nodes.value = nodeData;
  } catch (error) {
    console.error("获取集群数据失败：", error);
    ElMessage.error("获取集群数据失败，请检查后端服务");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="cluster-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>集群概览</h2>
        <p>查看 Kubernetes 集群运行状态及节点资源信息</p>
      </div>

      <el-button
        type="primary"
        :loading="loading"
        @click="loadData"
      >
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 集群统计 -->
    <div class="stats-grid">
      <el-card shadow="never" class="stats-card">
        <div class="stats-content">
          <div>
            <div class="stats-label">节点总数</div>
            <div class="stats-value">{{ overview.nodes.total }}</div>
          </div>
          <div class="stats-icon node-icon">
            <el-icon><Monitor /></el-icon>
          </div>
        </div>
        <div class="stats-footer">Kubernetes Nodes</div>
      </el-card>

      <el-card shadow="never" class="stats-card">
        <div class="stats-content">
          <div>
            <div class="stats-label">正常节点</div>
            <div class="stats-value success-text">
              {{ overview.nodes.ready }}
            </div>
          </div>
          <div class="stats-icon success-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
        </div>
        <div class="stats-footer">
          异常节点：{{ overview.nodes.not_ready }}
        </div>
      </el-card>

      <el-card shadow="never" class="stats-card">
        <div class="stats-content">
          <div>
            <div class="stats-label">Pod 总数</div>
            <div class="stats-value">{{ overview.pods.total }}</div>
          </div>
          <div class="stats-icon pod-icon">
            <el-icon><Box /></el-icon>
          </div>
        </div>
        <div class="stats-footer">Kubernetes Pods</div>
      </el-card>

      <el-card shadow="never" class="stats-card">
        <div class="stats-content">
          <div>
            <div class="stats-label">运行中 Pod</div>
            <div class="stats-value success-text">
              {{ overview.pods.running }}
            </div>
          </div>
          <div class="stats-icon running-icon">
            <el-icon><VideoPlay /></el-icon>
          </div>
        </div>
        <div class="stats-footer">
          Pending：{{ overview.pods.pending }}
          · Failed：{{ overview.pods.failed }}
        </div>
      </el-card>
    </div>

    <!-- Pod 状态 -->
    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>Pod 运行状态</span>
          <el-tag type="success" effect="plain">
            {{ overview.pods.running }} Running
          </el-tag>
        </div>
      </template>

      <div class="pod-status-grid">
        <div class="pod-status-item">
          <span class="status-dot running-dot"></span>
          <span class="pod-status-label">Running</span>
          <strong>{{ overview.pods.running }}</strong>
        </div>

        <div class="pod-status-item">
          <span class="status-dot pending-dot"></span>
          <span class="pod-status-label">Pending</span>
          <strong>{{ overview.pods.pending }}</strong>
        </div>

        <div class="pod-status-item">
          <span class="status-dot failed-dot"></span>
          <span class="pod-status-label">Failed</span>
          <strong>{{ overview.pods.failed }}</strong>
        </div>

        <div class="pod-status-item">
          <span class="status-dot succeeded-dot"></span>
          <span class="pod-status-label">Succeeded</span>
          <strong>{{ overview.pods.succeeded }}</strong>
        </div>

        <div class="pod-status-item">
          <span class="status-dot unknown-dot"></span>
          <span class="pod-status-label">Unknown</span>
          <strong>{{ overview.pods.unknown }}</strong>
        </div>
      </div>
    </el-card>

    <!-- 节点列表 -->
    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>集群节点</span>
          <el-tag effect="plain">{{ nodes.length }} 个节点</el-tag>
        </div>
      </template>

      <el-table
        :data="nodes"
        stripe
        style="width: 100%"
        empty-text="暂无节点数据"
      >
        <el-table-column
          prop="name"
          label="节点名称"
          min-width="130"
        >
          <template #default="{ row }">
            <span class="node-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'Ready' ? 'success' : 'danger'"
              effect="light"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="角色" min-width="130">
          <template #default="{ row }">
            {{ formatRoles(row.roles) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="internal_ip"
          label="内网 IP"
          min-width="145"
        />

        <el-table-column
          prop="kubelet_version"
          label="Kubelet 版本"
          min-width="125"
        />

        <el-table-column label="CPU" min-width="110">
          <template #default="{ row }">
            {{ row.allocatable.cpu }} / {{ row.capacity.cpu }} 核
          </template>
        </el-table-column>

        <el-table-column label="内存" min-width="170">
          <template #default="{ row }">
            {{ formatMemory(row.allocatable.memory) }}
            /
            {{ formatMemory(row.capacity.memory) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="table-tip">
        CPU 和内存分别展示可分配容量 / 总容量
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.cluster-page {
  padding: 20px;
  color: #303133;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.stats-card,
.content-card {
  border-radius: 9px;
  border-color: #ebeef5;
}

.stats-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats-label {
  margin-bottom: 10px;
  color: #909399;
  font-size: 14px;
}

.stats-value {
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.success-text {
  color: #67c23a;
}

.stats-icon {
  display: flex;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 23px;
}

.node-icon {
  color: #409eff;
  background: #ecf5ff;
}

.success-icon,
.running-icon {
  color: #67c23a;
  background: #f0f9eb;
}

.pod-icon {
  color: #8b7cf6;
  background: #f2f0ff;
}

.stats-footer {
  margin-top: 16px;
  color: #a8abb2;
  font-size: 12px;
}

.content-card {
  margin-bottom: 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
}

.pod-status-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.pod-status-item {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 32px;
}

.pod-status-label {
  color: #606266;
  font-size: 13px;
}

.pod-status-item strong {
  margin-left: auto;
  color: #303133;
  font-size: 16px;
}

.status-dot {
  width: 9px;
  height: 9px;
  flex-shrink: 0;
  border-radius: 50%;
}

.running-dot {
  background: #67c23a;
}

.pending-dot {
  background: #e6a23c;
}

.failed-dot {
  background: #f56c6c;
}

.succeeded-dot {
  background: #409eff;
}

.unknown-dot {
  background: #909399;
}

.node-name {
  color: #409eff;
  font-weight: 500;
}

.table-tip {
  margin-top: 12px;
  color: #a8abb2;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pod-status-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .cluster-page {
    padding: 12px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .pod-status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
