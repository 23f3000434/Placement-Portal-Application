// API helper — wraps axios with auth token and base URL
const API_BASE = "http://localhost:5000/api";

const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401/403 globally — redirect to login
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && (error.response.status === 401)) {
            localStorage.clear();
            window.location.hash = "#/login";
        }
        return Promise.reject(error);
    }
);

// Auth helpers
function getToken() { return localStorage.getItem("token"); }
function getRole() { return localStorage.getItem("role"); }
function getUserId() { return localStorage.getItem("user_id"); }
function isLoggedIn() { return !!getToken(); }

function logout() {
    localStorage.clear();
    window.location.hash = "#/login";
}
