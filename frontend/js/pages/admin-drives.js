const AdminDrives = {
    template: `
    <div>
        <h2 class="mb-4">Manage Placement Drives</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Search drives..." v-model="search" @input="fetchDrives">
            </div>
            <div class="col-md-3">
                <select class="form-select" v-model="statusFilter" @change="fetchDrives">
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="closed">Closed</option>
                </select>
            </div>
        </div>
        <div v-if="drives.length === 0" class="empty-state">
            <i class="bi bi-briefcase"></i>
            <p>No drives found</p>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Package</th>
                        <th>Deadline</th>
                        <th>Status</th>
                        <th>Applications</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="d in drives" :key="d.id">
                        <td><strong>{{ d.job_title }}</strong></td>
                        <td>{{ d.company_name }}</td>
                        <td>{{ d.package || '-' }}</td>
                        <td>{{ formatDate(d.deadline) }}</td>
                        <td><span class="badge" :class="'badge-' + d.status">{{ d.status }}</span></td>
                        <td>{{ d.total_applications }}</td>
                        <td>
                            <button v-if="d.status === 'pending'" class="btn btn-success btn-sm me-1" @click="approve(d.id)">
                                <i class="bi bi-check-lg"></i> Approve
                            </button>
                            <button v-if="d.status === 'pending'" class="btn btn-danger btn-sm me-1" @click="reject(d.id)">
                                <i class="bi bi-x-lg"></i> Reject
                            </button>
                            <button v-if="d.status === 'approved'" class="btn btn-secondary btn-sm" @click="closeDrive(d.id)">
                                <i class="bi bi-lock"></i> Close
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { drives: [], search: '', statusFilter: this.$route.query.status || '' };
    },
    mounted() { this.fetchDrives(); },
    methods: {
        async fetchDrives() {
            try {
                const params = {};
                if (this.search) params.search = this.search;
                if (this.statusFilter) params.status = this.statusFilter;
                const res = await api.get('/admin/drives', { params });
                this.drives = res.data;
            } catch (err) { console.error(err); }
        },
        async approve(id) { await api.put(`/admin/drives/${id}/approve`); this.fetchDrives(); },
        async reject(id) { await api.put(`/admin/drives/${id}/reject`); this.fetchDrives(); },
        async closeDrive(id) { await api.put(`/admin/drives/${id}/close`); this.fetchDrives(); },
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};
