const AdminStudents = {
    template: `
    <div>
        <h2 class="mb-4">Manage Students</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Search by name or branch..." v-model="search" @input="fetchStudents">
            </div>
        </div>
        <div v-if="students.length === 0" class="empty-state">
            <i class="bi bi-people"></i>
            <p>No students found</p>
        </div>
        <div class="table-responsive" v-else>
            <table class="table table-hover bg-white rounded shadow-sm">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Branch</th>
                        <th>CGPA</th>
                        <th>Year</th>
                        <th>Applications</th>
                        <th>Selected</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="s in students" :key="s.id">
                        <td><strong>{{ s.name }}</strong></td>
                        <td>{{ s.email }}</td>
                        <td>{{ s.branch }}</td>
                        <td>{{ s.cgpa }}</td>
                        <td>{{ s.year }}</td>
                        <td>{{ s.total_applications }}</td>
                        <td>{{ s.selected_count }}</td>
                        <td>
                            <span class="badge" :class="s.is_active ? 'bg-success' : 'bg-danger'">{{ s.is_active ? 'Active' : 'Inactive' }}</span>
                        </td>
                        <td>
                            <button class="btn btn-sm" :class="s.is_active ? 'btn-outline-warning' : 'btn-outline-success'" @click="toggleActive(s.user_id)">
                                {{ s.is_active ? 'Deactivate' : 'Activate' }}
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { students: [], search: '' };
    },
    mounted() { this.fetchStudents(); },
    methods: {
        async fetchStudents() {
            try {
                const params = {};
                if (this.search) params.search = this.search;
                const res = await api.get('/admin/students', { params });
                this.students = res.data;
            } catch (err) { console.error(err); }
        },
        async toggleActive(userId) {
            await api.put(`/admin/users/${userId}/toggle-active`);
            this.fetchStudents();
        }
    }
};
