// ──────────────────────────── Sidebar Component ────────────────────────────

const AdminSidebar = {
    template: `
    <div class="sidebar d-flex flex-column">
        <div class="brand"><i class="bi bi-mortarboard-fill"></i> Placement Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/admin" class="nav-link" exact-active-class="active">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/admin/companies" class="nav-link" active-class="active">
                <i class="bi bi-building"></i> Companies
            </router-link>
            <router-link to="/admin/drives" class="nav-link" active-class="active">
                <i class="bi bi-briefcase"></i> Drives
            </router-link>
            <router-link to="/admin/students" class="nav-link" active-class="active">
                <i class="bi bi-people"></i> Students
            </router-link>
            <router-link to="/admin/applications" class="nav-link" active-class="active">
                <i class="bi bi-file-earmark-text"></i> Applications
            </router-link>
        </nav>
        <div class="mt-auto p-3">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
};

const CompanySidebar = {
    template: `
    <div class="sidebar d-flex flex-column">
        <div class="brand"><i class="bi bi-building"></i> Company Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/company" class="nav-link" exact-active-class="active">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/company/drives" class="nav-link" active-class="active">
                <i class="bi bi-briefcase"></i> My Drives
            </router-link>
        </nav>
        <div class="mt-auto p-3">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
};

const StudentSidebar = {
    template: `
    <div class="sidebar d-flex flex-column">
        <div class="brand"><i class="bi bi-person-badge"></i> Student Portal</div>
        <nav class="nav flex-column mt-3">
            <router-link to="/student" class="nav-link" exact-active-class="active">
                <i class="bi bi-speedometer2"></i> Dashboard
            </router-link>
            <router-link to="/student/drives" class="nav-link" active-class="active">
                <i class="bi bi-briefcase"></i> Browse Drives
            </router-link>
            <router-link to="/student/applications" class="nav-link" active-class="active">
                <i class="bi bi-file-earmark-text"></i> My Applications
            </router-link>
            <router-link to="/student/profile" class="nav-link" active-class="active">
                <i class="bi bi-person"></i> Profile
            </router-link>
        </nav>
        <div class="mt-auto p-3">
            <button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')">
                <i class="bi bi-box-arrow-left"></i> Logout
            </button>
        </div>
    </div>
    `,
};

// ──────────────────────────── Layout Wrappers ────────────────────────────

const AdminLayout = {
    components: { AdminSidebar },
    template: `
    <div class="d-flex">
        <admin-sidebar @logout="logout" style="width: 250px; flex-shrink: 0;"></admin-sidebar>
        <div class="flex-grow-1 content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    methods: { logout }
};

const CompanyLayout = {
    components: { CompanySidebar },
    template: `
    <div class="d-flex">
        <company-sidebar @logout="logout" style="width: 250px; flex-shrink: 0;"></company-sidebar>
        <div class="flex-grow-1 content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    methods: { logout }
};

const StudentLayout = {
    components: { StudentSidebar },
    template: `
    <div class="d-flex">
        <student-sidebar @logout="logout" style="width: 250px; flex-shrink: 0;"></student-sidebar>
        <div class="flex-grow-1 content-area">
            <router-view></router-view>
        </div>
    </div>
    `,
    methods: { logout }
};
