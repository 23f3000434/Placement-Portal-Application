const api = axios.create({ baseURL: window.location.origin + "/api", headers: {"Content-Type":"application/json"} });
api.interceptors.request.use(c => { const t = localStorage.getItem("token"); if(t) c.headers.Authorization = "Bearer "+t; return c; });
api.interceptors.response.use(r=>r, e=>{ if(e.response && e.response.status===401){localStorage.clear();location.hash="#/login"} return Promise.reject(e); });
function logout(){localStorage.clear();location.hash="#/login";location.reload()}
function fmtDate(d){return d?new Date(d).toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"}):"-"}
