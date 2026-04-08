const AdminCompanies = {
    template: `
    <div>
        <h2 class="mb-4">Manage Companies</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Search companies..." v-model="search" @input="fetchCompanies">
            </div>
            <div class="col-md-3">
                <select class="form-select" v-model="statusFilter" @change="fetchCompanies">
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                </select>
            </div>
        </div>
        <div v-if="companies.length === 0" class="empty-state">
            <i class="bi bi-building"></i>
            <p>No companies found</p>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Email</th>
                        <th>HR Contact</th>
                        <th>Status</th>
                        <th>Drives</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="c in companies" :key="c.id">
                        <td><strong>{{ c.company_name }}</strong></td>
                        <td>{{ c.email }}</td>
                        <td>{{ c.hr_contact || '-' }}</td>
                        <td>
                            <span class="badge" :class="'badge-' + c.approval_status">{{ c.approval_status }}</span>
                            <span v-if="c.is_blacklisted" class="badge bg-dark ms-1">Blacklisted</span>
                        </td>
                        <td>{{ c.total_drives }}</td>
                        <td>
                            <button v-if="c.approval_status === 'pending'" class="btn btn-success btn-sm me-1" @click="approve(c.id)">
                                <i class="bi bi-check-lg"></i>
                            </button>
                            <button v-if="c.approval_status === 'pending'" class="btn btn-danger btn-sm me-1" @click="reject(c.id)">
                                <i class="bi bi-x-lg"></i>
                            </button>
                            <button class="btn btn-sm me-1" :class="c.is_blacklisted ? 'btn-secondary' : 'btn-outline-dark'" @click="toggleBlacklist(c.id)">
                                <i class="bi bi-slash-circle"></i> {{ c.is_blacklisted ? 'Unblock' : 'Blacklist' }}
                            </button>
                            <button class="btn btn-sm" :class="c.is_active === false ? 'btn-outline-success' : 'btn-outline-warning'" @click="toggleActive(c.user_id)">
                                {{ c.is_active === false ? 'Activate' : 'Deactivate' }}
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { companies: [], search: '', statusFilter: this.$route.query.status || '' };
    },
    mounted() { this.fetchCompanies(); },
    methods: {
        async fetchCompanies() {
            try {
                const params = {};
                if (this.search) params.search = this.search;
                if (this.statusFilter) params.status = this.statusFilter;
                const res = await api.get('/admin/companies', { params });
                this.companies = res.data;
            } catch (err) { console.error(err); }
        },
        async approve(id) {
            await api.put(`/admin/companies/${id}/approve`);
            this.fetchCompanies();
        },
        async reject(id) {
            await api.put(`/admin/companies/${id}/reject`);
            this.fetchCompanies();
        },
        async toggleBlacklist(id) {
            await api.put(`/admin/companies/${id}/blacklist`);
            this.fetchCompanies();
        },
        async toggleActive(userId) {
            await api.put(`/admin/users/${userId}/toggle-active`);
            this.fetchCompanies();
        }
    }
};
