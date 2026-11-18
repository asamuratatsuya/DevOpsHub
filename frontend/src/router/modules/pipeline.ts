const Layout = () => import("@/layout/index.vue");

export default {
  path: "/pipeline",
  name: "Pipeline",
  component: Layout,
  redirect: "/pipeline/index",
  meta: {
    icon: "ri:git-branch-line",
    title: "流水线管理",
    rank: 4
  },
  children: [
    {
      path: "/pipeline/index",
      name: "PipelineIndex",
      component: () => import("@/views/pipeline/index.vue"),
      meta: {
        title: "流水线记录"
      }
    }
  ]
} satisfies RouteConfigsTable;
