<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import {
  createProject,
  deleteProject,
  getProjectList,
  updateProject
} from "@/api/project";

import type { ProjectApi, ProjectPayload } from "@/api/project";

defineOptions({
  name: "ProjectIndex"
});

// 前端页面使用的数据结构
interface Project {
  id: string;
  name: string;
  repoUrl: string;
  branch: string;
  description: string;
  createdAt: string;
  status: string;
}

// 将后端数据转换为前端数据格式
function mapApiProject(item: ProjectApi): Project {
  return {
    id: String(item.id),
    name: item.name,
    repoUrl: item.repository_url ?? "",
    branch: item.branch,
    description: item.description ?? "",
    status: item.status,
    createdAt: item.created_at
  };
}

// 项目列表
const projects = ref<Project[]>([]);

// 加载状态
const loading = ref(false);
const saving = ref(false);

// 搜索关键词
const searchKeyword = ref("");

// 弹窗状态
const dialogVisible = ref(false);
const editingId = ref<string | null>(null);

// 表单数据
const createEmptyForm = () => ({
  name: "",
  repoUrl: "",
  branch: "main",
  description: ""
});

const form = reactive(createEmptyForm());

// 项目总数
const totalProjects = computed(() => projects.value.length);

// 搜索过滤
const filteredProjects = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();

  if (!keyword) return projects.value;

  return projects.value.filter(
    item =>
      item.name.toLowerCase().includes(keyword) ||
      item.repoUrl.toLowerCase().includes(keyword) ||
      item.branch.toLowerCase().includes(keyword)
  );
});

// 从后端获取项目列表
async function loadProjects() {
  loading.value = true;

  try {
    const data = await getProjectList();

    projects.value = data.map(mapApiProject);
  } catch (error) {
    console.error("获取项目列表失败：", error);
    ElMessage.error("获取项目列表失败，请检查后端服务");
  } finally {
    loading.value = false;
  }
}

// 页面初始化时加载项目
onMounted(() => {
  void loadProjects();
});

// 打开添加窗口
function openCreateDialog() {
  editingId.value = null;
  Object.assign(form, createEmptyForm());
  dialogVisible.value = true;
}

// 打开编辑窗口
function openEditDialog(item: Project) {
  editingId.value = item.id;

  Object.assign(form, {
    name: item.name,
    repoUrl: item.repoUrl,
    branch: item.branch,
    description: item.description
  });

  dialogVisible.value = true;
}

// 检查并规范化 GitHub 仓库地址
function normalizeRepoUrl(raw: string): string | null {
  try {
    const url = new URL(raw.trim());

    if (
      url.protocol !== "https:" ||
      url.hostname.toLowerCase() !== "github.com"
    ) {
      return null;
    }

    const parts = url.pathname.split("/").filter(Boolean);

    if (parts.length !== 2) {
      return null;
    }

    const owner = parts[0];
    const repository = parts[1].replace(/\.git$/i, "");

    if (!owner || !repository) {
      return null;
    }

    return `https://github.com/${owner}/${repository}`;
  } catch {
    return null;
  }
}

// 保存项目：根据是否存在 editingId 决定创建或更新
async function handleSave() {
  if (saving.value) return;

  const name = form.name.trim();
  const branch = form.branch.trim();
  const repoUrl = normalizeRepoUrl(form.repoUrl);

  if (!name) {
    ElMessage.warning("请输入项目名称");
    return;
  }

  if (!repoUrl) {
    ElMessage.warning("请输入有效的 GitHub 仓库地址");
    return;
  }

  if (!branch) {
    ElMessage.warning("请输入默认分支");
    return;
  }

  // 检查仓库地址是否重复
  const duplicated = projects.value.some(
    item =>
      item.repoUrl.toLowerCase() === repoUrl.toLowerCase() &&
      item.id !== editingId.value
  );

  if (duplicated) {
    ElMessage.warning("这个 GitHub 仓库已经登记过了");
    return;
  }

  const payload: ProjectPayload = {
    name,
    description: form.description.trim() || null,
    repository_url: repoUrl,
    branch
  };

  saving.value = true;

  try {
    if (editingId.value !== null) {
      // 调用后端更新接口
      const updated = await updateProject(Number(editingId.value), payload);

      const index = projects.value.findIndex(
        item => item.id === editingId.value
      );

      if (index !== -1) {
        projects.value[index] = mapApiProject(updated);
      }

      ElMessage.success("项目修改成功");
    } else {
      // 调用后端创建接口
      const created = await createProject(payload);

      projects.value.unshift(mapApiProject(created));

      ElMessage.success("项目添加成功");
    }

    dialogVisible.value = false;
  } catch (error) {
    console.error("保存项目失败：", error);
    ElMessage.error("保存项目失败，请检查后端服务或请求参数");
  } finally {
    saving.value = false;
  }
}

// 删除项目
async function handleDelete(item: Project) {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目「${item.name}」吗？`,
      "删除确认",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "warning"
      }
    );
  } catch {
    // 用户取消删除
    return;
  }

  try {
    // 调用后端删除接口
    await deleteProject(Number(item.id));

    projects.value = projects.value.filter(project => project.id !== item.id);

    ElMessage.success("项目删除成功");
  } catch (error) {
    console.error("删除项目失败：", error);
    ElMessage.error("删除项目失败，请检查后端服务");
  }
}

// 格式化时间
function formatDate(date: string) {
  return new Date(date).toLocaleString("zh-CN");
}

// 关闭弹窗
function closeDialog() {
  dialogVisible.value = false;
  editingId.value = null;
  Object.assign(form, createEmptyForm());
}
</script>

<template>
  <div class="project-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>项目管理</h2>
        <p>管理 GitHub 仓库，为自动化构建和部署做好准备。</p>
      </div>

      <el-button type="primary" @click="openCreateDialog">
        + 添加项目
      </el-button>
    </div>

    <!-- 统计信息 -->
    <div class="summary-card">
      <div class="summary-title">项目总数</div>
      <div class="summary-value">{{ totalProjects }}</div>
      <div class="summary-description">已登记的 GitHub 项目</div>
    </div>

    <!-- 项目列表 -->
    <div class="project-panel">
      <div class="panel-header">
        <div>
          <h3>项目列表</h3>
          <span>Project Repository Management</span>
        </div>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索项目名称、仓库地址或分支"
          clearable
          style="width: 290px"
        />
      </div>

      <el-table
        v-if="filteredProjects.length > 0"
        v-loading="loading"
        :data="filteredProjects"
        style="width: 100%"
      >
        <el-table-column prop="name" label="项目名称" min-width="140">
          <template #default="{ row }">
            <strong class="project-name">{{ row.name }}</strong>
          </template>
        </el-table-column>

        <el-table-column
          label="GitHub 仓库"
          min-width="240"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <a
              :href="row.repoUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="repo-link"
            >
              {{ row.repoUrl }}
            </a>
          </template>
        </el-table-column>

        <el-table-column prop="branch" label="默认分支" width="120" />

        <el-table-column label="项目状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'active' ? 'success' : 'info'"
              effect="light"
            >
              {{ row.status === "active" ? "正常" : row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="登记时间" min-width="175">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="145" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>

            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-else
        :description="
          searchKeyword
            ? '没有找到符合条件的项目'
            : '还没有项目，点击右上角添加项目'
        "
      />
    </div>

    <!-- 添加 / 编辑项目弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑项目' : '添加项目'"
      width="520px"
      @closed="closeDialog"
    >
      <el-form label-position="top" @submit.prevent="handleSave">
        <el-form-item label="项目名称" required>
          <el-input
            v-model="form.name"
            placeholder="例如：DevOpsHub"
            maxlength="50"
          />
        </el-form-item>

        <el-form-item label="GitHub 仓库地址" required>
          <el-input
            v-model="form.repoUrl"
            placeholder="https://github.com/username/repository"
          />
        </el-form-item>

        <el-form-item label="默认分支" required>
          <el-input v-model="form.branch" placeholder="main" />
        </el-form-item>

        <el-form-item label="项目描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="简单介绍一下这个项目"
          />
        </el-form-item>

        <div class="form-tip">
          项目资料将保存至服务端数据库，目前尚未验证 GitHub 仓库权限或连接状态。
        </div>
      </el-form>

      <template #footer>
        <el-button @click="closeDialog"> 取消 </el-button>

        <el-button type="primary" @click="handleSave"> 保存项目 </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.project-page {
  padding: 8px;
  color: #303133;
}

.page-header {
  display: flex;
  gap: 15px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #26364d;
}

.page-header p {
  margin: 0;
  font-size: 13px;
  color: #8492a6;
}

.summary-card,
.project-panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 9px;
}

.summary-card {
  width: 240px;
  padding: 20px;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 13px;
  color: #8492a6;
}

.summary-value {
  margin-top: 12px;
  font-size: 30px;
  font-weight: 700;
  color: #26364d;
}

.summary-description {
  margin-top: 7px;
  font-size: 12px;
  color: #a0aab8;
}

.project-panel {
  padding: 20px;
}

.panel-header {
  display: flex;
  gap: 15px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.panel-header h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: #35445a;
}

.panel-header span {
  font-size: 12px;
  color: #a0aab8;
}

.project-name {
  color: #35445a;
}

.repo-link {
  color: #409eff;
  text-decoration: none;
}

.repo-link:hover {
  text-decoration: underline;
}

.form-tip {
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.7;
  color: #956b23;
  background: #fff8e9;
  border-radius: 5px;
}

@media (width <= 650px) {
  .page-header,
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .panel-header .el-input {
    width: 100% !important;
  }
}
</style>
