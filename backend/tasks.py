import csv, io, os
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
    from app import create_app
    return create_app()

@celery_app.task(name="tasks.export_student_applications")
def export_student_applications(student_id, email):
    app = _app()
    with app.app_context():
        from models import Application, StudentProfile
        p = StudentProfile.query.get(student_id)
        if not p: return {"error": "Not found"}
        apps = Application.query.filter_by(student_id=student_id).all()
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Student ID","Company Name","Drive Title","Status","Applied Date","Updated Date"])
        for a in apps:
            w.writerow([student_id, a.drive.company.company_name, a.drive.job_title, a.status,
                a.applied_at.strftime("%Y-%m-%d %H:%M"), a.updated_at.strftime("%Y-%m-%d %H:%M") if a.updated_at else ""])
        export_dir = os.path.join(os.path.dirname(__file__), "exports")
        os.makedirs(export_dir, exist_ok=True)
        fname = f"export_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(os.path.join(export_dir, fname), "w") as f: f.write(out.getvalue())
        return {"status": "success", "file": fname}

@celery_app.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    app = _app()
    with app.app_context():
        from models import PlacementDrive, StudentProfile
        now = datetime.utcnow()
        drives = PlacementDrive.query.filter(PlacementDrive.status=="approved",
            PlacementDrive.deadline > now, PlacementDrive.deadline <= now + timedelta(days=3)).all()
        count = 0
        for d in drives:
            for s in StudentProfile.query.all():
                eligible = True
                if d.eligibility_cgpa and s.cgpa < d.eligibility_cgpa: eligible = False
                if d.eligibility_branch:
                    if s.branch.upper() not in [b.strip().upper() for b in d.eligibility_branch.split(",")]: eligible = False
                if eligible:
                    print(f"REMINDER: {s.name} - '{d.job_title}' deadline {d.deadline}")
                    count += 1
        return {"reminders": count}

@celery_app.task(name="tasks.send_monthly_report")
def send_monthly_report():
    app = _app()
    with app.app_context():
        from models import User, PlacementDrive, Application
        now = datetime.utcnow()
        ms = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ps = ms.replace(month=ms.month-1) if ms.month > 1 else ms.replace(year=ms.year-1, month=12)
        dc = PlacementDrive.query.filter(PlacementDrive.created_at >= ps, PlacementDrive.created_at < ms).count()
        ac = Application.query.filter(Application.applied_at >= ps, Application.applied_at < ms).count()
        sc = Application.query.filter(Application.applied_at >= ps, Application.applied_at < ms, Application.status=="selected").count()
        mn = ps.strftime("%B %Y")
        html = f"<html><body><h1>Monthly Report - {mn}</h1><table border=1><tr><th>Metric</th><th>Count</th></tr><tr><td>Drives</td><td>{dc}</td></tr><tr><td>Applications</td><td>{ac}</td></tr><tr><td>Selected</td><td>{sc}</td></tr></table></body></html>"
        rdir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(rdir, exist_ok=True)
        fname = f"report_{ps.strftime('%Y_%m')}.html"
        with open(os.path.join(rdir, fname), "w") as f: f.write(html)
        return {"status": "success", "file": fname}
