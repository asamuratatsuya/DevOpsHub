<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, Link } from "@element-plus/icons-vue";
import { getPipelineRuns, type PipelineRun } from "@/api/pipeline";

const loading = ref(false);
const runs = ref<PipelineRun[]>([]);
const repository = ref("asamuratatsuya/DevOpsHub");
const totalCount = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

const runningCount = computed(
  () => runs.value.filter(item => item.status === "in_progress").length
);
const successCount = computed(
  () => runs.value.filter(item => item.conclusion === "success").length
);
const failedCount = computed(
  () => runs.value.filter(item => item.conclusion === "failure").length
);

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function statusText(run: PipelineRun) {
  if (run.status !== "completed") {
    const labels: Record<string, string> = {
      queued: "排队中",
      in_progress: "运行中",
      waiting: "等待中",
      requested: "已请求",
      pending: "等待处理"
    };
    return labels[run.status] || run.status || "未知";
  }

  const labels: Record<string, string> = {
    success: "成功",
    failure: "失败",
    cancelled: "已取消",
    skipped: "已跳过",
    timed_out: "超时",
    action_required: "需要处理",
    neutral: "中性结束",
    stale: "已过期"
  };
  return labels[run.conclusion || ""] || run.conclusion || "已完成";
}

function statusType(run: PipelineRun) {
  if (run.status !== "completed") {
    return run.status === "in_progress" ? "warning" : "info";
  }

  if (run.conclusion === "success") return "success";
  if (run.conclusion === "failure" || run.conclusion === "timed_out") {
    return "danger";
  }
  return "info";
}

const eventLabels: Record<string, string> = {
  push: "代码推送",
  pull_request: "Pull Request",
  workflow_dispatch: "手动触发",
  schedule: "定时触发",
  release: "Release",
  workflow_run: "工作流触发"
};

function eventText(event: string) {
  return eventLabels[event] || event || "-";
}

async function loadRuns() {
  loading.value = true;
  try {
    const data = await getPipelineRuns(currentPage.value, pageSize.value);
    runs.value = data.runs || [];
    totalCount.value = data.total_count || 0;
    repository.value = data.repository || repository.value;
  } catch (error) {
    console.error("获取 GitHub Actions 运行记录失败：", error);
    ElMessage.error("获取流水线记录失败，请检查后端 GitHub Token 配置");
  } finally {
    loading.value = false;
  }
}

function handlePageChange(page: number) {
  currentPage.value = page;
  loadRuns();
}

function handleSizeChange(size: number) {
  pageSize.value = size;
  currentPage.value = 1;
  loadRuns();
}

onMounted(loadRuns);
</script>

<template>
  <div class="pipeline-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>流水线管理</h2>
        <p>查看 GitHub Actions 持续集成任务的执行记录与运行状态</p>
      </div>
      <el-button type="primary" :loading="loading" @click="loadRuns">
        <el-icon><Refresh /></el-icon>
        刷新记录
      </el-button>
    </div>

    <div class="summary-grid">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">运行记录总数</div>
        <div class="summary-value">{{ totalCount }}</div>
        <div class="summary-note">GitHub Actions 历史记录</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">本页运行中</div>
        <div class="summary-value warning-text">{{ runningCount }}</div>
        <div class="summary-note">正在执行的任务</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">本页成功</div>
        <div class="summary-value success-text">{{ successCount }}</div>
        <div class="summary-note">执行成功的任务</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">本页失败</div>
        <div class="summary-value danger-text">{{ failedCount }}</div>
        <div class="summary-note">执行失败的任务</div>
      </el-card>
    </div>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>GitHub Actions 运行记录</span>
            <el-tag effect="plain" class="repository-tag">{{ repository }}</el-tag>
          </div>
          <el-tag effect="plain">{{ runs.length }} 条</el-tag>
        </div>
      </template>

      <el-table :data="runs" stripe empty-text="暂无流水线运行记录">
        <el-table-column label="工作流" min-width="190">
          <template #default="{ row }">
            <div class="workflow-name">{{ row.name }}</div>
            <div class="run-title">{{ row.display_title || "-" }}</div>
          </template>
        </el-table-column>

        <el-table-column label="运行编号" width="105">
          <template #default="{ row }">
            #{{ row.run_number }}
          </template>
        </el-table-column>

        <el-table-column prop="branch" label="分支" min-width="120" />

        <el-table-column label="触发方式" min-width="130">
          <template #default="{ row }">
            {{ eventText(row.event) }}
          </template>
        </el-table-column>

        <el-table-column label="执行状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row)" effect="light">
              {{ statusText(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="actor" label="触发者" min-width="120">
          <template #default="{ row }">
            {{ row.actor || "-" }}
          </template>
        </el-table-column>

        <el-table-column label="触发时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.run_started_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-link
              v-if="row.html_url"
              :href="row.html_url"
              target="_blank"
              rel="noopener noreferrer"
              type="primary"
            >
              查看详情
              <el-icon class="link-icon"><Link /></el-icon>
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" v-if="totalCount > 0">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.pipeline-page {
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.summary-card {
  border-radius: 9px;
  border-color: #ebeef5;
}

.summary-label {
  color: #909399;
  font-size: 13px;
}

.summary-value {
  margin-top: 10px;
  font-size: 26px;
  font-weight: 600;
  line-height: 1.2;
}

.summary-note {
  margin-top: 8px;
  color: #c0c4cc;
  font-size: 12px;
}

.warning-text {
  color: #e6a23c;
}

.success-text {
  color: #67c23a;
}

.danger-text {
  color: #f56c6c;
}

.content-card {
  border-radius: 9px;
  border-color: #ebeef5;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
}

.repository-tag {
  margin-left: 10px;
  font-weight: 400;
}

.workflow-name {
  font-weight: 500;
  line-height: 1.6;
}

.run-title {
  margin-top: 3px;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.link-icon {
  margin-left: 3px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .pipeline-page {
    padding: 12px;
  }

  .page-header {
    align-items: flex-start;
    gap: 12px;
  }

  .summary-grid {
    gap: 10px;
  }

  .card-header {
    align-items: flex-start;
  }

  .repository-tag {
    display: block;
    width: fit-content;
    margin: 6px 0 0;
  }
}
</style>
