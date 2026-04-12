from extensions import db
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from datetime import datetime, timedelta
import bcrypt


def _pw(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def seed_admin():
    if User.query.filter_by(role="admin").first():
        return
    db.session.add(User(email="ashuathu93@gmail.com", password=_pw("admin123"), role="admin", is_active=True))
    db.session.commit()
    print("Admin seeded: ashuathu93@gmail.com / admin123")


def seed_test_student_a():
    """Guaranteed login for manual / CI checks: a@a.com / 123456 (upsert)."""
    email = "a@a.com"
    u = User.query.filter_by(email=email).first()
    if u:
        u.password = _pw("123456")
        u.role = "student"
        u.is_active = True
        db.session.flush()
        sp = u.student_profile
        if sp:
            sp.name = "Alex Test"
            sp.branch = "CSE"
            sp.cgpa = 9.0
            sp.year = 2026
            sp.phone = sp.phone or ""
        else:
            db.session.add(StudentProfile(
                user_id=u.id, name="Alex Test", branch="CSE", cgpa=9.0, year=2026, phone=""))
    else:
        u = User(email=email, password=_pw("123456"), role="student", is_active=True)
        db.session.add(u)
        db.session.flush()
        db.session.add(StudentProfile(
            user_id=u.id, name="Alex Test", branch="CSE", cgpa=9.0, year=2026, phone=""))
    db.session.commit()
    print("Test student ready: a@a.com / 123456")


def seed_demo_data():
    """Populate DB with demo students, companies, drives, and applications."""
    # Skip if already seeded
    if StudentProfile.query.count() > 0:
        return

    # ── 4 Students ──
    students_data = [
        {"email": "rahul.sharma@student.com", "name": "Rahul Sharma", "branch": "CSE", "cgpa": 8.7, "year": 2026, "phone": "9876543210"},
        {"email": "priya.patel@student.com", "name": "Priya Patel", "branch": "ECE", "cgpa": 9.1, "year": 2026, "phone": "9876543211"},
        {"email": "amit.kumar@student.com", "name": "Amit Kumar", "branch": "IT", "cgpa": 7.5, "year": 2026, "phone": "9876543212"},
        {"email": "sneha.reddy@student.com", "name": "Sneha Reddy", "branch": "CSE", "cgpa": 8.2, "year": 2026, "phone": "9876543213"},
    ]

    student_profiles = []
    for s in students_data:
        u = User(email=s["email"], password=_pw("student123"), role="student", is_active=True)
        db.session.add(u)
        db.session.flush()
        sp = StudentProfile(user_id=u.id, name=s["name"], branch=s["branch"], cgpa=s["cgpa"], year=s["year"], phone=s["phone"])
        db.session.add(sp)
        student_profiles.append(sp)

    # ── 3 Companies (all approved) ──
    companies_data = [
        {"email": "hr@google.com", "company_name": "Google India", "hr_contact": "Sunita Verma", "website": "https://careers.google.com", "description": "Global technology leader in search, cloud, and AI."},
        {"email": "hr@infosys.com", "company_name": "Infosys", "hr_contact": "Rajesh Nair", "website": "https://www.infosys.com/careers", "description": "Leading IT services and consulting company."},
        {"email": "hr@flipkart.com", "company_name": "Flipkart", "hr_contact": "Meera Joshi", "website": "https://www.flipkartcareers.com", "description": "India's leading e-commerce marketplace."},
    ]

    company_profiles = []
    for co in companies_data:
        u = User(email=co["email"], password=_pw("company123"), role="company", is_active=True)
        db.session.add(u)
        db.session.flush()
        cp = CompanyProfile(user_id=u.id, company_name=co["company_name"], hr_contact=co["hr_contact"],
                            website=co["website"], description=co["description"], approval_status="approved")
        db.session.add(cp)
        company_profiles.append(cp)

    db.session.flush()

    # ── 5 Placement Drives ──
    drives_data = [
        {"company_idx": 0, "job_title": "SDE Intern", "job_description": "Work on Google Search infrastructure. Build scalable distributed systems.", "package": "12 LPA", "eligibility_cgpa": 8.0, "eligibility_branch": "CSE,IT", "eligibility_year": 2026, "days_ahead": 25, "status": "approved"},
        {"company_idx": 0, "job_title": "Data Analyst", "job_description": "Analyze user behavior data. Build dashboards and insights.", "package": "10 LPA", "eligibility_cgpa": 7.0, "eligibility_branch": "CSE,ECE,IT", "eligibility_year": 2026, "days_ahead": 30, "status": "approved"},
        {"company_idx": 1, "job_title": "Systems Engineer", "job_description": "Join Infosys as a Systems Engineer. Training provided.", "package": "6 LPA", "eligibility_cgpa": 6.5, "eligibility_branch": "CSE,ECE,IT,EE,ME", "eligibility_year": 2026, "days_ahead": 20, "status": "approved"},
        {"company_idx": 2, "job_title": "Backend Developer", "job_description": "Build Flipkart's backend services using Java/Python microservices.", "package": "14 LPA", "eligibility_cgpa": 8.0, "eligibility_branch": "CSE,IT", "eligibility_year": 2026, "days_ahead": 15, "status": "approved"},
        {"company_idx": 2, "job_title": "Product Analyst", "job_description": "Analyze product metrics and drive growth strategies.", "package": "9 LPA", "eligibility_cgpa": 7.0, "eligibility_branch": "CSE,ECE,IT,ME", "eligibility_year": 2026, "days_ahead": 35, "status": "pending"},
    ]

    drives = []
    for d in drives_data:
        drive = PlacementDrive(
            company_id=company_profiles[d["company_idx"]].id,
            job_title=d["job_title"], job_description=d["job_description"],
            package=d["package"], eligibility_cgpa=d["eligibility_cgpa"],
            eligibility_branch=d["eligibility_branch"], eligibility_year=d["eligibility_year"],
            deadline=datetime.utcnow() + timedelta(days=d["days_ahead"]),
            status=d["status"],
            created_at=datetime.utcnow() - timedelta(days=5)  # created 5 days ago
        )
        db.session.add(drive)
        drives.append(drive)

    db.session.flush()

    # ── Applications (students apply to eligible drives) ──
    applications_data = [
        # Rahul (CSE, 8.7) → Google SDE, Google Data Analyst, Flipkart Backend
        {"student_idx": 0, "drive_idx": 0, "status": "shortlisted"},
        {"student_idx": 0, "drive_idx": 1, "status": "selected"},
        {"student_idx": 0, "drive_idx": 3, "status": "applied"},

        # Priya (ECE, 9.1) → Google Data Analyst, Infosys Systems Engineer
        {"student_idx": 1, "drive_idx": 1, "status": "selected"},
        {"student_idx": 1, "drive_idx": 2, "status": "applied"},

        # Amit (IT, 7.5) → Google Data Analyst, Infosys Systems Engineer
        {"student_idx": 2, "drive_idx": 1, "status": "applied"},
        {"student_idx": 2, "drive_idx": 2, "status": "shortlisted"},

        # Sneha (CSE, 8.2) → Google SDE, Flipkart Backend, Infosys
        {"student_idx": 3, "drive_idx": 0, "status": "selected"},
        {"student_idx": 3, "drive_idx": 3, "status": "shortlisted"},
        {"student_idx": 3, "drive_idx": 2, "status": "applied"},
    ]

    for a in applications_data:
        app = Application(
            student_id=student_profiles[a["student_idx"]].id,
            drive_id=drives[a["drive_idx"]].id,
            status=a["status"],
            applied_at=datetime.utcnow() - timedelta(days=3)  # applied 3 days ago
        )
        db.session.add(app)

    # Set interview for shortlisted Rahul at Google SDE
    db.session.flush()
    rahul_app = Application.query.filter_by(
        student_id=student_profiles[0].id, drive_id=drives[0].id).first()
    if rahul_app:
        rahul_app.interview_date = datetime.utcnow() + timedelta(days=7)
        rahul_app.interview_link = "https://meet.google.com/abc-xyz"
        rahul_app.interview_notes = "Round 1: DSA + Problem Solving (45 min)"

    db.session.commit()
    print(f"Demo data seeded: {len(students_data)} students, {len(companies_data)} companies, {len(drives_data)} drives, {len(applications_data)} applications")
