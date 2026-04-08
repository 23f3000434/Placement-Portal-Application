const CompanyInterviews = {
    template: `
    <div>
        <h2 class="mb-4"><i class="bi bi-calendar-event"></i> Interview Management</h2>
        <div class="mb-3">
            <select class="form-select" style="max-width:400px" v-model="selectedDrive" @change="fetchInterviews">
                <option value="">Select a drive</option>
                <option v-for="d in drives" :key="d.id" :value="d.id">{{ d.job_title }} ({{ d.total_applications }} applicants)</option>
            </select>
        </div>
        <div v-if="selectedDrive">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Scheduled Interviews</h5>
                <button class="btn btn-primary btn-sm" @click="showScheduleModal = true"><i class="bi bi-plus"></i> Schedule Interview</button>
            </div>
            <div v-if="interviews.length === 0" class="empty-state"><i class="bi bi-calendar-x"></i><p>No interviews scheduled for this drive</p></div>
            <div class="table-responsive" v-else>
                <table class="table table-hover bg-white rounded shadow-sm">
                    <thead>
                        <tr><th>Student</th><th>Date & Time</th><th>Type</th><th>Location/Link</th><th>Status</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        <tr v-for="i in interviews" :key="i.id">
                            <td><strong>{{ i.student_name }}</strong><br><small class="text-muted">{{ i.student_email }}</small></td>
                            <td>{{ formatDate(i.scheduled_date) }}</td>
                            <td><span class="badge" :class="i.interview_type === 'online' ? 'bg-info' : 'bg-secondary'">{{ i.interview_type }}</span></td>
                            <td>{{ i.location || '-' }}</td>
                            <td><span class="badge" :class="{'bg-primary': i.status === 'scheduled', 'bg-success': i.status === 'completed', 'bg-danger': i.status === 'cancelled'}">{{ i.status }}</span></td>
                            <td>
                                <select class="form-select form-select-sm" style="width:auto;display:inline" :value="i.status" @change="updateInterview(i.id, $event.target.value)">
                                    <option value="scheduled">Scheduled</option>
                                    <option value="completed">Completed</option>
                                    <option value="cancelled">Cancelled</option>
                                </select>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <!-- Schedule Modal -->
        <div v-if="showScheduleModal" class="modal d-block" style="background:rgba(0,0,0,0.5)">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header"><h5 class="modal-title">Schedule Interview</h5><button class="btn-close" @click="showScheduleModal=false"></button></div>
                    <form @submit.prevent="scheduleInterview">
                        <div class="modal-body">
                            <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
                            <div class="mb-3">
                                <label class="form-label">Student (from applicants) *</label>
                                <select class="form-select" v-model="form.student_id" required>
                                    <option value="">Select student</option>
                                    <option v-for="a in applicants" :key="a.student_id" :value="a.student_id">{{ a.student_name }} ({{ a.student_branch }}, CGPA: {{ a.student_cgpa }})</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Date & Time *</label>
                                <input type="datetime-local" class="form-control" v-model="form.scheduled_date" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Type</label>
                                <select class="form-select" v-model="form.interview_type">
                                    <option value="online">Online</option>
                                    <option value="in-person">In-Person</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Location / Meeting Link</label>
                                <input type="text" class="form-control" v-model="form.location" placeholder="Zoom link or room number">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Notes</label>
                                <textarea class="form-control" v-model="form.notes" rows="2"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" @click="showScheduleModal=false">Cancel</button>
                            <button type="submit" class="btn btn-primary" :disabled="scheduling">{{ scheduling ? 'Scheduling...' : 'Schedule' }}</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            drives: [], interviews: [], applicants: [], selectedDrive: '',
            showScheduleModal: false, scheduling: false, formError: '',
            form: { student_id: '', scheduled_date: '', interview_type: 'online', location: '', notes: '' }
        };
    },
    async mounted() {
        try { const res = await api.get('/company/drives'); this.drives = res.data; } catch (err) { console.error(err); }
    },
    methods: {
        async fetchInterviews() {
            if (!this.selectedDrive) return;
            try {
                const [intRes, appRes] = await Promise.all([
                    api.get(`/company/drives/${this.selectedDrive}/interviews`),
                    api.get(`/company/drives/${this.selectedDrive}/applications`)
                ]);
                this.interviews = intRes.data;
                this.applicants = appRes.data;
            } catch (err) { console.error(err); }
        },
        async scheduleInterview() {
            this.scheduling = true; this.formError = '';
            try {
                await api.post(`/company/drives/${this.selectedDrive}/interviews`, this.form);
                this.showScheduleModal = false;
                this.form = { student_id: '', scheduled_date: '', interview_type: 'online', location: '', notes: '' };
                this.fetchInterviews();
            } catch (err) { this.formError = err.response?.data?.error || 'Failed to schedule'; } finally { this.scheduling = false; }
        },
        async updateInterview(id, status) {
            try { await api.put(`/company/interviews/${id}`, { status }); this.fetchInterviews(); } catch (err) { console.error(err); }
        },
        formatDate(d) { return d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'; }
    }
};
