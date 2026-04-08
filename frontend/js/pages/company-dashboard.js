const CompanyDashboard = {
    template: `
    <div>
        <h2 class="mb-4">Company Dashboard</h2>
        <div v-if="data.approval_status === 'pending'" class="alert alert-warning">
            <i class="bi bi-hourglass-split"></i> Your company registration is pending admin approval. You cannot create drives yet.
        </div>
        <div v-if="data.approval_status === 'rejected'" class="alert alert-danger">
            <i class="bi bi-x-circle"></i> Your company registration was rejected. Contact admin for details.
        </div>
        <div v-if="data.is_blacklisted" class="alert alert-dark">
            <i class="bi bi-slash-circle"></i> Your company has been blacklisted.
        </div>
        <div class="row g-4 mb-4">
            <div class="col-md-4">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-building-fill fs-3 text-primary mb-2"></i>
                        <h5>{{ data.company_name }}</h5>
                        <span class="badge" :class="'badge-' + data.approval_status">{{ data.approval_status }}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-briefcase-fill fs-3 text-warning mb-2"></i>
                        <div class="stat-value">{{ data.total_drives || 0 }}</div>
                        <div class="stat-label">Total Drives</div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-people-fill fs-3 text-success mb-2"></i>
                        <div class="stat-value">{{ data.total_applicants || 0 }}</div>
                        <div class="stat-label">Total Applicants</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card shadow-sm">
            <div class="card-header d-flex justify-content-between align-items-center">
                <strong>Company Details</strong>
            </div>
            <div class="card-body">
                <p><strong>HR Contact:</strong> {{ data.hr_contact || 'Not set' }}</p>
                <p><strong>Website:</strong> <a :href="data.website" target="_blank">{{ data.website || 'Not set' }}</a></p>
                <p><strong>Description:</strong> {{ data.description || 'Not set' }}</p>
            </div>
        </div>
    </div>
    `,
    data() { return { data: {} }; },
    async mounted() {
        try {
            const res = await api.get('/company/dashboard');
            this.data = res.data;
        } catch (err) { console.error(err); }
    }
};
