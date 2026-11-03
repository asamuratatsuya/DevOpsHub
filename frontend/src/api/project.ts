import { http } from "@/utils/http";

/**
 * 后端返回的项目数据结构
 */
export interface ProjectApi {
  id: number;
  name: string;
  description: string | null;
  repository_url: string | null;
  branch: string;
  status: string;
  created_at: string;
}

/**
 * 创建或更新项目时提交的数据
 */
export interface ProjectPayload {
  name: string;
  description: string | null;
  repository_url: string;
  branch: string;
}

/**
 * 获取项目列表
 */
export function getProjectList() {
  return http.get<ProjectApi[], unknown>("/api/v1/projects");
}

/**
 * 创建项目
 */
export function createProject(data: ProjectPayload) {
  return http.post<ProjectApi, ProjectPayload>("/api/v1/projects", {
    data
  });
}

/**
 * 更新项目
 */
export function updateProject(id: number, data: ProjectPayload) {
  return http.request<ProjectApi>("put", `/api/v1/projects/${id}`, { data });
}

/**
 * 删除项目
 */
export function deleteProject(id: number) {
  return http.request<void>("delete", `/api/v1/projects/${id}`);
}
