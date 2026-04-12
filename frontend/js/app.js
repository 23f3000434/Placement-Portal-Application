const {createRouter,createWebHashHistory}=VueRouter;

// ═══ SIDEBAR ═══
const Sidebar={props:["links"],template:`
<div class="sidebar d-flex flex-column">
  <div class="brand"><i class="bi bi-briefcase-fill"></i> PPA</div>
  <nav class="nav flex-column mt-2">
    <router-link v-for="l in links" :key="l.to" :to="l.to" class="nav-link" active-class="active" :exact="l.to.split('/').length<=2"><i :class="l.icon"></i>{{l.label}}</router-link>
  </nav>
  <div class="mt-auto p-3"><button class="btn btn-outline-light btn-sm w-100" @click="$emit('logout')"><i class="bi bi-box-arrow-left"></i> Logout</button></div>
</div>`};

function makeLayout(links){
  return {
    components:{Sidebar},
    template:'<div><sidebar :links="links" @logout="doLogout"/><div class="main"><router-view></router-view></div></div>',
    data(){return{links:links}},
    methods:{doLogout(){logout()}}
  };
}

const AdminLayout=makeLayout([
  {to:"/admin",icon:"bi bi-speedometer2",label:"Dashboard"},
  {to:"/admin/companies",icon:"bi bi-building",label:"Companies"},
  {to:"/admin/drives",icon:"bi bi-briefcase",label:"Drives"},
  {to:"/admin/students",icon:"bi bi-people",label:"Students"},
  {to:"/admin/applications",icon:"bi bi-file-text",label:"Applications"},
  {to:"/admin/stats",icon:"bi bi-bar-chart",label:"Reports"}
]);
const CompanyLayout=makeLayout([
  {to:"/company",icon:"bi bi-speedometer2",label:"Dashboard"},
  {to:"/company/drives",icon:"bi bi-briefcase",label:"My Drives"},
  {to:"/company/profile",icon:"bi bi-person",label:"Profile"}
]);
const StudentLayout=makeLayout([
  {to:"/student",icon:"bi bi-speedometer2",label:"Dashboard"},
  {to:"/student/drives",icon:"bi bi-briefcase",label:"Browse Drives"},
  {to:"/student/applications",icon:"bi bi-file-text",label:"My Applications"},
  {to:"/student/profile",icon:"bi bi-person",label:"Profile"}
]);

// ═══ LOGIN ═══
const LoginPage={
  template:`
  <div class="login-box">
    <div class="card border-dark"><div class="card-body p-4">
      <h4 class="text-center mb-4">Placement Portal</h4>
      <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
      <form @submit.prevent="go">
        <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" v-model="email" required></div>
        <div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" v-model="pw" required></div>
        <button class="btn btn-dark w-100" :disabled="loading">{{loading?"Logging in...":"Login"}}</button>
      </form>
      <p class="text-center mt-3 mb-0"><router-link to="/register">Register here</router-link></p>
    </div></div>
  </div>`,
  data(){return{email:"",pw:"",err:"",loading:false}},
  methods:{
    async go(){
      this.loading=true;this.err="";
      try{
        const r=await api.post("/auth/login",{email:this.email,password:this.pw});
        localStorage.setItem("token",r.data.token);
        localStorage.setItem("role",r.data.role);
        this.$router.push("/"+r.data.role);
      }catch(e){this.err=e.response?.data?.error||"Login failed"}
      finally{this.loading=false}
    }
  }
};

// ═══ REGISTER ═══
const RegisterPage={
  template:`
  <div class="login-box">
    <div class="card border-dark"><div class="card-body p-4">
      <h4 class="text-center mb-4">Register</h4>
      <div v-if="err" class="alert alert-danger py-2">{{err}}</div>
      <form @submit.prevent="go">
        <div class="mb-3"><label class="form-label">Role</label>
          <select class="form-select" v-model="role" required><option value="">Select</option><option value="student">Student</option><option value="company">Company</option></select></div>
        <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" v-model="email" required></div>
        <div class="mb-3"><label class="form-label">Password (6+ chars)</label><input type="password" class="form-control" v-model="pw" required minlength="6"></div>
        <template v-if="role==='student'">
          <div class="mb-3"><label class="form-label">Name</label><input class="form-control" v-model="name" required></div>
          <div class="row">
            <div class="col mb-3"><label class="form-label">Branch</label><select class="form-select" v-model="branch" required><option v-for="b in branches" :value="b">{{b}}</option></select></div>
            <div class="col mb-3"><label class="form-label">CGPA</label><input type="number" step="0.01" min="0" max="10" class="form-control" v-model="cgpa" required></div>
            <div class="col mb-3"><label class="form-label">Year</label><input type="number" class="form-control" v-model="year" required></div>
          </div>
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
      <p class="text-center mt-3 mb-0"><router-link to="/login">Login here</router-link></p>
    </div></div>
  </div>`,
  data(){return{role:"",email:"",pw:"",err:"",loading:false,name:"",branch:"",cgpa:"",year:2026,phone:"",company_name:"",hr_contact:"",website:"",description:"",branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"]}},
  methods:{
    async go(){
      this.loading=true;this.err="";
      try{
        const p={email:this.email,password:this.pw,role:this.role};
        if(this.role==="student") Object.assign(p,{name:this.name,branch:this.branch,cgpa:this.cgpa,year:this.year,phone:this.phone});
        else Object.assign(p,{company_name:this.company_name,hr_contact:this.hr_contact,website:this.website,description:this.description});
        const r=await api.post("/auth/register",p);
        localStorage.setItem("token",r.data.token);
        localStorage.setItem("role",r.data.role);
        this.$router.push("/"+r.data.role);
      }catch(e){this.err=e.response?.data?.error||"Failed"}
      finally{this.loading=false}
    }
  }
};

// ═══════════ ADMIN PAGES ═══════════

const AdminDashboard={
  template:`<div><h4 class="mb-4">Admin Dashboard</h4>
    <div class="row g-3 mb-4">
      <div class="col-md-3 col-6" v-for="s in stats"><div class="card stat-card p-3 text-center"><div class="val">{{s.v}}</div><div class="lbl">{{s.l}}</div></div></div>
    </div></div>`,
  data(){return{d:{}}},
  computed:{stats(){return[{v:this.d.total_students||0,l:"Students"},{v:this.d.total_companies||0,l:"Companies"},{v:this.d.total_drives||0,l:"Drives"},{v:this.d.students_placed||0,l:"Placed"}]}},
  async mounted(){try{this.d=(await api.get("/admin/dashboard")).data}catch(e){console.error("AdminDashboard",e)}}
};

const AdminCompanies={
  template:`<div><h4 class="mb-3">Companies</h4>
    <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search..." v-model="search" @input="load"></div>
    <div class="col-md-3"><select class="form-select" v-model="filter" @change="load"><option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select></div></div>
    <div v-if="!items.length" class="empty"><i class="bi bi-building"></i><p>No companies</p></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>Company</th><th>Email</th><th>Status</th><th>Drives</th><th>Actions</th></tr></thead><tbody>
      <tr v-for="c in items"><td><strong>{{c.company_name}}</strong></td><td>{{c.email}}</td>
      <td><span class="badge" :class="'badge-'+c.approval_status">{{c.approval_status}}</span><span v-if="c.is_blacklisted" class="badge bg-dark ms-1">blocked</span></td>
      <td>{{c.total_drives}}</td>
      <td><button v-if="c.approval_status==='pending'" class="btn btn-dark btn-sm me-1" @click="act(c.id,'approve')">Approve</button>
        <button v-if="c.approval_status==='pending'" class="btn btn-outline-dark btn-sm me-1" @click="act(c.id,'reject')">Reject</button>
        <button class="btn btn-sm" :class="c.is_blacklisted?'btn-outline-dark':'btn-dark'" @click="act(c.id,'blacklist')">{{c.is_blacklisted?"Unblock":"Block"}}</button>
        <button class="btn btn-sm ms-1" :class="c.is_active?'btn-outline-dark':'btn-dark'" @click="toggle(c.user_id)">{{c.is_active?"Deactivate":"Activate"}}</button></td>
      </tr></tbody></table></div></div>`,
  data(){return{items:[],search:"",filter:""}},
  mounted(){this.load()},
  methods:{
    async load(){try{const p={};if(this.search)p.search=this.search;if(this.filter)p.status=this.filter;this.items=(await api.get("/admin/companies",{params:p})).data}catch(e){console.error("AdminCompanies",e)}},
    async act(id,a){await api.put("/admin/companies/"+id+"/"+a);this.load()},
    async toggle(uid){await api.put("/admin/users/"+uid+"/toggle-active");this.load()}
  }
};

const AdminDrives={
  template:`<div><h4 class="mb-3">Placement Drives</h4>
    <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search..." v-model="search" @input="load"></div>
    <div class="col-md-3"><select class="form-select" v-model="filter" @change="load"><option value="">All</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="closed">Closed</option></select></div></div>
    <div v-if="!items.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives</p></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>Title</th><th>Company</th><th>Package</th><th>Deadline</th><th>Status</th><th>Apps</th><th>Actions</th></tr></thead><tbody>
      <tr v-for="d in items"><td><strong>{{d.job_title}}</strong></td><td>{{d.company_name}}</td><td>{{d.package||"-"}}</td><td>{{fmtDate(d.deadline)}}</td>
      <td><span class="badge" :class="'badge-'+d.status">{{d.status}}</span></td><td>{{d.total_applications}}</td>
      <td><button v-if="d.status==='pending'" class="btn btn-dark btn-sm me-1" @click="act(d.id,'approve')">Approve</button>
        <button v-if="d.status==='pending'" class="btn btn-outline-dark btn-sm me-1" @click="act(d.id,'reject')">Reject</button>
        <button v-if="d.status==='approved'" class="btn btn-outline-dark btn-sm" @click="act(d.id,'close')">Close</button></td>
      </tr></tbody></table></div></div>`,
  data(){return{items:[],search:"",filter:""}},
  mounted(){this.load()},
  methods:{
    async load(){try{const p={};if(this.search)p.search=this.search;if(this.filter)p.status=this.filter;this.items=(await api.get("/admin/drives",{params:p})).data}catch(e){console.error("AdminDrives",e)}},
    async act(id,a){await api.put("/admin/drives/"+id+"/"+a);this.load()}
  }
};

const AdminStudents={
  template:`<div><h4 class="mb-3">Students</h4>
    <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search name/branch..." v-model="search" @input="load"></div></div>
    <div v-if="!items.length" class="empty"><i class="bi bi-people"></i><p>No students</p></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Apps</th><th>Selected</th><th>Status</th><th></th></tr></thead><tbody>
      <tr v-for="s in items"><td><strong>{{s.name}}</strong></td><td>{{s.email}}</td><td>{{s.branch}}</td><td>{{s.cgpa}}</td><td>{{s.year}}</td><td>{{s.total_applications}}</td><td>{{s.selected_count}}</td>
      <td><span class="badge" :class="s.is_active?'bg-dark':'bg-secondary'">{{s.is_active?"Active":"Inactive"}}</span></td>
      <td><button class="btn btn-sm" :class="s.is_active?'btn-outline-dark':'btn-dark'" @click="toggle(s.user_id)">{{s.is_active?"Deactivate":"Activate"}}</button></td>
      </tr></tbody></table></div></div>`,
  data(){return{items:[],search:""}},
  mounted(){this.load()},
  methods:{
    async load(){try{const p={};if(this.search)p.search=this.search;this.items=(await api.get("/admin/students",{params:p})).data}catch(e){console.error("AdminStudents",e)}},
    async toggle(uid){await api.put("/admin/users/"+uid+"/toggle-active");this.load()}
  }
};

const AdminApplications={
  template:`<div><h4 class="mb-3">All Applications</h4>
    <div v-if="!items.length" class="empty"><i class="bi bi-file-text"></i><p>No applications</p></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>#</th><th>Student</th><th>Branch</th><th>Company</th><th>Drive</th><th>Status</th><th>Date</th></tr></thead><tbody>
      <tr v-for="(a,i) in items"><td>{{i+1}}</td><td><strong>{{a.student_name}}</strong></td><td>{{a.student_branch}}</td><td>{{a.company_name}}</td><td>{{a.drive_title}}</td>
      <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td><td>{{fmtDate(a.applied_at)}}</td></tr></tbody></table></div></div>`,
  data(){return{items:[]}},
  async mounted(){try{this.items=(await api.get("/admin/applications")).data}catch(e){console.error("AdminApplications",e)}}
};

const AdminStats={
  template:`<div><h4 class="mb-4"><i class="bi bi-bar-chart"></i> Reports & Statistics</h4>
    <div class="row g-4 mb-4">
      <div class="col-md-6"><div class="card"><div class="card-header"><strong>Applications by Status</strong></div><div class="card-body"><canvas id="ch1" height="250"></canvas></div></div></div>
      <div class="col-md-6"><div class="card"><div class="card-header"><strong>Applications by Branch</strong></div><div class="card-body"><canvas id="ch2" height="250"></canvas></div></div></div>
    </div>
    <div class="row g-4">
      <div class="col-md-6"><div class="card"><div class="card-header"><strong>Drives per Month</strong></div><div class="card-body"><canvas id="ch3" height="250"></canvas></div></div></div>
      <div class="col-md-6"><div class="card"><div class="card-header"><strong>Top Companies</strong></div><div class="card-body">
        <div v-if="!s.top_companies||!s.top_companies.length" class="text-muted text-center py-4">No data</div>
        <table v-else class="table table-sm"><thead><tr><th>Company</th><th>Selected</th></tr></thead><tbody><tr v-for="c in s.top_companies"><td>{{c.company}}</td><td><span class="badge bg-dark">{{c.selections}}</span></td></tr></tbody></table>
      </div></div></div>
    </div></div>`,
  data(){return{s:{},charts:[]}},
  async mounted(){try{this.s=(await api.get("/admin/stats")).data;this.$nextTick(()=>this.draw())}catch(e){console.error("AdminStats",e)}},
  methods:{
    draw(){
      this.charts.forEach(c=>c.destroy());this.charts=[];
      const clr={applied:"#999",shortlisted:"#666",selected:"#111",rejected:"#ccc"};
      const sc=this.s.status_counts||{};
      const c1=document.getElementById("ch1");
      if(c1&&Object.keys(sc).length)this.charts.push(new Chart(c1,{type:"doughnut",data:{labels:Object.keys(sc).map(s=>s[0].toUpperCase()+s.slice(1)),datasets:[{data:Object.values(sc),backgroundColor:Object.keys(sc).map(s=>clr[s]||"#888")}]},options:{responsive:true,plugins:{legend:{position:"bottom"}}}}));
      const bs=this.s.branch_stats||{};
      const c2=document.getElementById("ch2");
      if(c2&&Object.keys(bs).length)this.charts.push(new Chart(c2,{type:"bar",data:{labels:Object.keys(bs),datasets:[{label:"Applications",data:Object.values(bs),backgroundColor:"#333"}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}}));
      const dm=this.s.drives_monthly||[];
      const c3=document.getElementById("ch3");
      if(c3&&dm.length)this.charts.push(new Chart(c3,{type:"line",data:{labels:dm.map(d=>d.month),datasets:[{label:"Drives",data:dm.map(d=>d.count),borderColor:"#111",tension:.3,fill:false}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}}));
    }
  },
  beforeUnmount(){this.charts.forEach(c=>c.destroy())}
};

// ═══════════ COMPANY PAGES ═══════════

const CompanyDashboard={
  template:`<div><h4 class="mb-3">Company Dashboard</h4>
    <div v-if="d.approval_status==='pending'" class="alert alert-warning">Pending admin approval.</div>
    <div v-if="d.approval_status==='rejected'" class="alert alert-danger">Registration rejected.</div>
    <div v-if="d.is_blacklisted" class="alert alert-dark">Company blacklisted.</div>
    <div class="row g-3 mb-4">
      <div class="col-md-4 col-6"><div class="card stat-card p-3 text-center"><div class="val">{{d.total_drives||0}}</div><div class="lbl">Drives</div></div></div>
      <div class="col-md-4 col-6"><div class="card stat-card p-3 text-center"><div class="val">{{d.total_applicants||0}}</div><div class="lbl">Applicants</div></div></div>
    </div>
    <div class="card"><div class="card-body"><p><strong>Company:</strong> {{d.company_name}}</p><p><strong>HR:</strong> {{d.hr_contact||"N/A"}}</p><p><strong>Website:</strong> {{d.website||"N/A"}}</p><p><strong>Status:</strong> <span class="badge" :class="'badge-'+d.approval_status">{{d.approval_status}}</span></p></div></div></div>`,
  data(){return{d:{}}},
  async mounted(){try{this.d=(await api.get("/company/dashboard")).data}catch(e){console.error("CompanyDashboard",e)}}
};

const CompanyProfileEdit={
  template:`<div><h4 class="mb-3">Edit Profile</h4>
    <div v-if="ok" class="alert alert-success py-2">{{ok}}</div><div v-if="err" class="alert alert-danger py-2">{{err}}</div>
    <div class="card"><div class="card-body"><form @submit.prevent="save">
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Company Name</label><input class="form-control" v-model="p.company_name" required></div>
      <div class="col-md-6 mb-3"><label class="form-label">Email</label><input class="form-control" :value="p.email" disabled></div></div>
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">HR Contact</label><input class="form-control" v-model="p.hr_contact"></div>
      <div class="col-md-6 mb-3"><label class="form-label">Website</label><input class="form-control" v-model="p.website"></div></div>
      <div class="mb-3"><label class="form-label">Description</label><textarea class="form-control" v-model="p.description" rows="3"></textarea></div>
      <button class="btn btn-dark" :disabled="saving">{{saving?"Saving...":"Save"}}</button>
    </form></div></div></div>`,
  data(){return{p:{},saving:false,ok:"",err:""}},
  async mounted(){try{this.p=(await api.get("/company/profile")).data}catch(e){console.error(e)}},
  methods:{async save(){this.saving=true;this.ok="";this.err="";try{await api.put("/company/profile",this.p);this.ok="Saved!"}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.saving=false}}}
};

const CompanyDrives={
  template:`<div>
    <div class="d-flex justify-content-between mb-3"><h4>My Drives</h4><button class="btn btn-dark btn-sm" @click="showModal=true"><i class="bi bi-plus"></i> New Drive</button></div>
    <div v-if="!drives.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives yet</p></div>
    <div class="row g-3"><div class="col-md-6" v-for="d in drives"><div class="card">
      <div class="card-header d-flex justify-content-between"><strong>{{d.job_title}}</strong><span class="badge" :class="'badge-'+d.status">{{d.status}}</span></div>
      <div class="card-body">
        <p class="text-muted small mb-2">{{(d.job_description||"").substring(0,120)}}...</p>
        <div class="row text-center"><div class="col"><small class="text-muted">Package</small><br><strong>{{d.package||"-"}}</strong></div><div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{d.eligibility_cgpa||"Any"}}</strong></div><div class="col"><small class="text-muted">Apps</small><br><strong>{{d.total_applications}}</strong></div></div>
        <hr><small class="text-muted">Deadline: {{fmtDate(d.deadline)}}</small>
        <div class="mt-2"><router-link :to="'/company/drives/'+d.id+'/apps'" class="btn btn-dark btn-sm">View Applications</router-link></div>
      </div></div></div></div>
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
    </div></div></div></div>`,
  data(){return{drives:[],showModal:false,formErr:"",f:{job_title:"",job_description:"",package:"",eligibility_cgpa:0,eligibility_branch:"",eligibility_year:"",deadline:""}}},
  mounted(){this.load()},
  methods:{
    async load(){try{this.drives=(await api.get("/company/drives")).data}catch(e){console.error("CompanyDrives",e)}},
    async create(){this.formErr="";try{await api.post("/company/drives",this.f);this.showModal=false;this.f={job_title:"",job_description:"",package:"",eligibility_cgpa:0,eligibility_branch:"",eligibility_year:"",deadline:""};this.load()}catch(e){this.formErr=e.response?.data?.error||"Failed"}}
  }
};

const CompanyApplications={
  template:`<div>
    <div class="d-flex align-items-center mb-3"><router-link to="/company/drives" class="btn btn-outline-dark btn-sm me-3"><i class="bi bi-arrow-left"></i></router-link><h4 class="mb-0">Applications</h4></div>
    <div v-if="!apps.length" class="empty"><i class="bi bi-file-text"></i><p>No applications yet</p></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>Student</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Phone</th><th>Resume</th><th>Status</th><th>Update</th></tr></thead><tbody>
      <tr v-for="a in apps"><td><strong>{{a.student_name}}</strong></td><td>{{a.student_email}}</td><td>{{a.student_branch}}</td><td>{{a.student_cgpa}}</td><td>{{a.student_phone||"-"}}</td>
      <td><a v-if="a.resume_url" :href="a.resume_url" target="_blank">View</a><span v-else>-</span></td>
      <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td>
      <td><select class="form-select form-select-sm" style="width:auto" :value="a.status" @change="update(a.id,$event.target.value)">
        <option value="applied">Applied</option><option value="shortlisted">Shortlisted</option><option value="selected">Selected</option><option value="rejected">Rejected</option>
      </select></td></tr></tbody></table></div></div>`,
  data(){return{apps:[]}},
  mounted(){this.load()},
  methods:{
    async load(){try{this.apps=(await api.get("/company/drives/"+this.$route.params.did+"/applications")).data}catch(e){console.error("CompanyApplications",e)}},
    async update(aid,s){try{await api.put("/company/applications/"+aid+"/status",{status:s});this.load()}catch(e){alert(e.response?.data?.error||"Failed")}}
  }
};

// ═══════════ STUDENT PAGES ═══════════

const StudentDashboard={
  template:`<div><h4 class="mb-4">Welcome, {{d.name}}</h4>
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3" v-for="s in stats"><div class="card stat-card p-3 text-center"><div class="val">{{s.v}}</div><div class="lbl">{{s.l}}</div></div></div>
    </div>
    <div class="card"><div class="card-body"><div class="row"><div class="col-md-3"><strong>Branch:</strong> {{d.branch}}</div><div class="col-md-3"><strong>CGPA:</strong> {{d.cgpa}}</div><div class="col-md-3"><strong>Year:</strong> {{d.year}}</div></div></div></div></div>`,
  data(){return{d:{}}},
  computed:{stats(){return[{v:this.d.total_applications||0,l:"Applications"},{v:this.d.pending||0,l:"Pending"},{v:this.d.shortlisted||0,l:"Shortlisted"},{v:this.d.selected||0,l:"Selected"}]}},
  async mounted(){try{this.d=(await api.get("/student/dashboard")).data}catch(e){console.error("StudentDashboard",e)}}
};

const StudentDrives={
  template:`<div><h4 class="mb-3">Available Drives</h4>
    <div class="row mb-3"><div class="col-md-4"><input class="form-control" placeholder="Search drives or company..." v-model="search" @input="load"></div>
    <div class="col-md-3"><select class="form-select" v-model="branch" @change="load"><option value="">All Branches</option><option v-for="b in branches" :value="b">{{b}}</option></select></div></div>
    <div v-if="!drives.length" class="empty"><i class="bi bi-briefcase"></i><p>No drives available</p></div>
    <div class="row g-3"><div class="col-md-6" v-for="d in drives"><div class="card">
      <div class="card-header d-flex justify-content-between"><div><strong>{{d.job_title}}</strong><br><small class="text-muted">{{d.company_name}}</small></div><span class="badge bg-dark">{{d.package||"N/A"}}</span></div>
      <div class="card-body">
        <p class="text-muted small mb-2">{{(d.job_description||"").substring(0,150)}}...</p>
        <div class="row text-center mb-3"><div class="col"><small class="text-muted">Min CGPA</small><br><strong>{{d.eligibility_cgpa||"Any"}}</strong></div><div class="col"><small class="text-muted">Branches</small><br><strong>{{d.eligibility_branch||"All"}}</strong></div><div class="col"><small class="text-muted">Deadline</small><br><strong>{{fmtDate(d.deadline)}}</strong></div></div>
        <button v-if="!d.already_applied" class="btn btn-dark w-100" @click="apply(d.id)" :disabled="applying===d.id">{{applying===d.id?"Applying...":"Apply Now"}}</button>
        <button v-else class="btn btn-outline-dark w-100" disabled><i class="bi bi-check"></i> Applied</button>
      </div></div></div></div></div>`,
  data(){return{drives:[],search:"",branch:"",applying:null,branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"]}},
  mounted(){this.load()},
  methods:{
    async load(){try{const p={};if(this.search)p.search=this.search;if(this.branch)p.branch=this.branch;this.drives=(await api.get("/student/drives",{params:p})).data}catch(e){console.error("StudentDrives",e)}},
    async apply(id){this.applying=id;try{await api.post("/student/drives/"+id+"/apply");this.load()}catch(e){alert(e.response?.data?.error||"Failed")}finally{this.applying=null}}
  }
};

const StudentApplications={
  template:`<div>
    <div class="d-flex justify-content-between mb-3"><h4>My Applications</h4><button class="btn btn-outline-dark btn-sm" @click="exportCSV" :disabled="exporting"><i class="bi bi-download"></i> Export CSV</button></div>
    <div v-if="msg" class="alert alert-info py-2">{{msg}}</div>
    <div v-if="!apps.length" class="empty"><i class="bi bi-file-text"></i><p>No applications yet</p><router-link to="/student/drives" class="btn btn-dark">Browse Drives</router-link></div>
    <div class="table-responsive" v-else><table class="table"><thead><tr><th>#</th><th>Company</th><th>Position</th><th>Package</th><th>Status</th><th>Applied</th><th>Deadline</th></tr></thead><tbody>
      <tr v-for="(a,i) in apps"><td>{{i+1}}</td><td><strong>{{a.company_name}}</strong></td><td>{{a.job_title}}</td><td>{{a.package||"-"}}</td>
      <td><span class="badge" :class="'badge-'+a.status">{{a.status}}</span></td><td>{{fmtDate(a.applied_at)}}</td><td>{{fmtDate(a.deadline)}}</td></tr></tbody></table></div></div>`,
  data(){return{apps:[],exporting:false,msg:""}},
  mounted(){this.load()},
  methods:{
    async load(){try{this.apps=(await api.get("/student/applications")).data}catch(e){console.error("StudentApplications",e)}},
    async exportCSV(){this.exporting=true;try{const r=await api.post("/student/export");this.msg=r.data.message;if(r.data.csv_data){const b=new Blob([r.data.csv_data],{type:"text/csv"});const u=URL.createObjectURL(b);const a=document.createElement("a");a.href=u;a.download="applications.csv";a.click();URL.revokeObjectURL(u)}}catch(e){this.msg="Export failed"}finally{this.exporting=false}}
  }
};

const StudentProfilePage={
  template:`<div><h4 class="mb-3">My Profile</h4>
    <div v-if="ok" class="alert alert-success py-2">{{ok}}</div><div v-if="err" class="alert alert-danger py-2">{{err}}</div>
    <div class="card"><div class="card-body"><form @submit.prevent="save">
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Name</label><input class="form-control" v-model="p.name" required></div>
      <div class="col-md-6 mb-3"><label class="form-label">Email</label><input class="form-control" :value="p.email" disabled></div></div>
      <div class="row"><div class="col-md-4 mb-3"><label class="form-label">Branch</label><select class="form-select" v-model="p.branch"><option v-for="b in branches" :value="b">{{b}}</option></select></div>
      <div class="col-md-4 mb-3"><label class="form-label">CGPA</label><input type="number" step="0.01" min="0" max="10" class="form-control" v-model="p.cgpa"></div>
      <div class="col-md-4 mb-3"><label class="form-label">Year</label><input type="number" class="form-control" v-model="p.year"></div></div>
      <div class="row"><div class="col-md-6 mb-3"><label class="form-label">Phone</label><input class="form-control" v-model="p.phone"></div>
      <div class="col-md-6 mb-3"><label class="form-label">Resume URL</label><input class="form-control" v-model="p.resume_url" placeholder="https://drive.google.com/..."></div></div>
      <button class="btn btn-dark" :disabled="saving">{{saving?"Saving...":"Save"}}</button>
    </form></div></div></div>`,
  data(){return{p:{},saving:false,ok:"",err:"",branches:["CSE","ECE","EE","ME","CE","IT","CH","BT"]}},
  async mounted(){try{this.p=(await api.get("/student/profile")).data}catch(e){console.error(e)}},
  methods:{async save(){this.saving=true;this.ok="";this.err="";try{await api.put("/student/profile",this.p);this.ok="Saved!"}catch(e){this.err=e.response?.data?.error||"Failed"}finally{this.saving=false}}}
};

// ═══ ROUTER ═══
const routes=[
  {path:"/",redirect:"/login"},
  {path:"/login",component:LoginPage},
  {path:"/register",component:RegisterPage},
  {path:"/admin",component:AdminLayout,children:[
    {path:"",component:AdminDashboard},
    {path:"companies",component:AdminCompanies},
    {path:"drives",component:AdminDrives},
    {path:"students",component:AdminStudents},
    {path:"applications",component:AdminApplications},
    {path:"stats",component:AdminStats}
  ]},
  {path:"/company",component:CompanyLayout,children:[
    {path:"",component:CompanyDashboard},
    {path:"drives",component:CompanyDrives},
    {path:"drives/:did/apps",component:CompanyApplications},
    {path:"profile",component:CompanyProfileEdit}
  ]},
  {path:"/student",component:StudentLayout,children:[
    {path:"",component:StudentDashboard},
    {path:"drives",component:StudentDrives},
    {path:"applications",component:StudentApplications},
    {path:"profile",component:StudentProfilePage}
  ]}
];

const router=createRouter({history:createWebHashHistory(),routes});
router.beforeEach((to,from,next)=>{
  const pub=["/login","/register"];
  const t=localStorage.getItem("token");
  const r=localStorage.getItem("role");
  if(pub.includes(to.path)){if(t&&r)return next("/"+r);return next()}
  if(!t)return next("/login");
  if(to.path.startsWith("/admin")&&r!=="admin")return next("/login");
  if(to.path.startsWith("/company")&&r!=="company")return next("/login");
  if(to.path.startsWith("/student")&&r!=="student")return next("/login");
  next();
});

const app=Vue.createApp({});
app.use(router);
app.mount("#app");
