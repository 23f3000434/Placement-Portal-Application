// ──────────────────────────── Vue Router Setup ────────────────────────────

const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginPage },
    { path: "/register", component: RegisterPage },

    // Admin routes
    {
        path: "/admin",
        component: AdminLayout,
        children: [
            { path: "", component: AdminDashboard },
            { path: "companies", component: AdminCompanies },
            { path: "drives", component: AdminDrives },
            { path: "students", component: AdminStudents },
            { path: "applications", component: AdminApplications },
        ],
    },

    // Company routes
    {
        path: "/company",
        component: CompanyLayout,
        children: [
            { path: "", component: CompanyDashboard },
            { path: "drives", component: CompanyDrives },
            { path: "drives/:driveId/applications", component: CompanyApplications },
        ],
    },

    // Student routes
    {
        path: "/student",
        component: StudentLayout,
        children: [
            { path: "", component: StudentDashboard },
            { path: "drives", component: StudentDrives },
            { path: "applications", component: StudentApplications },
            { path: "profile", component: StudentProfile },
        ],
    },
];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
});

// Navigation guard — protect routes based on role
router.beforeEach((to, from, next) => {
    const publicPages = ["/login", "/register"];
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    // If going to a public page, allow
    if (publicPages.includes(to.path)) {
        // If already logged in, redirect to dashboard
        if (token && role) {
            const dashboards = { admin: "/admin", company: "/company", student: "/student" };
            return next(dashboards[role] || "/login");
        }
        return next();
    }

    // If not logged in, redirect to login
    if (!token) {
        return next("/login");
    }

    // Check role-based access
    if (to.path.startsWith("/admin") && role !== "admin") return next("/login");
    if (to.path.startsWith("/company") && role !== "company") return next("/login");
    if (to.path.startsWith("/student") && role !== "student") return next("/login");

    next();
});

// ──────────────────────────── Create Vue App ────────────────────────────

const app = Vue.createApp({});
app.use(router);
app.mount("#app");
