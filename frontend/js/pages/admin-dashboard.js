const AdminDashboard = {
    template: `
    <div>
        <h2 class="mb-4">Admin Dashboard</h2>
        <div class="row g-4 mb-4">
            <div class="col-md-3" v-for="stat in stats" :key="stat.label">
                <div class="card stat-card shadow-sm">
                    <div class="card-body text-center">
                        <i :class="stat.icon" class="fs-3 mb-2" :style="{color: stat.color}"></i>
                        <div class="stat-value">{{ stat.value }}</div>
                        <div class="stat-label">{{ stat.label }}</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Quick Actions</strong></div>
                    <div class="card-body">
                        <router-link to="/admin/companies?status=pending" class="btn btn-warning me-2 mb-2">
                            <i class="bi bi-hourglass-split"></i> Pending Companies ({{ data.pending_companies }})
                        </router-link>
                        <router-link to="/admin/drives?status=pending" class="btn btn-warning me-2 mb-2">
                            <i class="bi bi-hourglass-split"></i> Pending Drives ({{ data.pending_drives }})
                        </router-link>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Overview</strong></div>
                    <div class="card-body">
                        <canvas id="overviewChart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return { data: {}, chart: null };
    },
    computed: {
        stats() {
            return [
                { label: 'Students', value: this.data.total_students || 0, icon: 'bi bi-people-fill', color: '#3498db' },
                { label: 'Companies', value: this.data.total_companies || 0, icon: 'bi bi-building-fill', color: '#2ecc71' },
                { label: 'Drives', value: this.data.total_drives || 0, icon: 'bi bi-briefcase-fill', color: '#f39c12' },
                { label: 'Placed', value: this.data.students_placed || 0, icon: 'bi bi-trophy-fill', color: '#9b59b6' },
            ];
        }
    },
    async mounted() {
        try {
            const res = await api.get('/admin/dashboard');
            this.data = res.data;
            this.$nextTick(() => this.renderChart());
        } catch (err) { console.error(err); }
    },
    methods: {
        renderChart() {
            const ctx = document.getElementById('overviewChart');
            if (!ctx) return;
            if (this.chart) this.chart.destroy();
            this.chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Approved Drives', 'Pending Drives', 'Total Applications', 'Students Placed'],
                    datasets: [{
                        data: [this.data.approved_drives || 0, this.data.pending_drives || 0, this.data.total_applications || 0, this.data.students_placed || 0],
                        backgroundColor: ['#27ae60', '#f39c12', '#3498db', '#9b59b6'],
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
            });
        }
    }
};
