const StudentDashboard = {
    template: `
    <div>
        <h2 class="mb-4">Welcome, {{ data.name }}</h2>
        <div class="row g-4 mb-4">
            <div class="col-md-3">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-file-earmark-text-fill fs-3 text-primary mb-2"></i>
                        <div class="stat-value">{{ data.total_applications || 0 }}</div>
                        <div class="stat-label">Total Applications</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-hourglass-split fs-3 text-warning mb-2"></i>
                        <div class="stat-value">{{ data.pending || 0 }}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-star-fill fs-3 text-info mb-2"></i>
                        <div class="stat-value">{{ data.shortlisted || 0 }}</div>
                        <div class="stat-label">Shortlisted</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi bi-trophy-fill fs-3 text-success mb-2"></i>
                        <div class="stat-value">{{ data.selected || 0 }}</div>
                        <div class="stat-label">Selected</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card shadow-sm">
            <div class="card-header"><strong>Your Profile</strong></div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3"><strong>Branch:</strong> {{ data.branch }}</div>
                    <div class="col-md-3"><strong>CGPA:</strong> {{ data.cgpa }}</div>
                    <div class="col-md-3"><strong>Year:</strong> {{ data.year }}</div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() { return { data: {} }; },
    async mounted() {
        try { const res = await api.get('/student/dashboard'); this.data = res.data; } catch (err) { console.error(err); }
    }
};
