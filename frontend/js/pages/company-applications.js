const CompanyApplications = {
    template: `
    <div>
        <div class="d-flex align-items-center mb-4">
            <router-link to="/company/drives" class="btn btn-outline-secondary me-3">
                <i class="bi bi-arrow-left"></i> Back to Drives
            </router-link>
            <h2 class="mb-0">Applications</h2>
        </div>
        <div v-if="applications.length === 0" class="empty-state">
            <i class="bi bi-file-earmark-text"></i>
            <p>No applications for this drive yet</p>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Email</th>
                        <th>Branch</th>
                        <th>CGPA</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Applied On</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="a in applications" :key="a.id">
                        <td><strong>{{ a.student_name }}</strong></td>
                        <td>{{ a.student_email }}</td>
                        <td>{{ a.student_branch }}</td>
                        <td>{{ a.student_cgpa }}</td>
                        <td>{{ a.student_phone || '-' }}</td>
                        <td><span class="badge" :class="'badge-' + a.status">{{ a.status }}</span></td>
                        <td>{{ formatDate(a.applied_at) }}</td>
                        <td>
                            <select class="form-select form-select-sm" style="width: auto; display: inline-block;" :value="a.status" @change="updateStatus(a.id, $event.target.value)">
                                <option value="applied">Applied</option>
                                <option value="shortlisted">Shortlisted</option>
                                <option value="selected">Selected</option>
                                <option value="rejected">Rejected</option>
                            </select>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() { return { applications: [], driveId: null }; },
    mounted() {
        this.driveId = this.$route.params.driveId;
        this.fetchApplications();
    },
    methods: {
        async fetchApplications() {
            try {
                const res = await api.get(`/company/drives/${this.driveId}/applications`);
                this.applications = res.data;
            } catch (err) { console.error(err); }
        },
        async updateStatus(appId, status) {
            try {
                await api.put(`/company/applications/${appId}/status`, { status });
                this.fetchApplications();
            } catch (err) { alert(err.response?.data?.error || 'Failed to update'); }
        },
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};
