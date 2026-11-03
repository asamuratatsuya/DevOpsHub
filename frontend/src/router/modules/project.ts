const Layout = () => import("@/layout/index.vue");

export default {
  path: "/project",
  name: "Project",
  component: Layout,
  redirect: "/project/index",
  meta: {
    icon: "ri:folder-3-line",
    title: "项目管理",
    rank: 1
  },
  children: [
    {
      path: "/project/index",
      name: "ProjectIndex",
      component: () => import("@/views/project/index.vue"),
      meta: {
        title: "项目列表"
      }
    }
  ]
} satisfies RouteConfigsTable;
