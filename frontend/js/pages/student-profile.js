const StudentProfile = {
    template: `
    <div>
        <h2 class="mb-4">My Profile</h2>
        <div v-if="success" class="alert alert-success alert-dismissible">
            {{ success }}
            <button type="button" class="btn-close" @click="success=''"></button>
        </div>
        <div v-if="error" class="alert alert-danger alert-dismissible">
            {{ error }}
            <button type="button" class="btn-close" @click="error=''"></button>
        </div>
        <div class="card shadow-sm">
            <div class="card-body">
                <form @submit.prevent="updateProfile">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Full Name</label>
                            <input type="text" class="form-control" v-model="profile.name" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control" :value="profile.email" disabled>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4 mb-3">
                            <label class="form-label">Branch</label>
                            <select class="form-select" v-model="profile.branch" required>
                                <option v-for="b in branches" :value="b">{{ b }}</option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label class="form-label">CGPA</label>
                            <input type="number" step="0.01" min="0" max="10" class="form-control" v-model="profile.cgpa" required>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label class="form-label">Graduation Year</label>
                            <input type="number" min="2020" max="2030" class="form-control" v-model="profile.year" required>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Phone</label>
                            <input type="tel" class="form-control" v-model="profile.phone">
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
    </div>
    `,
    data() {
        return {
            profile: {}, saving: false, success: '', error: '',
            branches: ['CSE', 'ECE', 'EE', 'ME', 'CE', 'IT', 'CH', 'BT']
        };
    },
    async mounted() {
        try { const res = await api.get('/student/profile'); this.profile = res.data; } catch (err) { console.error(err); }
    },
    methods: {
        async updateProfile() {
            this.saving = true; this.success = ''; this.error = '';
            try {
                await api.put('/student/profile', this.profile);
                this.success = 'Profile updated successfully!';
            } catch (err) { this.error = err.response?.data?.error || 'Failed to update'; } finally { this.saving = false; }
        }
    }
};
