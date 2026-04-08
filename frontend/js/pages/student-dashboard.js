const StudentDashboard = {
    template: `
    <div>
        <h2 class="mb-4">Welcome, {{ data.name }}</h2>
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3" v-for="stat in stats" :key="stat.label">
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
            <div class="col-md-7">
                <div class="card shadow-sm">
                    <div class="card-header d-flex justify-content-between">
                        <strong>Upcoming Drives</strong>
                        <router-link to="/student/drives" class="btn btn-sm btn-outline-primary">View All</router-link>
                    </div>
                    <div class="card-body p-0">
                        <div v-if="!data.upcoming_drives || data.upcoming_drives.length === 0" class="text-center text-muted py-4">No upcoming drives</div>
                        <div class="table-responsive" v-else>
                            <table class="table table-hover mb-0">
                                <thead><tr><th>Company</th><th>Position</th><th>Package</th><th>Deadline</th><th></th></tr></thead>
                                <tbody>
                                    <tr v-for="d in data.upcoming_drives" :key="d.id">
                                        <td>{{ d.company_name }}</td>
                                        <td>{{ d.job_title }}</td>
                                        <td>{{ d.package || '-' }}</td>
                                        <td>{{ formatDate(d.deadline) }}</td>
                                        <td>
                                            <span v-if="d.already_applied" class="badge bg-success">Applied</span>
                                            <router-link v-else to="/student/drives" class="btn btn-sm btn-outline-primary">Apply</router-link>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-header"><strong>Upcoming Interviews</strong></div>
                    <div class="card-body">
                        <div v-if="!data.upcoming_interviews || data.upcoming_interviews.length === 0" class="text-muted text-center py-3">No interviews scheduled</div>
                        <div v-for="i in (data.upcoming_interviews || [])" :key="i.id" class="border-bottom pb-2 mb-2">
                            <strong>{{ i.drive_title }}</strong> <small class="text-muted">- {{ i.company_name }}</small><br>
                            <small><i class="bi bi-calendar"></i> {{ formatDateTime(i.scheduled_date) }}</small><br>
                            <small><i class="bi bi-geo-alt"></i> {{ i.location || 'TBD' }} ({{ i.interview_type }})</small>
                        </div>
                    </div>
                </div>
                <div class="card shadow-sm mt-3">
                    <div class="card-header"><strong>Your Profile</strong></div>
                    <div class="card-body">
                        <p class="mb-1"><strong>Branch:</strong> {{ data.branch }}</p>
                        <p class="mb-1"><strong>CGPA:</strong> {{ data.cgpa }}</p>
                        <p class="mb-0"><strong>Year:</strong> {{ data.year }}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() { return { data: {} }; },
    computed: {
        stats() {
            return [
                { label: 'Applications', value: this.data.total_applications || 0, icon: 'bi bi-file-earmark-text-fill', color: '#3498db' },
                { label: 'Pending', value: this.data.pending || 0, icon: 'bi bi-hourglass-split', color: '#f39c12' },
                { label: 'Shortlisted', value: this.data.shortlisted || 0, icon: 'bi bi-star-fill', color: '#9b59b6' },
                { label: 'Selected', value: this.data.selected || 0, icon: 'bi bi-trophy-fill', color: '#27ae60' },
            ];
        }
    },
    async mounted() {
        try { const res = await api.get('/student/dashboard'); this.data = res.data; } catch (err) { console.error(err); }
    },
    methods: {
        formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; },
        formatDateTime(d) { return d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'; }
    }
};
