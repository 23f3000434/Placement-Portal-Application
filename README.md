# Placement Portal Application (PPA)

A web-based placement management system for institutes to manage campus recruitment activities.

## Tech Stack

- **Backend:** Flask, SQLite, Flask-SQLAlchemy, Flask-JWT-Extended
- **Frontend:** Vue.js 3 (CDN), Bootstrap 5, Chart.js
- **Caching:** Redis + Flask-Caching
- **Background Jobs:** Celery + Redis
- **Auth:** JWT (JSON Web Tokens) + bcrypt

## Roles

| Role | Description |
|------|-------------|
| **Admin** | Pre-seeded superuser. Manages companies, students, drives. |
| **Company** | Registers, creates placement drives (after admin approval), manages applications. |
| **Student** | Registers, browses drives, applies, tracks application status. |

## Setup & Run

### 1. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Redis (required for caching & Celery)

```bash
# macOS
brew install redis
redis-server

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

### 3. Run the Flask backend

```bash
cd backend
python app.py
```

This will:
- Create the SQLite database (`instance/placement.db`)
- Seed the admin user
- Start the server on `http://localhost:5000`

### 4. Open the frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 8080
```

Then visit `http://localhost:8080`

### 5. (Optional) Start Celery worker & beat

```bash
# In a new terminal
cd backend
celery -A tasks.celery_app worker --loglevel=info

# In another terminal (for scheduled tasks)
cd backend
celery -A tasks.celery_app beat --loglevel=info
```

## Default Admin Login

- **Email:** admin@placement.com
- **Password:** admin123

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register student/company |
| POST | `/api/auth/login` | Login |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard stats |
| GET | `/api/admin/companies` | List companies |
| PUT | `/api/admin/companies/:id/approve` | Approve company |
| PUT | `/api/admin/companies/:id/reject` | Reject company |
| PUT | `/api/admin/companies/:id/blacklist` | Toggle blacklist |
| GET | `/api/admin/drives` | List all drives |
| PUT | `/api/admin/drives/:id/approve` | Approve drive |
| PUT | `/api/admin/drives/:id/reject` | Reject drive |
| PUT | `/api/admin/drives/:id/close` | Close drive |
| GET | `/api/admin/students` | List students |
| PUT | `/api/admin/users/:id/toggle-active` | Activate/deactivate user |
| GET | `/api/admin/applications` | All applications |

### Company
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/company/dashboard` | Company dashboard |
| GET | `/api/company/profile` | Get profile |
| PUT | `/api/company/profile` | Update profile |
| GET | `/api/company/drives` | List own drives |
| POST | `/api/company/drives` | Create new drive |
| PUT | `/api/company/drives/:id` | Update drive |
| PUT | `/api/company/drives/:id/close` | Close drive |
| GET | `/api/company/drives/:id/applications` | View applications |
| PUT | `/api/company/applications/:id/status` | Update app status |

### Student
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/student/dashboard` | Student dashboard |
| GET | `/api/student/profile` | Get profile |
| PUT | `/api/student/profile` | Update profile |
| GET | `/api/student/drives` | Browse approved drives |
| POST | `/api/student/drives/:id/apply` | Apply to drive |
| GET | `/api/student/applications` | My applications |
| POST | `/api/student/export` | Export applications CSV |

## Background Jobs

1. **Daily Reminders** — Sends reminders about drives with deadlines in next 3 days (9 AM daily)
2. **Monthly Report** — Generates HTML placement activity report (1st of each month)
3. **CSV Export** — Student-triggered async export of application history

## Project Structure

```
placement-portal/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config.py           # Configuration
│   ├── extensions.py       # Flask extensions
│   ├── models.py           # SQLAlchemy models
│   ├── seed.py             # Admin seeder
│   ├── tasks.py            # Celery background tasks
│   ├── requirements.txt
│   └── routes/
│       ├── auth.py         # Auth endpoints
│       ├── admin.py        # Admin endpoints
│       ├── company.py      # Company endpoints
│       └── student.py      # Student endpoints
├── frontend/
│   ├── index.html          # Entry point (Jinja2/CDN)
│   └── js/
│       ├── api.js          # Axios API helper
│       ├── app.js          # Vue Router + app init
│       ├── components.js   # Sidebar + layout components
│       └── pages/          # All page components
└── README.md
```
