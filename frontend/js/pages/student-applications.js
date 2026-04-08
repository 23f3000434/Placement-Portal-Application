const StudentApplications = {
    template: `
    <div>
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>My Applications</h2>
            <button class="btn btn-outline-primary" @click="exportCSV" :disabled="exporting">
                <span v-if="exporting" class="spinner-border spinner-border-sm me-2"></span>
                <i v-else class="bi bi-download"></i> Export CSV
            </button>
        </div>
        <div v-if="exportMsg" class="alert alert-info alert-dismissible">
            {{ exportMsg }}
            <button type="button" class="btn-close" @click="exportMsg=''"></button>
        </div>
        <div v-if="applications.length === 0" class="empty-state">
            <i class="bi bi-file-earmark-text"></i>
            <p>You haven't applied to any drives yet</p>
            <router-link to="/student/drives" class="btn btn-primary">Browse Drives</router-link>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Company</th>
                        <th>Position</th>
                        <th>Package</th>
                        <th>Status</th>
                        <th>Applied On</th>
                        <th>Deadline</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(a, i) in applications" :key="a.id">
                        <td>{{ i + 1 }}</td>
                        <td><strong>{{ a.company_name }}</strong></td>
                        <td>{{ a.job_title }}</td>
                        <td>{{ a.package || '-' }}</td>
                        <td><span class="badge" :class="'badge-' + a.status">{{ a.status }}</span></td>
                        <td>{{ formatDate(a.applied_at) }}</td>
                        <td>{{ formatDate(a.deadline) }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() { return { applications: [], exporting: false, exportMsg: '' }; },
    async mounted() {
        try { const res = await api.get('/student/applications'); this.applications = res.data; } catch (err) { console.error(err); }
    },
    methods: {
        async exportCSV() {
            this.exporting = true;
            try {
                const res = await api.post('/student/export');
                this.exportMsg = res.data.message;
                if (res.data.csv_data) {
                    const blob = new Blob([res.data.csv_data], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url; a.download = 'my_applications.csv'; a.click();
                    window.URL.revokeObjectURL(url);
                }
            } catch (err) { this.exportMsg = 'Export failed'; } finally { this.exporting = false; }
        },
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};