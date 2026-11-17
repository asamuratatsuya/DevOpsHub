
const Layout = () => import("@/layout/index.vue");

export default {
  path: "/deployment",
  name: "Deployment",
  component: Layout,
  redirect: "/deployment/index",
  meta: {
    icon: "ri:rocket-line",
    title: "部署管理",
    rank: 3
  },
  children: [
    {
      path: "/deployment/index",
      name: "DeploymentIndex",
      component: () => import("@/views/deployment/index.vue"),
      meta: {
        title: "Deployment 管理"
      }
    }
  ]
} satisfies RouteConfigsTable;
