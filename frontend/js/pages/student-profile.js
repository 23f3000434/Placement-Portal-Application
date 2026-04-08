const StudentProfile = {
    template: `
    <div>
        <h2 class="mb-4">My Profile</h2>
        <div v-if="success" class="alert alert-success alert-dismissible">{{ success }}<button type="button" class="btn-close" @click="success=''"></button></div>
        <div v-if="error" class="alert alert-danger alert-dismissible">{{ error }}<button type="button" class="btn-close" @click="error=''"></button></div>
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <form @submit.prevent="updateProfile" novalidate>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Full Name *</label>
                            <input type="text" class="form-control" :class="{'is-invalid': v.name}" v-model="profile.name" required minlength="2">
                            <div class="invalid-feedback">{{ v.name }}</div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control" :value="profile.email" disabled>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4 mb-3">
                            <label class="form-label">Branch *</label>
                            <select class="form-select" :class="{'is-invalid': v.branch}" v-model="profile.branch" required>
                                <option v-for="b in branches" :value="b">{{ b }}</option>
                            </select>
                            <div class="invalid-feedback">{{ v.branch }}</div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label class="form-label">CGPA *</label>
                            <input type="number" step="0.01" min="0" max="10" class="form-control" :class="{'is-invalid': v.cgpa}" v-model="profile.cgpa" required>
                            <div class="invalid-feedback">{{ v.cgpa }}</div>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label class="form-label">Graduation Year *</label>
                            <input type="number" min="2020" max="2035" class="form-control" :class="{'is-invalid': v.year}" v-model="profile.year" required>
                            <div class="invalid-feedback">{{ v.year }}</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Phone</label>
                            <input type="tel" class="form-control" v-model="profile.phone" pattern="[0-9]{10}" placeholder="10-digit number">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Resume URL</label>
                            <input type="url" class="form-control" v-model="profile.resume_url" placeholder="https://drive.google.com/...">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" :disabled="saving">
                        <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
                        {{ saving ? 'Saving...' : 'Save Changes' }}
                    </button>
                </form>
            </div>
        </div>
        <!-- Resume Upload -->
        <div class="card shadow-sm">
            <div class="card-header"><strong>Upload Resume</strong></div>
            <div class="card-body">
                <p v-if="profile.resume_url" class="mb-2">Current: <a :href="profile.resume_url" target="_blank">{{ profile.resume_url }}</a></p>
                <form @submit.prevent="uploadResume">
                    <div class="input-group">
                        <input type="file" class="form-control" accept=".pdf,.doc,.docx" ref="resumeFile">
                        <button type="submit" class="btn btn-outline-primary" :disabled="uploading">
                            {{ uploading ? 'Uploading...' : 'Upload' }}
                        </button>
                    </div>
                    <small class="text-muted">Accepted: PDF, DOC, DOCX</small>
                </form>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            profile: {}, saving: false, uploading: false, success: '', error: '',
            branches: ['CSE', 'ECE', 'EE', 'ME', 'CE', 'IT', 'CH', 'BT'],
            v: {}
        };
    },
    async mounted() {
        try { const res = await api.get('/student/profile'); this.profile = res.data; } catch (err) { console.error(err); }
    },
    methods: {
        validate() {
            this.v = {};
            if (!this.profile.name || this.profile.name.trim().length < 2) this.v.name = 'Name must be at least 2 characters';
            if (!this.profile.branch) this.v.branch = 'Branch is required';
            const cgpa = parseFloat(this.profile.cgpa);
            if (isNaN(cgpa) || cgpa < 0 || cgpa > 10) this.v.cgpa = 'CGPA must be between 0 and 10';
            const year = parseInt(this.profile.year);
            if (isNaN(year) || year < 2020 || year > 2035) this.v.year = 'Year must be between 2020 and 2035';
            return Object.keys(this.v).length === 0;
        },
        async updateProfile() {
            if (!this.validate()) return;
            this.saving = true; this.success = ''; this.error = '';
            try {
                await api.put('/student/profile', this.profile);
                this.success = 'Profile updated successfully!';
            } catch (err) { this.error = err.response?.data?.error || 'Failed to update'; } finally { this.saving = false; }
        },
        async uploadResume() {
            const file = this.$refs.resumeFile?.files?.[0];
            if (!file) { this.error = 'Please select a file'; return; }
            this.uploading = true; this.error = ''; this.success = '';
            const formData = new FormData();
            formData.append('resume', file);
            try {
                const res = await api.post('/student/upload-resume', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                this.profile.resume_url = res.data.resume_url;
                this.success = 'Resume uploaded successfully!';
            } catch (err) { this.error = err.response?.data?.error || 'Upload failed'; } finally { this.uploading = false; }
        }
    }
};
