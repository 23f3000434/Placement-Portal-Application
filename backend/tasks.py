import csv
import io
import os
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

# Create Celery app
celery_app = Celery(
    "placement_tasks",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
)

celery_app.conf.beat_schedule = {
    "daily-deadline-reminders": {
        "task": "tasks.send_daily_reminders",
        "schedule": crontab(hour=9, minute=0),  # every day at 9 AM
    },
    "monthly-activity-report": {
        "task": "tasks.send_monthly_report",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),  # 1st of every month at 8 AM
    },
}

celery_app.conf.timezone = "Asia/Kolkata"


def get_flask_app():
    """Create Flask app context for Celery tasks that need DB access."""
    from app import create_app
    app = create_app()
    return app


# ──────────────────────────── Task 1: Export Student Applications CSV ────────────────────────────

@celery_app.task(name="tasks.export_student_applications")
def export_student_applications(student_id, email):
    """
    User-triggered async job: exports a student's application history as CSV.
    In production, this would email the CSV or store it for download.
    """
    app = get_flask_app()
    with app.app_context():
        from models import Application, StudentProfile

        profile = StudentProfile.query.get(student_id)
        if not profile:
            return {"error": "Student not found"}

        applications = Application.query.filter_by(student_id=student_id).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date", "Updated Date"])

        for a in applications:
            writer.writerow([
                student_id,
                a.drive.company.company_name,
                a.drive.job_title,
                a.status,
                a.applied_at.strftime("%Y-%m-%d %H:%M"),
                a.updated_at.strftime("%Y-%m-%d %H:%M") if a.updated_at else "",
            ])

        csv_content = output.getvalue()

        # Save to file
        export_dir = os.path.join(os.path.dirname(__file__), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"applications_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(export_dir, filename)

        with open(filepath, "w") as f:
            f.write(csv_content)

        # In production: send email with CSV attachment using Flask-Mail
        # For now, just return the file path
        return {"status": "success", "file": filename, "email": email}


# ──────────────────────────── Task 2: Daily Deadline Reminders ────────────────────────────

@celery_app.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    """
    Scheduled job: sends reminders about drives with deadlines in the next 3 days.
    In production, this would send emails/SMS/webhooks.
    """
    app = get_flask_app()
    with app.app_context():
        from models import PlacementDrive, StudentProfile

        # Find drives with deadlines in the next 3 days
        now = datetime.utcnow()
        upcoming_deadline = now + timedelta(days=3)

        upcoming_drives = PlacementDrive.query.filter(
            PlacementDrive.status == "approved",
            PlacementDrive.deadline > now,
            PlacementDrive.deadline <= upcoming_deadline,
        ).all()

        if not upcoming_drives:
            return {"status": "no upcoming drives"}

        students = StudentProfile.query.all()
        reminders_sent = 0

        for drive in upcoming_drives:
            for student in students:
                # Check eligibility
                eligible = True
                if drive.eligibility_cgpa and student.cgpa < drive.eligibility_cgpa:
                    eligible = False
                if drive.eligibility_branch:
                    allowed = [b.strip().upper() for b in drive.eligibility_branch.split(",")]
                    if student.branch.upper() not in allowed:
                        eligible = False

                if eligible:
                    # In production: send actual email/SMS
                    # For now, just log it
                    print(f"REMINDER: {student.name} ({student.user.email}) - "
                          f"Drive '{drive.job_title}' deadline: {drive.deadline}")
                    reminders_sent += 1

        return {"status": "success", "reminders_sent": reminders_sent}


# ──────────────────────────── Task 3: Monthly Activity Report ────────────────────────────

@celery_app.task(name="tasks.send_monthly_report")
def send_monthly_report():
    """
    Scheduled job: generates monthly placement activity report and sends to admin.
    Generates an HTML report.
    """
    app = get_flask_app()
    with app.app_context():
        from models import User, PlacementDrive, Application
        from flask import render_template_string

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 1:
            prev_month_start = month_start.replace(year=now.year - 1, month=12)
        else:
            prev_month_start = month_start.replace(month=now.month - 1)

        # Stats for previous month
        drives_conducted = PlacementDrive.query.filter(
            PlacementDrive.created_at >= prev_month_start,
            PlacementDrive.created_at < month_start,
        ).count()

        applications_received = Application.query.filter(
            Application.applied_at >= prev_month_start,
            Application.applied_at < month_start,
        ).count()

        students_selected = Application.query.filter(
            Application.applied_at >= prev_month_start,
            Application.applied_at < month_start,
            Application.status == "selected",
        ).count()

        month_name = prev_month_start.strftime("%B %Y")

        html_report = f"""
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .highlight {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        </style></head>
        <body>
            <h1>Monthly Placement Activity Report</h1>
            <h2>{month_name}</h2>
            <table>
                <tr><th>Metric</th><th>Count</th></tr>
                <tr><td>Placement Drives Conducted</td><td class="highlight">{drives_conducted}</td></tr>
                <tr><td>Applications Received</td><td class="highlight">{applications_received}</td></tr>
                <tr><td>Students Selected</td><td class="highlight">{students_selected}</td></tr>
            </table>
            <p style="margin-top: 20px; color: #7f8c8d;">
                This report was auto-generated on {now.strftime("%Y-%m-%d %H:%M")} by the Placement Portal System.
            </p>
        </body>
        </html>
        """

        # Save report
        report_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(report_dir, exist_ok=True)
        filename = f"monthly_report_{prev_month_start.strftime('%Y_%m')}.html"
        filepath = os.path.join(report_dir, filename)

        with open(filepath, "w") as f:
            f.write(html_report)

        # In production: send via Flask-Mail to admin
        admin = User.query.filter_by(role="admin").first()
        if admin:
            print(f"Monthly report for {month_name} sent to {admin.email}")

        return {"status": "success", "report": filename, "month": month_name}
