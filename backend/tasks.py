import csv, io, os, json
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("tasks", broker="redis://localhost:6379/1", backend="redis://localhost:6379/1")
celery_app.conf.beat_schedule = {
    "daily-reminders": {"task": "tasks.send_daily_reminders", "schedule": crontab(hour=9, minute=0)},
    "monthly-report": {"task": "tasks.send_monthly_report", "schedule": crontab(day_of_month=1, hour=8, minute=0)},
}
celery_app.conf.timezone = "Asia/Kolkata"


def _app():
    import sys
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from app import create_app
    return create_app()


def _send_email(app, to, subject, html_body):
    """Send email using Flask-Mail. Falls back to console log if not configured."""
    try:
        from flask_mail import Message
        from extensions import mail
        with app.app_context():
            msg = Message(subject=subject, recipients=[to], html=html_body)
            mail.send(msg)
            return True
    except Exception as e:
        print(f"[EMAIL] Would send to {to}: {subject} (mail not configured: {e})")
        return False


def _send_gchat_webhook(text):
    """Send message via Google Chat Webhook. Set GCHAT_WEBHOOK_URL env var."""
    url = os.environ.get("GCHAT_WEBHOOK_URL", "")
    if not url:
        print(f"[GCHAT WEBHOOK] {text}")
        return False
    try:
        import urllib.request
        data = json.dumps({"text": text}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        print(f"[GCHAT WEBHOOK FAILED] {e}")
        return False


# ── Task A: Daily Reminders (Google Chat Webhook / Email) ──
@celery_app.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    """
    Scheduled: runs daily at 9 AM IST.
    For each approved drive whose deadline is in the next 3 days, emails every active student
    who has not applied yet (no CGPA/branch/year filter — matches project brief wording).
    Uses Google Chat Webhook if configured, falls back to email, falls back to console.
    """
    app = _app()
    with app.app_context():
        from models import PlacementDrive, StudentProfile, Application
        now = datetime.utcnow()
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == "approved",
            PlacementDrive.deadline > now,
            PlacementDrive.deadline <= now + timedelta(days=3)
        ).all()
        if not drives:
            return {"status": "no upcoming drives", "reminders": 0}

        count = 0
        for d in drives:
            for s in StudentProfile.query.all():
                if not s.user or not s.user.is_active:
                    continue
                if Application.query.filter_by(student_id=s.id, drive_id=d.id).first():
                    continue
                msg = (
                    f"Reminder: '{d.job_title}' by {d.company.company_name} — "
                    f"deadline {d.deadline.strftime('%d %b %Y')}. "
                    f"Open the Placement Portal to review eligibility and apply if you qualify."
                )
                _send_gchat_webhook(f"@{s.name} ({s.user.email}): {msg}")
                _send_email(
                    app, s.user.email, f"Deadline Reminder: {d.job_title}",
                    f"<p>Hi {s.name},</p><p>{msg}</p>",
                )
                count += 1

        return {"status": "success", "reminders_sent": count}


# ── Task B: Monthly Activity Report (HTML via Email) ──
@celery_app.task(name="tasks.send_monthly_report")
def send_monthly_report():
    """
    Scheduled: runs on 1st of every month at 8 AM IST.
    Generates HTML report, saves file, and sends to admin via email.
    """
    app = _app()
    with app.app_context():
        from models import User, PlacementDrive, Application
        from extensions import db
        now = datetime.utcnow()
        ms = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ps = ms.replace(month=ms.month - 1) if ms.month > 1 else ms.replace(year=ms.year - 1, month=12)

        # Drives "conducted" in period: approved drives that received at least one application in the month
        from sqlalchemy import func
        drives_conducted = db.session.query(func.count(func.distinct(Application.drive_id))).filter(
            Application.applied_at >= ps, Application.applied_at < ms).scalar() or 0
        new_drives_count = PlacementDrive.query.filter(
            PlacementDrive.created_at >= ps, PlacementDrive.created_at < ms,
            PlacementDrive.status == "approved").count()
        apps_count = Application.query.filter(
            Application.applied_at >= ps, Application.applied_at < ms).count()
        selected_count = Application.query.filter(
            Application.applied_at >= ps, Application.applied_at < ms,
            Application.status == "selected").count()

        month_name = ps.strftime("%B %Y")

        html = f"""
        <html><head><style>
            body {{ font-family: Arial, sans-serif; padding: 20px; background: #fff; color: #111; }}
            h1 {{ border-bottom: 2px solid #111; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #333; padding: 12px; text-align: left; }}
            th {{ background: #111; color: #fff; }}
            tr:nth-child(even) {{ background: #f5f5f5; }}
            .val {{ font-size: 1.5em; font-weight: bold; }}
        </style></head>
        <body>
            <h1>Monthly Placement Activity Report</h1>
            <h2>{month_name}</h2>
            <table>
                <tr><th>Metric</th><th>Count</th></tr>
                <tr><td>Drives with applicant activity (distinct drives)</td><td class="val">{drives_conducted}</td></tr>
                <tr><td>New approved drives created in period</td><td class="val">{new_drives_count}</td></tr>
                <tr><td>Total applications received</td><td class="val">{apps_count}</td></tr>
                <tr><td>Applications marked selected</td><td class="val">{selected_count}</td></tr>
            </table>
            <p style="color:#666;margin-top:20px;">Auto-generated on {now.strftime('%Y-%m-%d %H:%M')} by Placement Portal.</p>
        </body></html>
        """

        # Save HTML report
        rdir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(rdir, exist_ok=True)
        html_fname = f"report_{ps.strftime('%Y_%m')}.html"
        with open(os.path.join(rdir, html_fname), "w") as f:
            f.write(html)

        # Send to admin via email
        admin = User.query.filter_by(role="admin").first()
        if admin:
            _send_email(app, admin.email, f"Monthly Placement Report — {month_name}", html)
            _send_gchat_webhook(
                f"Monthly Report for {month_name}: {drives_conducted} drives with applications, "
                f"{apps_count} applications, {selected_count} selected"
            )

        return {"status": "success", "html_file": html_fname, "month": month_name}


# ── Task C: Export Student Applications as CSV (User-Triggered Async) ──
@celery_app.task(name="tasks.export_student_applications")
def export_student_applications(student_id, email):
    """
    User-triggered async job: exports placement application history as CSV.
    Saves file and sends alert via email when done.
    """
    app = _app()
    with app.app_context():
        from models import Application, StudentProfile
        p = StudentProfile.query.get(student_id)
        if not p:
            return {"error": "Not found"}

        apps = Application.query.filter_by(student_id=student_id).all()
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date", "Updated Date"])
        for a in apps:
            w.writerow([
                student_id,
                a.drive.company.company_name,
                a.drive.job_title,
                a.status,
                a.applied_at.strftime("%Y-%m-%d %H:%M"),
                a.updated_at.strftime("%Y-%m-%d %H:%M") if a.updated_at else ""
            ])

        export_dir = os.path.join(os.path.dirname(__file__), "exports")
        os.makedirs(export_dir, exist_ok=True)
        fname = f"export_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(export_dir, fname)
        with open(filepath, "w") as f:
            f.write(out.getvalue())

        # Send alert to student when done
        _send_email(
            app, email,
            "Your Placement Application Export is Ready",
            f"<p>Hi,</p><p>Your CSV export is ready: <strong>{fname}</strong></p><p>You can download it from your dashboard.</p>"
        )
        _send_gchat_webhook(f"CSV export ready for student {email}: {fname}")

        return {"status": "success", "file": fname, "email": email, "student_id": student_id}
