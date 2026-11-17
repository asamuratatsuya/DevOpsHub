
const Layout = () => import("@/layout/index.vue");

export default {
  path: "/cluster",
  name: "Cluster",
  component: Layout,
  redirect: "/cluster/index",
  meta: {
    icon: "ri:cloud-line",
    title: "集群管理",
    rank: 2
  },
  children: [
    {
      path: "/cluster/index",
      name: "ClusterIndex",
      component: () => import("@/views/cluster/index.vue"),
      meta: {
        title: "集群概览"
      }
    }
  ]
} satisfies RouteConfigsTable;
