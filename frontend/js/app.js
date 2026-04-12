const {createRouter,createWebHashHistory}=VueRouter;

// ═══════════════════════════ PAGINATION COMPONENT ═══════════════════════════
const Pagination={props:["page","pages","total"],emits:["change"],template:`
<nav v-if="pages>1" class="d-flex justify-content-between align-items-center mt-3">
  <small class="text-muted">Showing page {{page}} of {{pages}} ({{total}} total)</small>
  <div>
    <button class="btn btn-outline-dark btn-sm me-1" :disabled="page<=1" @click="$emit('change',page-1)">‹ Prev</button>
    <button class="btn btn-outline-dark btn-sm" :disabled="page>=pages" @click="$emit('change',page+1)">Next ›</button>
  </div>
</nav>`};

// ═══════════════════════════ SIDEBAR ═══════════════════════════
const Sidebar={props:["links","open"],emits:["toggle"],template:`
<div>
  <div class="mobile-nav">
    <span class="brand"><i class="bi bi-briefcase-fill"></i> PPA</span>
    <button class="btn" @click="$emit('toggle')"><i class="bi bi-list"></i></button>
  </div>
  <div class="sidebar-overlay" :class="{open:open}" @click="$emit('toggle')"></div>
  <div class="sidebar d-flex flex-column" :class="{open:open}">
    <div class="brand"><i class="bi bi-briefcase-fill"></i> PPA</div>
    <nav class="nav flex-column mt-2">
      <router-link v-for="l in links" :key="l.to" :to="l.to" class="nav-link" :class="{active:$route.path===l.to}" @click="$emit('toggle')"><i :class="l.icon"></i>{{l.label}}</router-link>
    </nav>
    <div class="mt-auto p-3"><button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')"><i class="bi bi-box-arrow-left"></i> Logout</button></div>
  </div>
</div>`};

function makeLayout(links){return{components:{Sidebar},template:`<div><sidebar :links="links" :open="sidebarOpen" @toggle="sidebarOpen=!sidebarOpen" @logout="logout"/><div class="main"><router-view/></div></div>`,data(){return{links,sidebarOpen:false}},methods:{logout}}}
const AdminLayout=makeLayout([{to:"/admin",icon:"bi bi-speedometer2",label:"Dashboard"},{to:"/admin/companies",icon:"bi bi-building",label:"Companies"},{to:"/admin/drives",icon:"bi bi-briefcase",label:"Drives"},{to:"/admin/students",icon:"bi bi-people",label:"Students"},{to:"/admin/applications",icon:"bi bi-file-text",label:"Applications"},{to:"/admin/stats",icon:"bi bi-bar-chart",label:"Reports"}]);
const CompanyLayout=makeLayout([{to:"/company",icon:"bi bi-speedometer2",label:"Dashboard"},{to:"/company/drives",icon:"bi bi-briefcase",label:"My Drives"},{to:"/company/profile",icon:"bi bi-person",label:"Profile"}]);
const StudentLayout=makeLayout([{to:"/student",icon:"bi bi-speedometer2",label:"Dashboard"},{to:"/student/drives",icon:"bi bi-briefcase",label:"Browse Drives"},{to:"/student/applications",icon:"bi bi-file-text",label:"My Applications"},{to:"/student/profile",icon:"bi bi-person",label:"Profile"}]);

// ═══════════════════════════ LOGIN ═══════════════════════════
const LoginPage={template:`
<div class="login-box">
  <div class="card border-dark">
    <div class="card-body p-4">
      <h4 class="text-center mb-4">Placement Portal</h4>
      <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
      <form @submit.prevent="go">
        <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" v-model="email" required></div>
        <div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" v-model="pw" required></div>
        <button class="btn btn-dark w-100" :disabled="loading">{{loading?"...":"Login"}}</button>
      </form>
      <p class="text-center mt-3 mb-0"><router-link to="/register">Register</router-link></p>
    </div>
  </div>
</div>`,
data(){return{email:"",pw:"",err:"",loading:false}},
methods:{async go(){this.loading=true;this.err="";try{const r=await api.post("/auth/login",{email:this.email,password:this.pw});localStorage.setItem("token",r.data.token);localStorage.setItem("role",r.data.role);this.$router.push("/"+r.data.role)}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.loading=false}}}};

// ═══════════════════════════ REGISTER ═══════════════════════════
const RegisterPage={template:`
<div class="login-box">
  <div class="card border-dark">
    <div class="card-body p-4">
      <h4 class="text-center mb-4">Register</h4>
      <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
      <form @submit.prevent="go">
        <div class="mb-3"><label class="form-label">Role</label><select class="form-select" v-model="role" required><option value="">Select</option><option value="student">Student</option><option value="company">Company</option></select></div>
        <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" v-model="email" required></div>
        <div class="mb-3"><label class="form-label">Password (6+ chars)</label><input type="password" class="form-control" v-model="pw" required minlength="6"></div>
        <template v-if="role==='student'">
          <div class="mb-3"><label class="form-label">Name</label><input class="form-control" v-model="name" required></div>
          <div class="row"><div class="col mb-3"><label class="form-label">Branch</label><select class="form-select" v-model="branch" required><option v-for="b in branches" :value="b">{{b}}</option></select></div>
          <div class="col mb-3"><label class="form-label">CGPA</label><input type="number" step="0.01" min="0" max="10" class="form-control" v-model="cgpa" required></div>
          <div class="col mb-3"><label class="form-label">Year</label><input type="number" class="form-control" v-model="year" required></div></div>
          <div class="mb-3"><label class="form-label">Phone</label><input class="form-control" v-model="phone"></div>
        </template>
        <template v-if="role==='company'">
          <div class="mb-3"><label class="form-label">Company Name</label><input class="form-control" v-model="company_name" required></div>
          <div class="mb-3"><label class="form-label">HR Contact</label><input class="form-control" v-model="hr_contact"></div>
          <div class="mb-3"><label class="form-label">Website</label><input class="form-control" v-model="website"></div>
          <div class="mb-3"><label class="form-label">Description</label><textarea class="form-control" v-model="description" rows="2"></textarea></div>
        </template>
        <button class="btn btn-dark w-100" :disabled="loading||!role">{{loading?"...":"Register"}}</button>
      </form>
      <p class="text-center mt-3 mb-0"><router-link to="/login">Login</router-link></p>
    </div>
  </div>
</div>`,
data(){return{role:"",email:"",pw:"",err:"",loading:false,name:"",branch:"",cgpa:"",year:2026,phone:"",company_name:"",hr_contact:"",website:"",description:"",branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"]}},
methods:{async go(){this.loading=true;this.err="";try{const p={email:this.email,password:this.pw,role:this.role};if(this.role==="student")Object.assign(p,{name:this.name,branch:this.branch,cgpa:this.cgpa,year:this.year,phone:this.phone});else Object.assign(p,{company_name:this.company_name,hr_contact:this.hr_contact,website:this.website,description:this.description});const r=await api.post("/auth/register",p);localStorage.setItem("token",r.data.token);localStorage.setItem("role",r.data.role);this.$router.push("/"+r.data.role)}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.loading=false}}}};

// ═══════════════════════════ ADMIN PAGES ═══════════════════════════
const AdminDashboard={template:`
<div>
  <h4 class="mb-4">Admin Dashboard</h4>
  <div class="row g-3 mb-4">
    <div class="col-md-3 col-6" v-for="s in stats"><div class="card stat-card p-3 text-center"><div class="val">{{s.v}}</div><div class="lbl">{{s.l}}</div></div></div>
  </div>
</div>`,
data(){return{d:{}}},computed:{stats(){return[{v:this.d.total_students||0,l:"Students"},{v:this.d.total_companies||0,l:"Companies"},{v:this.d.total_drives||0,l:"Drives"},{v:this.d.students_placed||0,l:"Placed"}]}},
async mounted(){try{this.d=(await api.get("/admin/dashboard")).data}catch(e){}}};

const AdminCompanies={components:{Pagination},template:`
<div>
  <h4 class="mb-3">Companies</h4>
  <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search..." v-model="search" @input="load"></div>
  <div class="col-md-3"><select class="form-select" v-model="filter" @change="load"><option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select></div></div>
  <div v-if="!items.length" class="empty"><i class="bi bi-building"></i><p>No companies</p></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>Company</th><th>Email</th><th>Status</th><th>Drives</th><th>Actions</th></tr></thead><tbody>
    <tr v-for="c in items"><td><strong>{{c.company_name}}</strong></td><td>{{c.email}}</td>
    <td><span class="badge" :class="'badge-'+c.approval_status">{{c.approval_status}}</span><span v-if="c.is_blacklisted" class="badge bg-dark ms-1">blocked</span></td>
    <td>{{c.total_drives}}</td>
    <td>
      <button v-if="c.approval_status==='pending'" class="btn btn-dark btn-sm me-1" @click="act(c.id,'approve')">Approve</button>
      <button v-if="c.approval_status==='pending'" class="btn btn-outline-dark btn-sm me-1" @click="act(c.id,'reject')">Reject</button>
      <button class="btn btn-sm" :class="c.is_blacklisted?'btn-outline-dark':'btn-dark'" @click="act(c.id,'blacklist')">{{c.is_blacklisted?"Unblock":"Block"}}</button>
      <button class="btn btn-sm ms-1" :class="c.is_active?'btn-outline-dark':'btn-dark'" @click="toggle(c.user_id)">{{c.is_active?"Deactivate":"Activate"}}</button>
    </td></tr></tbody></table></div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{items:[],search:"",filter:"",page:1,pages:1,total:0}},mounted(){this.load()},
methods:{async load(){const p={page:this.page};if(this.search)p.search=this.search;if(this.filter)p.status=this.filter;const r=(await api.get("/admin/companies",{params:p})).data;this.items=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()},
async act(id,a){await api.put("/admin/companies/"+id+"/"+a);this.load()},
async toggle(uid){await api.put("/admin/users/"+uid+"/toggle-active");this.load()}}};

const AdminDrives={components:{Pagination},template:`
<div>
  <h4 class="mb-3">Placement Drives</h4>
  <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search title or company..." v-model="search" @input="load"></div>
  <div class="col-md-3"><select class="form-select" v-model="filter" @change="load"><option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="closed">Closed</option></select></div></div>
  <div v-if="!items.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives</p></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>Title</th><th>Company</th><th>Package</th><th>Deadline</th><th>Status</th><th>Apps</th><th>Actions</th></tr></thead><tbody>
    <tr v-for="d in items"><td><strong>{{d.job_title}}</strong></td><td>{{d.company_name}}</td><td>{{d.package||"-"}}</td><td>{{fmtDate(d.deadline)}}</td>
    <td><span class="badge" :class="'badge-'+d.status">{{d.status}}</span></td><td>{{d.total_applications}}</td>
    <td>
      <button v-if="d.status==='pending'" class="btn btn-dark btn-sm me-1" @click="act(d.id,'approve')">Approve</button>
      <button v-if="d.status==='pending'" class="btn btn-outline-dark btn-sm me-1" @click="act(d.id,'reject')">Reject</button>
      <button v-if="d.status==='approved'" class="btn btn-outline-dark btn-sm" @click="act(d.id,'close')">Close</button>
    </td></tr></tbody></table></div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{items:[],search:"",filter:"",page:1,pages:1,total:0}},mounted(){this.load()},
methods:{async load(){const p={page:this.page};if(this.search)p.search=this.search;if(this.filter)p.status=this.filter;const r=(await api.get("/admin/drives",{params:p})).data;this.items=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()},
async act(id,a){await api.put("/admin/drives/"+id+"/"+a);this.load()}}};

const AdminStudents={components:{Pagination},template:`
<div>
  <h4 class="mb-3">Students</h4>
  <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search name/branch..." v-model="search" @input="load"></div></div>
  <div v-if="!items.length" class="empty"><i class="bi bi-people"></i><p>No students</p></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Apps</th><th>Selected</th><th>Status</th><th></th></tr></thead><tbody>
    <tr v-for="s in items"><td><strong>{{s.name}}</strong></td><td>{{s.email}}</td><td>{{s.branch}}</td><td>{{s.cgpa}}</td><td>{{s.year}}</td><td>{{s.total_applications}}</td><td>{{s.selected_count}}</td>
    <td><span class="badge" :class="s.is_active?'bg-dark':'bg-secondary'">{{s.is_active?"Active":"Inactive"}}</span></td>
    <td><button class="btn btn-sm" :class="s.is_active?'btn-outline-dark':'btn-dark'" @click="toggle(s.user_id)">{{s.is_active?"Deactivate":"Activate"}}</button></td></tr></tbody></table></div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{items:[],search:"",page:1,pages:1,total:0}},mounted(){this.load()},
methods:{async load(){const p={page:this.page};if(this.search)p.search=this.search;const r=(await api.get("/admin/students",{params:p})).data;this.items=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()},
async toggle(uid){await api.put("/admin/users/"+uid+"/toggle-active");this.load()}}};

const AdminApplications={components:{Pagination},template:`
<div>
  <h4 class="mb-3">All Applications</h4>
  <div v-if="!items.length" class="empty"><i class="bi bi-file-text"></i><p>No applications</p></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>#</th><th>Student</th><th>Branch</th><th>Company</th><th>Drive</th><th>Status</th><th>Date</th></tr></thead><tbody>
    <tr v-for="(a,i) in items"><td>{{(page-1)*20+i+1}}</td><td><strong>{{a.student_name}}</strong></td><td>{{a.student_branch}}</td><td>{{a.company_name}}</td><td>{{a.drive_title}}</td>
    <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td><td>{{fmtDate(a.applied_at)}}</td></tr></tbody></table></div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{items:[],page:1,pages:1,total:0}},mounted(){this.load()},
methods:{async load(){const r=(await api.get("/admin/applications",{params:{page:this.page}})).data;this.items=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()}}};

// ═══════════════════════════ COMPANY PAGES ═══════════════════════════
const CompanyDashboard={template:`
<div>
  <h4 class="mb-3">Company Dashboard</h4>
  <div v-if="d.approval_status==='pending'" class="alert alert-warning">Pending admin approval. Cannot create drives yet.</div>
  <div v-if="d.approval_status==='rejected'" class="alert alert-danger">Registration rejected.</div>
  <div v-if="d.is_blacklisted" class="alert alert-dark">Company blacklisted.</div>
  <div class="row g-3 mb-4">
    <div class="col-md-4 col-6"><div class="card stat-card p-3 text-center"><div class="val">{{d.total_drives||0}}</div><div class="lbl">Drives</div></div></div>
    <div class="col-md-4 col-6"><div class="card stat-card p-3 text-center"><div class="val">{{d.total_applicants||0}}</div><div class="lbl">Applicants</div></div></div>
  </div>
  <div class="card"><div class="card-body"><p><strong>Company:</strong> {{d.company_name}}</p><p><strong>HR:</strong> {{d.hr_contact||"N/A"}}</p><p><strong>Website:</strong> {{d.website||"N/A"}}</p><p><strong>Status:</strong> <span class="badge" :class="'badge-'+d.approval_status">{{d.approval_status}}</span></p></div></div>
</div>`,
data(){return{d:{}}},async mounted(){try{this.d=(await api.get("/company/dashboard")).data}catch(e){}}};

const CompanyProfileEdit={template:`
<div>
  <h4 class="mb-3">Edit Company Profile</h4>
  <div v-if="ok" class="alert alert-success py-2">{{ok}}</div>
  <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
  <div class="card"><div class="card-body">
    <form @submit.prevent="save">
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Company Name</label><input class="form-control" v-model="p.company_name" required></div>
      <div class="col-md-6 mb-3"><label class="form-label">Email</label><input class="form-control" :value="p.email" disabled></div></div>
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">HR Contact</label><input class="form-control" v-model="p.hr_contact"></div>
      <div class="col-md-6 mb-3"><label class="form-label">Website</label><input class="form-control" v-model="p.website"></div></div>
      <div class="mb-3"><label class="form-label">Description</label><textarea class="form-control" v-model="p.description" rows="3"></textarea></div>
      <button class="btn btn-dark" :disabled="saving">{{saving?"Saving...":"Save"}}</button>
    </form>
  </div></div>
</div>`,
data(){return{p:{},saving:false,ok:"",err:""}},
async mounted(){this.p=(await api.get("/company/profile")).data},
methods:{async save(){this.saving=true;this.ok="";this.err="";try{await api.put("/company/profile",this.p);this.ok="Profile updated!"}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.saving=false}}}};

const CompanyDrives={template:`
<div>
  <div class="d-flex justify-content-between mb-3"><h4>My Drives</h4><button class="btn btn-dark btn-sm" @click="showModal=true"><i class="bi bi-plus"></i> New Drive</button></div>
  <div v-if="!drives.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives yet</p></div>
  <div class="row g-3">
    <div class="col-md-6" v-for="d in drives">
      <div class="card">
        <div class="card-header d-flex justify-content-between"><strong>{{d.job_title}}</strong><span class="badge" :class="'badge-'+d.status">{{d.status}}</span></div>
        <div class="card-body">
          <p class="text-muted small mb-2">{{(d.job_description||"").substring(0,120)}}...</p>
          <div class="row text-center"><div class="col"><small class="text-muted">Package</small><br><strong>{{d.package||"-"}}</strong></div><div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{d.eligibility_cgpa||"Any"}}</strong></div><div class="col"><small class="text-muted">Apps</small><br><strong>{{d.total_applications}}</strong></div></div>
          <hr><small class="text-muted">Deadline: {{fmtDate(d.deadline)}}</small>
          <div class="mt-2"><router-link :to="'/company/drives/'+d.id+'/apps'" class="btn btn-dark btn-sm me-1">View Applications</router-link></div>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showModal" class="modal d-block" style="background:rgba(0,0,0,.5)"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header"><h5>Create Drive</h5><button class="btn-close" @click="showModal=false"></button></div>
    <form @submit.prevent="create"><div class="modal-body">
      <div v-if="formErr" class="alert alert-danger py-2">{{formErr}}</div>
      <div class="mb-3"><label class="form-label">Job Title *</label><input class="form-control" v-model="f.job_title" required></div>
      <div class="mb-3"><label class="form-label">Description *</label><textarea class="form-control" v-model="f.job_description" rows="3" required></textarea></div>
      <div class="row"><div class="col-md-4 mb-3"><label class="form-label">Package</label><input class="form-control" v-model="f.package" placeholder="e.g. 6 LPA"></div>
      <div class="col-md-4 mb-3"><label class="form-label">Min CGPA</label><input type="number" step="0.1" min="0" max="10" class="form-control" v-model="f.eligibility_cgpa"></div>
      <div class="col-md-4 mb-3"><label class="form-label">Year</label><input type="number" class="form-control" v-model="f.eligibility_year"></div></div>
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Branches (comma-sep)</label><input class="form-control" v-model="f.eligibility_branch" placeholder="CSE,ECE,IT"></div>
      <div class="col-md-6 mb-3"><label class="form-label">Deadline *</label><input type="datetime-local" class="form-control" v-model="f.deadline" required></div></div>
    </div><div class="modal-footer"><button type="button" class="btn btn-outline-dark" @click="showModal=false">Cancel</button><button class="btn btn-dark">Create</button></div></form>
  </div></div></div>
</div>`,
data(){return{drives:[],showModal:false,formErr:"",f:{job_title:"",job_description:"",package:"",eligibility_cgpa:0,eligibility_branch:"",eligibility_year:"",deadline:""}}},
mounted(){this.load()},
methods:{async load(){this.drives=(await api.get("/company/drives")).data},
async create(){this.formErr="";try{await api.post("/company/drives",this.f);this.showModal=false;this.f={job_title:"",job_description:"",package:"",eligibility_cgpa:0,eligibility_branch:"",eligibility_year:"",deadline:""};this.load()}catch(e){this.formErr=e.response?.data?.error||"Failed"}}}};

const CompanyApplications={template:`
<div>
  <div class="d-flex align-items-center mb-3"><router-link to="/company/drives" class="btn btn-outline-dark btn-sm me-3"><i class="bi bi-arrow-left"></i></router-link><h4 class="mb-0">Applications</h4></div>
  <div v-if="!apps.length" class="empty"><i class="bi bi-file-text"></i><p>No applications yet</p></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>Student</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Phone</th><th>Resume</th><th>Status</th><th>Update</th><th>Interview</th></tr></thead><tbody>
    <tr v-for="a in apps"><td><strong>{{a.student_name}}</strong></td><td>{{a.student_email}}</td><td>{{a.student_branch}}</td><td>{{a.student_cgpa}}</td><td>{{a.student_phone||"-"}}</td>
    <td><a v-if="a.resume_url" :href="a.resume_url" target="_blank">View</a><span v-else>-</span></td>
    <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td>
    <td><select class="form-select form-select-sm" style="width:auto" :value="a.status" @change="update(a.id,$event.target.value)">
      <option value="applied">Applied</option><option value="shortlisted">Shortlisted</option><option value="selected">Selected</option><option value="rejected">Rejected</option>
    </select></td>
    <td><button class="btn btn-outline-dark btn-sm" @click="openInterview(a)"><i class="bi bi-calendar-event"></i></button></td></tr></tbody></table></div>
  <div v-if="showInterview" class="modal d-block" style="background:rgba(0,0,0,.5)"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5>Schedule Interview — {{iApp.student_name}}</h5><button class="btn-close" @click="showInterview=false"></button></div>
    <form @submit.prevent="saveInterview"><div class="modal-body">
      <div v-if="iMsg" class="alert alert-success py-2">{{iMsg}}</div>
      <div class="mb-3"><label class="form-label">Interview Date & Time</label><input type="datetime-local" class="form-control" v-model="iForm.interview_date" required></div>
      <div class="mb-3"><label class="form-label">Meeting Link</label><input class="form-control" v-model="iForm.interview_link" placeholder="https://meet.google.com/..."></div>
      <div class="mb-3"><label class="form-label">Notes</label><textarea class="form-control" v-model="iForm.interview_notes" rows="2" placeholder="Instructions for the student..."></textarea></div>
    </div><div class="modal-footer"><button type="button" class="btn btn-outline-dark" @click="showInterview=false">Close</button><button class="btn btn-dark" :disabled="iSaving">{{iSaving?"Saving...":"Schedule"}}</button></div></form>
  </div></div></div>
</div>`,
data(){return{apps:[],showInterview:false,iApp:{},iForm:{interview_date:"",interview_link:"",interview_notes:""},iSaving:false,iMsg:""}},mounted(){this.load()},
methods:{async load(){this.apps=(await api.get("/company/drives/"+this.$route.params.did+"/applications")).data},
async update(aid,s){try{await api.put("/company/applications/"+aid+"/status",{status:s});this.load()}catch(e){alert(e.response?.data?.error||"Failed")}},
openInterview(a){this.iApp=a;this.iForm.interview_date=a.interview_date?a.interview_date.substring(0,16):"";this.iForm.interview_link=a.interview_link||"";this.iForm.interview_notes=a.interview_notes||"";this.iMsg="";this.showInterview=true},
async saveInterview(){this.iSaving=true;try{await api.put("/company/applications/"+this.iApp.id+"/interview",this.iForm);this.iMsg="Interview scheduled!";this.load()}catch(e){alert(e.response?.data?.error||"Failed")}finally{this.iSaving=false}}}};

// ═══════════════════════════ STUDENT PAGES ═══════════════════════════
const StudentDashboard={template:`
<div>
  <h4 class="mb-4">Welcome, {{d.name}}</h4>
  <div class="row g-3 mb-4">
    <div class="col-6 col-md-3" v-for="s in stats"><div class="card stat-card p-3 text-center"><div class="val">{{s.v}}</div><div class="lbl">{{s.l}}</div></div></div>
  </div>
  <div class="card"><div class="card-body"><div class="row"><div class="col-md-3"><strong>Branch:</strong> {{d.branch}}</div><div class="col-md-3"><strong>CGPA:</strong> {{d.cgpa}}</div><div class="col-md-3"><strong>Year:</strong> {{d.year}}</div></div></div></div>
</div>`,
data(){return{d:{}}},computed:{stats(){return[{v:this.d.total_applications||0,l:"Applications"},{v:this.d.pending||0,l:"Pending"},{v:this.d.shortlisted||0,l:"Shortlisted"},{v:this.d.selected||0,l:"Selected"}]}},
async mounted(){try{this.d=(await api.get("/student/dashboard")).data}catch(e){}}};

const StudentDrives={components:{Pagination},template:`
<div>
  <h4 class="mb-3">Available Drives</h4>
  <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search..." v-model="search" @input="load"></div>
  <div class="col-md-3"><select class="form-select" v-model="branch" @change="load"><option value="">All Branches</option><option v-for="b in branches" :value="b">{{b}}</option></select></div></div>
  <div v-if="!drives.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives available</p></div>
  <div class="row g-3">
    <div class="col-md-6" v-for="d in drives">
      <div class="card">
        <div class="card-header d-flex justify-content-between"><div><strong>{{d.job_title}}</strong><br><small class="text-muted">{{d.company_name}}</small></div><span class="badge bg-dark">{{d.package||"N/A"}}</span></div>
        <div class="card-body">
          <p class="text-muted small mb-2">{{(d.job_description||"").substring(0,150)}}...</p>
          <div class="row text-center mb-3"><div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{d.eligibility_cgpa||"Any"}}</strong></div><div class="col"><small class="text-muted">Branches</small><br><strong>{{d.eligibility_branch||"All"}}</strong></div><div class="col"><small class="text-muted">Deadline</small><br><strong>{{fmtDate(d.deadline)}}</strong></div></div>
          <button v-if="!d.already_applied" class="btn btn-dark w-100" @click="apply(d.id)" :disabled="applying===d.id">{{applying===d.id?"Applying...":"Apply Now"}}</button>
          <button v-else class="btn btn-outline-dark w-100" disabled><i class="bi bi-check"></i> Applied</button>
        </div>
      </div>
    </div>
  </div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{drives:[],search:"",branch:"",applying:null,branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"],page:1,pages:1,total:0}},
mounted(){this.load()},
methods:{async load(){const p={page:this.page};if(this.search)p.search=this.search;if(this.branch)p.branch=this.branch;const r=(await api.get("/student/drives",{params:p})).data;this.drives=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()},
async apply(id){this.applying=id;try{await api.post("/student/drives/"+id+"/apply");this.load()}catch(e){alert(e.response?.data?.error||"Failed")}finally{this.applying=null}}}};

const StudentApplications={components:{Pagination},template:`
<div>
  <div class="d-flex justify-content-between mb-3"><h4>My Applications</h4><button class="btn btn-outline-dark btn-sm" @click="exportCSV" :disabled="exporting"><i class="bi bi-download"></i> Export CSV</button></div>
  <div v-if="msg" class="alert alert-info py-2">{{msg}}</div>
  <div v-if="!apps.length" class="empty"><i class="bi bi-file-text"></i><p>No applications yet</p><router-link to="/student/drives" class="btn btn-dark">Browse Drives</router-link></div>
  <div class="table-responsive" v-else><table class="table"><thead><tr><th>#</th><th>Company</th><th>Position</th><th>Package</th><th>Status</th><th>Interview</th><th>Applied</th><th>Deadline</th></tr></thead><tbody>
    <tr v-for="(a,i) in apps"><td>{{(page-1)*20+i+1}}</td><td><strong>{{a.company_name}}</strong></td><td>{{a.job_title}}</td><td>{{a.package||"-"}}</td>
    <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td>
    <td><span v-if="a.interview_date"><i class="bi bi-calendar-event"></i> {{fmtDate(a.interview_date)}}<br><a v-if="a.interview_link" :href="a.interview_link" target="_blank" class="small">Join</a><br><small v-if="a.interview_notes" class="text-muted">{{a.interview_notes}}</small></span><span v-else class="text-muted">-</span></td>
    <td>{{fmtDate(a.applied_at)}}</td><td>{{fmtDate(a.deadline)}}</td></tr></tbody></table></div>
  <pagination :page="page" :pages="pages" :total="total" @change="goPage"/>
</div>`,
data(){return{apps:[],exporting:false,msg:"",page:1,pages:1,total:0}},
mounted(){this.load()},
methods:{async load(){const r=(await api.get("/student/applications",{params:{page:this.page}})).data;this.apps=r.items;this.page=r.page;this.pages=r.pages;this.total=r.total},
goPage(p){this.page=p;this.load()},
async exportCSV(){this.exporting=true;try{const r=await api.post("/student/export");this.msg=r.data.message;if(r.data.csv_data){const b=new Blob([r.data.csv_data],{type:"text/csv"});const u=URL.createObjectURL(b);const a=document.createElement("a");a.href=u;a.download="applications.csv";a.click();URL.revokeObjectURL(u)}}catch(e){this.msg="Export failed"}finally{this.exporting=false}}}};

const StudentProfilePage={template:`
<div>
  <h4 class="mb-3">My Profile</h4>
  <div v-if="ok" class="alert alert-success py-2">{{ok}}</div>
  <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
  <div class="card"><div class="card-body">
    <form @submit.prevent="save">
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Name</label><input class="form-control" v-model="p.name" required></div>
      <div class="col-md-6 mb-3"><label class="form-label">Email</label><input class="form-control" :value="p.email" disabled></div></div>
      <div class="row"><div class="col-md-4 mb-3"><label class="form-label">Branch</label><select class="form-select" v-model="p.branch"><option v-for="b in branches" :value="b">{{b}}</option></select></div>
      <div class="col-md-4 mb-3"><label class="form-label">CGPA</label><input type="number" step="0.01" min="0" max="10" class="form-control" v-model="p.cgpa"></div>
      <div class="col-md-4 mb-3"><label class="form-label">Year</label><input type="number" class="form-control" v-model="p.year"></div></div>
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Phone</label><input class="form-control" v-model="p.phone"></div>
      <div class="col-md-6 mb-3"><label class="form-label">Resume URL</label><input class="form-control" v-model="p.resume_url" placeholder="https://drive.google.com/..."></div></div>
      <button class="btn btn-dark me-2" :disabled="saving">{{saving?"Saving...":"Save"}}</button>
    </form>
    <hr>
    <h6>Upload Resume (PDF/DOC/DOCX, max 5MB)</h6>
    <div class="d-flex align-items-center gap-2">
      <input type="file" class="form-control" style="max-width:350px" accept=".pdf,.doc,.docx" ref="fileInput">
      <button class="btn btn-outline-dark" @click="uploadResume" :disabled="uploading">{{uploading?"Uploading...":"Upload"}}</button>
    </div>
    <div v-if="uploadMsg" class="mt-2"><small :class="uploadErr?'text-danger':'text-success'">{{uploadMsg}}</small></div>
    <div v-if="p.resume_url" class="mt-2"><small class="text-muted">Current: <a :href="p.resume_url" target="_blank">{{p.resume_url}}</a></small></div>
  </div></div>
</div>`,
data(){return{p:{},saving:false,ok:"",err:"",branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"],uploading:false,uploadMsg:"",uploadErr:false}},
async mounted(){this.p=(await api.get("/student/profile")).data},
methods:{async save(){this.saving=true;this.ok="";this.err="";try{await api.put("/student/profile",this.p);this.ok="Saved!"}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.saving=false}},
async uploadResume(){const f=this.$refs.fileInput?.files?.[0];if(!f){this.uploadMsg="Please select a file";this.uploadErr=true;return}
this.uploading=true;this.uploadMsg="";this.uploadErr=false;
const fd=new FormData();fd.append("resume",f);
try{const r=await api.post("/student/resume-upload",fd,{headers:{"Content-Type":"multipart/form-data"}});this.uploadMsg=r.data.message;this.p.resume_url=r.data.resume_url;this.uploadErr=false}catch(e){this.uploadMsg=e.response?.data?.error||"Upload failed";this.uploadErr=true}finally{this.uploading=false}}}};

// ═══════════════════════════ ADMIN STATS ═══════════════════════════
const AdminStats={template:`
<div>
  <h4 class="mb-4"><i class="bi bi-bar-chart"></i> Reports \& Statistics</h4>
  <div class="row g-4 mb-4">
    <div class="col-md-6"><div class="card"><div class="card-header"><strong>Applications by Status</strong></div><div class="card-body"><canvas id="ch1" height="250"></canvas></div></div></div>
    <div class="col-md-6"><div class="card"><div class="card-header"><strong>Applications by Branch</strong></div><div class="card-body"><canvas id="ch2" height="250"></canvas></div></div></div>
  </div>
  <div class="row g-4">
    <div class="col-md-6"><div class="card"><div class="card-header"><strong>Drives per Month</strong></div><div class="card-body"><canvas id="ch3" height="250"></canvas></div></div></div>
    <div class="col-md-6"><div class="card"><div class="card-header"><strong>Top Companies by Selections</strong></div><div class="card-body">
      <div v-if="!s.top_companies||!s.top_companies.length" class="text-muted text-center py-4">No data yet</div>
      <table v-else class="table table-sm"><thead><tr><th>Company</th><th>Selected</th></tr></thead><tbody><tr v-for="c in s.top_companies"><td>{{c.company}}</td><td><span class="badge bg-dark">{{c.selections}}</span></td></tr></tbody></table>
    </div></div></div>
  </div>
</div>`,
data(){return{s:{},charts:[]}},
async mounted(){try{this.s=(await api.get("/admin/stats")).data;this.$nextTick(()=>this.draw())}catch(e){}},
methods:{draw(){
  this.charts.forEach(c=>c.destroy());this.charts=[];
  const clr={applied:"#999",shortlisted:"#666",selected:"#111",rejected:"#ccc"};
  const sc=this.s.status_counts||{};
  const c1=document.getElementById("ch1");
  if(c1)this.charts.push(new Chart(c1,{type:"doughnut",data:{labels:Object.keys(sc).map(s=>s[0].toUpperCase()+s.slice(1)),datasets:[{data:Object.values(sc),backgroundColor:Object.keys(sc).map(s=>clr[s]||"#888")}]},options:{responsive:true,plugins:{legend:{position:"bottom"}}}}));
  const bs=this.s.branch_stats||{};
  const c2=document.getElementById("ch2");
  if(c2)this.charts.push(new Chart(c2,{type:"bar",data:{labels:Object.keys(bs),datasets:[{label:"Applications",data:Object.values(bs),backgroundColor:"#333"}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}}));
  const dm=this.s.drives_monthly||[];
  const c3=document.getElementById("ch3");
  if(c3)this.charts.push(new Chart(c3,{type:"line",data:{labels:dm.map(d=>d.month),datasets:[{label:"Drives",data:dm.map(d=>d.count),borderColor:"#111",tension:.3,fill:false}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}}));
}},
beforeUnmount(){this.charts.forEach(c=>c.destroy())}};

// ═══════════════════════════ ROUTER ═══════════════════════════
const routes=[
  {path:"/",redirect:"/login"},{path:"/login",component:LoginPage},{path:"/register",component:RegisterPage},
  {path:"/admin",component:AdminLayout,children:[
    {path:"",component:AdminDashboard},{path:"companies",component:AdminCompanies},{path:"drives",component:AdminDrives},{path:"students",component:AdminStudents},{path:"applications",component:AdminApplications},{path:"stats",component:AdminStats}]},
  {path:"/company",component:CompanyLayout,children:[
    {path:"",component:CompanyDashboard},{path:"drives",component:CompanyDrives},{path:"drives/:did/apps",component:CompanyApplications},{path:"profile",component:CompanyProfileEdit}]},
  {path:"/student",component:StudentLayout,children:[
    {path:"",component:StudentDashboard},{path:"drives",component:StudentDrives},{path:"applications",component:StudentApplications},{path:"profile",component:StudentProfilePage}]}
];
const router=createRouter({history:createWebHashHistory(),routes});
router.beforeEach((to,from,next)=>{
  const pub=["/login","/register"];const t=localStorage.getItem("token");const r=localStorage.getItem("role");
  if(pub.includes(to.path)){if(t&&r)return next("/"+r);return next()}
  if(!t)return next("/login");
  if(to.path.startsWith("/admin")&&r!=="admin")return next("/login");
  if(to.path.startsWith("/company")&&r!=="company")return next("/login");
  if(to.path.startsWith("/student")&&r!=="student")return next("/login");
  next();
});
Vue.createApp({}).use(router).mount("#app");
