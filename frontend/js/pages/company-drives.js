const CompanyDrives = {
    template: `
    <div>
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>My Placement Drives</h2>
            <button class="btn btn-primary" @click="showCreateModal = true">
                <i class="bi bi-plus-lg"></i> Create Drive
            </button>
        </div>
        <div v-if="drives.length === 0" class="empty-state">
            <i class="bi bi-briefcase"></i>
            <p>No drives created yet</p>
        </div>
        <div class="row g-3">
            <div class="col-md-6" v-for="d in drives" :key="d.id">
                <div class="card shadow-sm">
                    <div class="card-header d-flex justify-content-between">
                        <strong>{{ d.job_title }}</strong>
                        <span class="badge" :class="'badge-' + d.status">{{ d.status }}</span>
                    </div>
                    <div class="card-body">
                        <p class="text-muted small">{{ d.job_description?.substring(0, 150) }}...</p>
                        <div class="row text-center">
                            <div class="col"><small class="text-muted">Package</small><br><strong>{{ d.package || '-' }}</strong></div>
                            <div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{ d.eligibility_cgpa || 'Any' }}</strong></div>
                            <div class="col"><small class="text-muted">Applications</small><br><strong>{{ d.total_applications }}</strong></div>
                        </div>
                        <hr>
                        <small class="text-muted">Deadline: {{ formatDate(d.deadline) }}</small>
                        <div class="mt-2">
                            <router-link :to="'/company/drives/' + d.id + '/applications'" class="btn btn-sm btn-outline-primary me-1">
                                <i class="bi bi-people"></i> View Applications
                            </router-link>
                            <button v-if="d.status === 'approved'" class="btn btn-sm btn-outline-secondary" @click="closeDrive(d.id)">
                                <i class="bi bi-lock"></i> Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <!-- Create Drive Modal -->
        <div v-if="showCreateModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Create Placement Drive</h5>
                        <button type="button" class="btn-close" @click="showCreateModal = false"></button>
                    </div>
                    <form @submit.prevent="createDrive">
                        <div class="modal-body">
                            <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
                            <div class="mb-3">
                                <label class="form-label">Job Title *</label>
                                <input type="text" class="form-control" v-model="form.job_title" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Job Description *</label>
                                <textarea class="form-control" v-model="form.job_description" rows="4" required></textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Package</label>
                                    <input type="text" class="form-control" v-model="form.package" placeholder="e.g., 6 LPA">
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Min CGPA</label>
                                    <input type="number" step="0.1" min="0" max="10" class="form-control" v-model="form.eligibility_cgpa">
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label">Target Year</label>
                                    <input type="number" min="2020" max="2030" class="form-control" v-model="form.eligibility_year">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Eligible Branches (comma-separated)</label>
                                    <input type="text" class="form-control" v-model="form.eligibility_branch" placeholder="CSE,ECE,IT">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Application Deadline *</label>
                                    <input type="datetime-local" class="form-control" v-model="form.deadline" required>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
                            <button type="submit" class="btn btn-primary" :disabled="creating">
                                {{ creating ? 'Creating...' : 'Create Drive' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            drives: [], showCreateModal: false, creating: false, formError: '',
            form: { job_title: '', job_description: '', package: '', eligibility_cgpa: 0, eligibility_branch: '', eligibility_year: 2026, deadline: '' }
        };
    },
    mounted() { this.fetchDrives(); },
    methods: {
        async fetchDrives() {
            try { const res = await api.get('/company/drives'); this.drives = res.data; } catch (err) { console.error(err); }
        },
        async createDrive() {
            this.creating = true; this.formError = '';
            try {
                await api.post('/company/drives', this.form);
                this.showCreateModal = false;
                this.form = { job_title: '', job_description: '', package: '', eligibility_cgpa: 0, eligibility_branch: '', eligibility_year: 2026, deadline: '' };
                this.fetchDrives();
            } catch (err) { this.formError = err.response?.data?.error || 'Failed to create drive'; } finally { this.creating = false; }
        },
        async closeDrive(id) { await api.put(`/company/drives/${id}/close`); this.fetchDrives(); },
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};
