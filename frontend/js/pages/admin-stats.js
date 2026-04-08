const AdminStats = {
    template: `
    <div>
        <h2 class="mb-4"><i class="bi bi-bar-chart"></i> Reports & Placement Statistics</h2>
        <div class="row g-4 mb-4">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Applications by Status</strong></div>
                    <div class="card-body"><canvas id="statusChart" height="250"></canvas></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Applications by Branch</strong></div>
                    <div class="card-body"><canvas id="branchChart" height="250"></canvas></div>
                </div>
            </div>
        </div>
        <div class="row g-4 mb-4">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Drives per Month</strong></div>
                    <div class="card-body"><canvas id="monthlyChart" height="250"></canvas></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Top Companies by Selections</strong></div>
                    <div class="card-body">
                        <div v-if="stats.top_companies && stats.top_companies.length === 0" class="text-muted text-center py-4">No selections yet</div>
                        <table v-else class="table table-sm">
                            <thead><tr><th>Company</th><th>Selections</th></tr></thead>
                            <tbody>
                                <tr v-for="c in (stats.top_companies || [])" :key="c.company">
                                    <td>{{ c.company }}</td>
                                    <td><span class="badge bg-success">{{ c.selections }}</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() { return { stats: {}, charts: [] }; },
    async mounted() {
        try {
            const res = await api.get('/admin/stats');
            this.stats = res.data;
            this.$nextTick(() => this.renderCharts());
        } catch (err) { console.error(err); }
    },
    methods: {
        renderCharts() {
            this.charts.forEach(c => c.destroy());
            this.charts = [];
            const colors = { applied: '#3498db', shortlisted: '#f39c12', selected: '#27ae60', rejected: '#e74c3c' };
            const sc = this.stats.status_counts || {};
            const ctx1 = document.getElementById('statusChart');
            if (ctx1) {
                this.charts.push(new Chart(ctx1, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(sc).map(s => s.charAt(0).toUpperCase() + s.slice(1)),
                        datasets: [{ data: Object.values(sc), backgroundColor: Object.keys(sc).map(s => colors[s] || '#95a5a6') }]
                    },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                }));
            }
            const bs = this.stats.branch_stats || {};
            const ctx2 = document.getElementById('branchChart');
            if (ctx2) {
                this.charts.push(new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(bs),
                        datasets: [{ label: 'Applications', data: Object.values(bs), backgroundColor: '#3498db' }]
                    },
                    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
                }));
            }
            const dm = this.stats.drives_by_month || [];
            const ctx3 = document.getElementById('monthlyChart');
            if (ctx3) {
                this.charts.push(new Chart(ctx3, {
                    type: 'line',
                    data: {
                        labels: dm.map(d => d.month),
                        datasets: [{ label: 'Drives', data: dm.map(d => d.count), borderColor: '#2ecc71', tension: 0.3, fill: false }]
                    },
                    options: { responsive: true, scales: { y: { beginAtZero: true } } }
                }));
            }
        }
    },
    beforeUnmount() { this.charts.forEach(c => c.destroy()); }
};
