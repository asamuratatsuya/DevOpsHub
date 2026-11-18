import { http } from "@/utils/http";

export interface PipelineRun {
  id: number;
  name: string;
  run_number: number;
  display_title: string;
  event: string;
  status: string;
  conclusion: string | null;
  branch: string;
  head_sha: string;
  html_url: string;
  created_at: string | null;
  updated_at: string | null;
  run_started_at: string | null;
  actor: string;
}

export interface PipelineRunList {
  repository: string;
  total_count: number;
  page: number;
  per_page: number;
  runs: PipelineRun[];
}

export function getPipelineRuns(page = 1, perPage = 20) {
  return http.get<PipelineRunList, unknown>("/api/v1/pipelines/runs", {
    params: {
      page,
      per_page: perPage
    }
  });
}
