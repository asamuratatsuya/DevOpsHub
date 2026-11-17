
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Refresh, VideoPlay, Document } from "@element-plus/icons-vue";
import {
  getDeploymentList,
  getClusterPodList,
  scaleDeployment,
  restartDeployment,
  getPodLogs,
  type Deployment,
  type ClusterPod
} from "@/api/deployment";

const loading = ref(false);
const deployments = ref<Deployment[]>([]);
const pods = ref<ClusterPod[]>([]);

const scaleVisible = ref(false);
const scaleLoading = ref(false);
const selectedDeployment = ref<Deployment | null>(null);
const replicas = ref(1);

const logsVisible = ref(false);
const logsLoading = ref(false);
const logsContent = ref("");
const selectedPod = ref<ClusterPod | null>(null);

const namespaceFilter = ref("");

const filteredDeployments = computed(() => {
  if (!namespaceFilter.value) return deployments.value;
  return deployments.value.filter(
    item => item.namespace === namespaceFilter.value
  );
});

const namespaces = computed(() =>
  [...new Set(deployments.value.map(item => item.namespace))]
);

const filteredPods = computed(() => {
  if (!namespaceFilter.value) return pods.value;
  return pods.value.filter(
    item => item.namespace === namespaceFilter.value
  );
});

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

async function loadData() {
  loading.value = true;
  try {
    const [deploymentData, podData] = await Promise.all([
      getDeploymentList(),
      getClusterPodList()
    ]);
    deployments.value = deploymentData;
    pods.value = podData;
  } catch (error) {
    console.error("获取 Kubernetes 数据失败：", error);
    ElMessage.error("获取数据失败，请检查后端服务");
  } finally {
    loading.value = false;
  }
}

function openScale(row: Deployment) {
  selectedDeployment.value = row;
  replicas.value = row.replicas.desired;
  scaleVisible.value = true;
}

async function confirmScale() {
  if (!selectedDeployment.value) return;

  scaleLoading.value = true;
  try {
    const item = selectedDeployment.value;
    await scaleDeployment(item.namespace, item.name, replicas.value);
    ElMessage.success("副本数调整成功");
    scaleVisible.value = false;
    await loadData();
  } catch (error) {
    console.error("调整副本数失败：", error);
    ElMessage.error("扩缩容失败");
  } finally {
    scaleLoading.value = false;
  }
}

async function restart(row: Deployment) {
  try {
    await ElMessageBox.confirm(
      `确定要重启 Deployment「${row.name}」吗？`,
      "重启确认",
      {
        confirmButtonText: "确定重启",
        cancelButtonText: "取消",
        type: "warning"
      }
    );

    await restartDeployment(row.namespace, row.name);
    ElMessage.success("重启指令已发送");
    await loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("重启 Deployment 失败：", error);
      ElMessage.error("重启失败");
    }
  }
}

async function openLogs(row: ClusterPod) {
  selectedPod.value = row;
  logsContent.value = "";
  logsVisible.value = true;
  logsLoading.value = true;

  try {
    logsContent.value =
      (await getPodLogs(row.namespace, row.name)) || "暂无日志内容";
  } catch (error) {
    console.error("获取 Pod 日志失败：", error);
    logsContent.value = "获取日志失败，请检查 Pod 状态及访问权限。";
  } finally {
    logsLoading.value = false;
  }
}

onMounted(loadData);
</script>

<template>
  <div class="deployment-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>Deployment 管理</h2>
        <p>查看 Kubernetes 工作负载，管理副本数量及应用运行状态</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadData">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>Deployment 列表</span>
          <el-tag effect="plain">{{ filteredDeployments.length }} 个</el-tag>
        </div>
      </template>

      <div class="filter-bar">
        <el-select
          v-model="namespaceFilter"
          placeholder="全部命名空间"
          clearable
          style="width: 220px"
        >
          <el-option
            v-for="item in namespaces"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </div>

      <el-table :data="filteredDeployments" stripe empty-text="暂无 Deployment">
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="namespace" label="命名空间" min-width="130" />

        <el-table-column label="副本状态" min-width="130">
          <template #default="{ row }">
            <el-tag
              :type="row.replicas.ready === row.replicas.desired ? 'success' : 'warning'"
            >
              {{ row.replicas.ready }} / {{ row.replicas.desired }} Ready
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="镜像" min-width="220">
          <template #default="{ row }">
            <div v-for="image in row.images" :key="image" class="image-text">
              {{ image }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="strategy" label="更新策略" width="120">
          <template #default="{ row }">
            {{ row.strategy || "-" }}
          </template>
        </el-table-column>

        <el-table-column label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openScale(row)">
              扩缩容
            </el-button>
            <el-button link type="warning" @click="restart(row)">
              重启
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>Pod 列表</span>
          <el-tag effect="plain">{{ filteredPods.length }} 个</el-tag>
        </div>
      </template>

      <el-table :data="filteredPods" stripe empty-text="暂无 Pod">
        <el-table-column prop="name" label="Pod 名称" min-width="220" />
        <el-table-column prop="namespace" label="命名空间" min-width="130" />

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'Running' ? 'success' : row.status === 'Pending' ? 'warning' : 'danger'"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="容器就绪" width="120">
          <template #default="{ row }">
            {{ row.ready_containers }} / {{ row.total_containers }}
          </template>
        </el-table-column>

        <el-table-column prop="node_name" label="所在节点" min-width="120" />

        <el-table-column prop="restart_count" label="重启次数" width="100" />

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openLogs(row)">
              <el-icon><Document /></el-icon>
              查看日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="scaleVisible" title="调整 Deployment 副本数" width="420px">
      <div v-if="selectedDeployment" class="scale-content">
        <p>Deployment：{{ selectedDeployment.name }}</p>
        <p>命名空间：{{ selectedDeployment.namespace }}</p>
        <div class="replica-control">
          <span>目标副本数</span>
          <el-input-number v-model="replicas" :min="0" :max="10" />
        </div>
      </div>
      <template #footer>
        <el-button @click="scaleVisible = false">取消</el-button>
        <el-button type="primary" :loading="scaleLoading" @click="confirmScale">
          确认调整
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="logsVisible"
      :title="`Pod 日志 - ${selectedPod?.name || ''}`"
      width="75%"
      top="6vh"
    >
      <div v-loading="logsLoading" class="logs-container">
        <pre>{{ logsContent }}</pre>
      </div>
      <template #footer>
        <el-button @click="logsVisible = false">关闭</el-button>
        <el-button
          type="primary"
          :loading="logsLoading"
          @click="selectedPod && openLogs(selectedPod)"
        >
          <el-icon><Refresh /></el-icon>
          刷新日志
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.deployment-page {
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

.content-card {
  margin-bottom: 18px;
  border-radius: 9px;
  border-color: #ebeef5;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
}

.filter-bar {
  margin-bottom: 16px;
}

.image-text {
  overflow-wrap: anywhere;
  line-height: 1.7;
  font-size: 12px;
  color: #606266;
}

.scale-content p {
  margin: 0 0 14px;
  color: #606266;
}

.replica-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 22px;
}

.logs-container {
  min-height: 180px;
  max-height: 60vh;
  overflow: auto;
  padding: 14px;
  border-radius: 6px;
  background: #1e1e1e;
  color: #d4d4d4;
}

.logs-container pre {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-family: Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 600px) {
  .deployment-page {
    padding: 12px;
  }

  .page-header {
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
