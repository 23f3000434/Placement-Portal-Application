// ──────────────────────────── Sidebar Components ────────────────────────────

const AdminSidebar = {
    template: `
    <div class="sidebar" :class="{show: showSidebar}">
        <div class="brand"><i class="bi bi-mortarboard-fill"></i> Placement Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/admin" class="nav-link" exact-active-class="active" @click="$emit('nav')">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/admin/companies" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-building"></i> Companies
            </router-link>
            <router-link to="/admin/drives" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-briefcase"></i> Drives
            </router-link>
            <router-link to="/admin/students" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-people"></i> Students
            </router-link>
            <router-link to="/admin/applications" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-file-earmark-text"></i> Applications
            </router-link>
            <router-link to="/admin/stats" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-bar-chart"></i> Reports & Stats
            </router-link>
        </nav>
        <div class="mt-auto p-3" style="position:absolute;bottom:0;width:100%;">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
    props: ['showSidebar'],
};

const CompanySidebar = {
    template: `
    <div class="sidebar" :class="{show: showSidebar}">
        <div class="brand"><i class="bi bi-building"></i> Company Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/company" class="nav-link" exact-active-class="active" @click="$emit('nav')">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/company/drives" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-briefcase"></i> My Drives
            </router-link>
            <router-link to="/company/interviews" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-calendar-event"></i> Interviews
            </router-link>
        </nav>
        <div class="mt-auto p-3" style="position:absolute;bottom:0;width:100%;">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
    props: ['showSidebar'],
};

const StudentSidebar = {
    template: `
    <div class="sidebar" :class="{show: showSidebar}">
        <div class="brand"><i class="bi bi-person-badge"></i> Student Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/student" class="nav-link" exact-active-class="active" @click="$emit('nav')">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/student/drives" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-briefcase"></i> Browse Drives
            </router-link>
            <router-link to="/student/applications" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-file-earmark-text"></i> My Applications
            </router-link>
            <router-link to="/student/profile" class="nav-link" active-class="active" @click="$emit('nav')">
                <i class="bi bi-person"></i> Profile
            </router-link>
        </nav>
        <div class="mt-auto p-3" style="position:absolute;bottom:0;width:100%;">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
    props: ['showSidebar'],
};

// ──────────────────────────── Layout Wrappers (Responsive) ────────────────────────────

const AdminLayout = {
    components: { AdminSidebar },
    template: `
    <div>
        <button class="btn btn-dark sidebar-toggle" @click="showSidebar = !showSidebar">
            <i class="bi bi-list"></i>
        </button>
        <admin-sidebar :show-sidebar="showSidebar" @logout="doLogout" @nav="showSidebar = false"></admin-sidebar>
        <div class="content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    data() { return { showSidebar: false }; },
    methods: { doLogout() { logout(); } }
};

const CompanyLayout = {
    components: { CompanySidebar },
    template: `
    <div>
        <button class="btn btn-dark sidebar-toggle" @click="showSidebar = !showSidebar">
            <i class="bi bi-list"></i>
        </button>
        <company-sidebar :show-sidebar="showSidebar" @logout="doLogout" @nav="showSidebar = false"></company-sidebar>
        <div class="content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    data() { return { showSidebar: false }; },
    methods: { doLogout() { logout(); } }
};

const StudentLayout = {
    components: { StudentSidebar },
    template: `
    <div>
        <button class="btn btn-dark sidebar-toggle" @click="showSidebar = !showSidebar">
            <i class="bi bi-list"></i>
        </button>
        <student-sidebar :show-sidebar="showSidebar" @logout="doLogout" @nav="showSidebar = false"></student-sidebar>
        <div class="content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    data() { return { showSidebar: false }; },
    methods: { doLogout() { logout(); } }
};
