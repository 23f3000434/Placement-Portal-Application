const RegisterPage = {
    template: `
    <div class="login-container">
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h3 class="text-center mb-4"><i class="bi bi-person-plus-fill text-primary"></i> Register</h3>
                <div v-if="error" class="alert alert-danger alert-dismissible">
                    {{ error }}
                    <button type="button" class="btn-close" @click="error=''"></button>
                </div>
                <form @submit.prevent="handleRegister">
                    <div class="mb-3">
                        <label class="form-label">I am a</label>
                        <select class="form-select" v-model="role" required>
                            <option value="">Select role</option>
                            <option value="student">Student</option>
                            <option value="company">Company</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" v-model="email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" v-model="password" required minlength="6">
                    </div>
                    <template v-if="role === 'student'">
                        <div class="mb-3">
                            <label class="form-label">Full Name</label>
                            <input type="text" class="form-control" v-model="name" required>
                        </div>
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <label class="form-label">Branch</label>
                                <select class="form-select" v-model="branch" required>
                                    <option value="">Select</option>
                                    <option v-for="b in branches" :value="b">{{ b }}</option>
                                </select>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">CGPA</label>
                                <input type="number" step="0.01" min="0" max="10" class="form-control" v-model="cgpa" required>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label">Year</label>
                                <input type="number" min="2020" max="2030" class="form-control" v-model="year" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Phone</label>
                            <input type="tel" class="form-control" v-model="phone">
                        </div>
                    </template>
                    <template v-if="role === 'company'">
                        <div class="mb-3">
                            <label class="form-label">Company Name</label>
                            <input type="text" class="form-control" v-model="company_name" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">HR Contact Name</label>
                            <input type="text" class="form-control" v-model="hr_contact">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Website</label>
                            <input type="url" class="form-control" v-model="website" placeholder="https://">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" v-model="description" rows="3"></textarea>
                        </div>
                    </template>
                    <button type="submit" class="btn btn-primary w-100" :disabled="loading || !role">
                        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                        {{ loading ? 'Registering...' : 'Register' }}
                    </button>
                </form>
                <p class="text-center mt-3 mb-0">
                    Already have an account? <router-link to="/login">Login here</router-link>
                </p>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            role: '', email: '', password: '', error: '', loading: false,
            name: '', branch: '', cgpa: '', year: 2026, phone: '',
            company_name: '', hr_contact: '', website: '', description: '',
            branches: ['CSE', 'ECE', 'EE', 'ME', 'CE', 'IT', 'CH', 'BT'],
        };
    },
    methods: {
        async handleRegister() {
            this.loading = true;
            this.error = '';
            try {
                const payload = { email: this.email, password: this.password, role: this.role };
                if (this.role === 'student') {
                    Object.assign(payload, { name: this.name, branch: this.branch, cgpa: this.cgpa, year: this.year, phone: this.phone });
                } else {
                    Object.assign(payload, { company_name: this.company_name, hr_contact: this.hr_contact, website: this.website, description: this.description });
                }
                const res = await api.post('/auth/register', payload);
                localStorage.setItem('token', res.data.token);
                localStorage.setItem('role', res.data.role);
                localStorage.setItem('user_id', res.data.user_id);
                const routes = { admin: '/admin', company: '/company', student: '/student' };
                this.$router.push(routes[res.data.role] || '/login');
            } catch (err) {
                this.error = err.response?.data?.error || 'Registration failed';
            } finally {
                this.loading = false;
            }
        }
    }
};
