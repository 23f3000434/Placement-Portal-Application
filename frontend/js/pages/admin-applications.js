const AdminApplications = {
    template: `
    <div>
        <h2 class="mb-4">All Applications</h2>
        <div v-if="applications.length === 0" class="empty-state">
            <i class="bi bi-file-earmark-text"></i>
            <p>No applications yet</p>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Student</th>
                        <th>Branch</th>
                        <th>Company</th>
                        <th>Drive</th>
                        <th>Status</th>
                        <th>Applied On</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(a, i) in applications" :key="a.id">
                        <td>{{ i + 1 }}</td>
                        <td><strong>{{ a.student_name }}</strong></td>
                        <td>{{ a.student_branch }}</td>
                        <td>{{ a.company_name }}</td>
                        <td>{{ a.drive_title }}</td>
                        <td><span class="badge" :class="'badge-' + a.status">{{ a.status }}</span></td>
                        <td>{{ formatDate(a.applied_at) }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { applications: [] };
    },
    async mounted() {
        try {
            const res = await api.get('/admin/applications');
            this.applications = res.data;
        } catch (err) { console.error(err); }
    },
    methods: {
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};
