# Placement Portal Application

Flask API + Vue (CDN) + Bootstrap frontend, SQLite database, Redis for caching and Celery. See the course project brief for full requirements.

Commands below use **bash** or **zsh** (macOS default). From `backend/`, always run `source .venv/bin/activate` before Python/Celery.

## Prerequisites

- Python 3.10+ (recommended)
- [Redis](https://redis.io/) on `localhost:6379` (DB `0` = cache, DB `1` = Celery broker/results)
- Optional: [MailHog](https://github.com/mailhog/MailHog) for local email (`SMTP` port `1025`, web UI `http://127.0.0.1:8025`)

### Install Redis and MailHog

**macOS (Homebrew)**

```bash
brew install python@3.12 redis
brew services start redis
```

Optional MailHog (SMTP `1025`, web UI `8025`):

```bash
brew install mailhog
mailhog
```

Leave that terminal open, then open **http://127.0.0.1:8025**.

**Linux** (examples)

```bash
# Fedora / RHEL-style
sudo dnf install redis python3
sudo systemctl enable --now redis

# Debian / Ubuntu
sudo apt install redis-server python3 python3-venv
sudo systemctl enable --now redis-server
```

Start Redis in the foreground if you are not using systemd:

```bash
redis-server
```

## First-time setup

From the project root (the folder that contains `backend/` and `frontend/`):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On **macOS**, if `python3` is missing, install Python from [python.org](https://www.python.org/downloads/macos/) or use `brew install python@3.12` and ensure `python3` is on your `PATH`.

### Environment (optional MailHog)

For local development, load MailHog settings before **Flask** and **Celery** (same shell or each terminal):

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
```

Without MailHog, configure real SMTP via environment variables (see `backend/config.py`: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`).

## Run the web app

The SQLite file `backend/placement.db` is created on first run. Admin and demo data are seeded from `backend/seed.py`.

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
python app.py
```

Open **http://127.0.0.1:5000** (Flask serves the Vue SPA and static assets).

Default seeded accounts are defined in `backend/seed.py` (admin user and test student `a@a.com`). Check that file or the console output after the first start for exact emails and passwords.

## Celery worker (required for background jobs)

Run from **`backend/`** so `tasks` imports correctly:

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
celery -A tasks.celery_app worker --loglevel=info
```

## Celery Beat (scheduled jobs — optional for demos)

Runs **daily reminders** (9:00 IST) and **monthly report** (1st of month, 8:00 IST) per `backend/tasks.py`:

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
celery -A tasks.celery_app beat --loglevel=info
```

You still need a **worker** running to execute those schedules.

## Trigger scheduled tasks immediately (manual run)

With Redis up and a **worker** running in another terminal, from `backend/`:

**Daily reminders** (deadline reminders email / webhook):

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
celery -A tasks.celery_app call tasks.send_daily_reminders
```

**Monthly activity report** (HTML report + email to admin):

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
celery -A tasks.celery_app call tasks.send_monthly_report
```

**Student CSV export** is normally triggered from the student dashboard. To run it once from the CLI (worker must be running):

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
celery -A tasks.celery_app call tasks.export_student_applications --args='[1,"student@example.com"]'
```

Replace `1` with the student profile ID and the email with that student’s login email.

## Optional smoke test

```bash
cd backend
source .venv/bin/activate
set -a && source mailhog.dev.env && set +a
python verify_core.py
```

## Clean submission / zip checklist

- Do **not** include `.venv/`, `__pycache__/`, `*.pyc`, `placement.db`, Redis `dump.rdb`, or Celery Beat schedule files (`celerybeat-schedule*`).
- Generated folders (`exports/`, `uploads/resumes/`, `reports/*.html`) are empty or only contain `.gitkeep` in this repo; they refill at runtime.
