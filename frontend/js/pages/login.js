const LoginPage = {
    template: `
    <div class="login-container">
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h3 class="text-center mb-4"><i class="bi bi-mortarboard-fill text-primary"></i> Placement Portal</h3>
                <div v-if="error" class="alert alert-danger alert-dismissible">
                    {{ error }}
                    <button type="button" class="btn-close" @click="error=''"></button>
                </div>
                <form @submit.prevent="handleLogin">
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" v-model="email" required placeholder="Enter your email">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" v-model="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                        {{ loading ? 'Logging in...' : 'Login' }}
                    </button>
                </form>
                <p class="text-center mt-3 mb-0">
                    Don't have an account? <router-link to="/register">Register here</router-link>
                </p>
            </div>
        </div>
    </div>
    `,
    data() {
        return { email: '', password: '', error: '', loading: false };
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            this.error = '';
            try {
                const res = await api.post('/auth/login', { email: this.email, password: this.password });
                localStorage.setItem('token', res.data.token);
                localStorage.setItem('role', res.data.role);
                localStorage.setItem('user_id', res.data.user_id);
                const routes = { admin: '/admin', company: '/company', student: '/student' };
                this.$router.push(routes[res.data.role] || '/login');
            } catch (err) {
                this.error = err.response?.data?.error || 'Login failed';
            } finally {
                this.loading = false;
            }
        }
    }
};
