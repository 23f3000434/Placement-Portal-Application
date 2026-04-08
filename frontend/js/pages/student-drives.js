const StudentDrives = {
    template: `
    <div>
        <h2 class="mb-4">Available Placement Drives</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Search drives..." v-model="search" @input="fetchDrives">
            </div>
            <div class="col-md-3">
                <select class="form-select" v-model="branchFilter" @change="fetchDrives">
                    <option value="">All Branches</option>
                    <option v-for="b in branches" :value="b">{{ b }}</option>
                </select>
            </div>
        </div>
        <div v-if="drives.length === 0" class="empty-state">
            <i class="bi bi-briefcase"></i>
            <p>No drives available right now</p>
        </div>
        <div class="row g-3">
            <div class="col-md-6" v-for="d in drives" :key="d.id">
                <div class="card shadow-sm">
                    <div class="card-header d-flex justify-content-between">
                        <div>
                            <strong>{{ d.job_title }}</strong>
                            <small class="text-muted d-block">{{ d.company_name }}</small>
                        </div>
                        <span class="badge bg-primary align-self-start">{{ d.package || 'Not specified' }}</span>
                    </div>
                    <div class="card-body">
                        <p class="text-muted small">{{ d.job_description?.substring(0, 200) }}...</p>
                        <div class="row text-center mb-3">
                            <div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{ d.eligibility_cgpa || 'Any' }}</strong></div>
                            <div class="col"><small class="text-muted">Branches</small><br><strong>{{ d.eligibility_branch || 'All' }}</strong></div>
                            <div class="col"><small class="text-muted">Deadline</small><br><strong>{{ formatDate(d.deadline) }}</strong></div>
                        </div>
                        <button v-if="!d.already_applied" class="btn btn-primary w-100" @click="apply(d.id)" :disabled="applying === d.id">
                            <span v-if="applying === d.id" class="spinner-border spinner-border-sm me-2"></span>
                            {{ applying === d.id ? 'Applying...' : 'Apply Now' }}
                        </button>
                        <button v-else class="btn btn-success w-100" disabled>
                            <i class="bi bi-check-circle"></i> Already Applied
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return { drives: [], search: '', branchFilter: '', applying: null, branches: ['CSE', 'ECE', 'EE', 'ME', 'CE', 'IT', 'CH', 'BT'] };
    },
    mounted() { this.fetchDrives(); },
    methods: {
        async fetchDrives() {
            try {
                const params = {};
                if (this.search) params.search = this.search;
                if (this.branchFilter) params.branch = this.branchFilter;
                const res = await api.get('/student/drives', { params });
                this.drives = res.data;
            } catch (err) { console.error(err); }
        },
        async apply(driveId) {
            this.applying = driveId;
            try {
                await api.post(`/student/drives/${driveId}/apply`);
                this.fetchDrives();
            } catch (err) {
                alert(err.response?.data?.error || 'Failed to apply');
            } finally { this.applying = null; }
        },
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
    }
};
