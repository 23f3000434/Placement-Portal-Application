from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, StudentProfile, PlacementDrive, Application, CompanyProfile, Interview
from datetime import datetime
import os

student_bp = Blueprint("student", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def student_required(fn):
    """Decorator: ensures the user is a student."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "student":
            return jsonify({"error": "Student access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def get_student_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.student_profile:
        return None
    return user.student_profile


# ──────────────────────────── Dashboard ────────────────────────────

@student_bp.route("/dashboard", methods=["GET"])
@student_required
def dashboard():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404

    total_apps = Application.query.filter_by(student_id=profile.id).count()
    selected = Application.query.filter_by(student_id=profile.id, status="selected").count()
    shortlisted = Application.query.filter_by(student_id=profile.id, status="shortlisted").count()
    pending = Application.query.filter_by(student_id=profile.id, status="applied").count()
    rejected = Application.query.filter_by(student_id=profile.id, status="rejected").count()

    # Upcoming approved drives (for dashboard display)
    upcoming_drives = PlacementDrive.query.filter(
        PlacementDrive.status == "approved",
        PlacementDrive.deadline > datetime.utcnow()
    ).order_by(PlacementDrive.deadline.asc()).limit(5).all()

    drives_list = []
    applied_ids = {a.drive_id for a in Application.query.filter_by(student_id=profile.id).all()}
    for d in upcoming_drives:
        drives_list.append({
            "id": d.id,
            "company_name": d.company.company_name,
            "job_title": d.job_title,
            "package": d.package,
            "deadline": d.deadline.isoformat(),
            "already_applied": d.id in applied_ids,
        })

    # Upcoming interviews
    interviews = Interview.query.filter_by(
        student_id=profile.id, status="scheduled"
    ).order_by(Interview.scheduled_date.asc()).all()

    interviews_list = []
    for i in interviews:
        interviews_list.append({
            "id": i.id,
            "drive_title": i.drive.job_title,
            "company_name": i.drive.company.company_name,
            "scheduled_date": i.scheduled_date.isoformat(),
            "interview_type": i.interview_type,
            "location": i.location,
        })

    return jsonify({
        "name": profile.name,
        "branch": profile.branch,
        "cgpa": profile.cgpa,
        "year": profile.year,
        "total_applications": total_apps,
        "selected": selected,
        "shortlisted": shortlisted,
        "pending": pending,
        "rejected": rejected,
        "upcoming_drives": drives_list,
        "upcoming_interviews": interviews_list,
    }), 200


# ──────────────────────────── Profile ────────────────────────────

@student_bp.route("/profile", methods=["GET"])
@student_required
def get_profile():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({
        "id": profile.id,
        "name": profile.name,
        "email": profile.user.email,
        "branch": profile.branch,
        "cgpa": profile.cgpa,
        "year": profile.year,
        "phone": profile.phone,
        "resume_url": profile.resume_url,
    }), 200


@student_bp.route("/profile", methods=["PUT"])
@student_required
def update_profile():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    if data.get("name", "").strip():
        profile.name = data["name"].strip()
    if data.get("branch", "").strip():
        profile.branch = data["branch"].strip().upper()
    if data.get("cgpa") is not None:
        try:
            cgpa = float(data["cgpa"])
            if cgpa < 0 or cgpa > 10:
                return jsonify({"error": "CGPA must be between 0 and 10"}), 400
            profile.cgpa = cgpa
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid CGPA value"}), 400
    if data.get("year") is not None:
        try:
            year = int(data["year"])
            if year < 2020 or year > 2035:
                return jsonify({"error": "Year must be between 2020 and 2035"}), 400
            profile.year = year
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid year value"}), 400

    profile.phone = data.get("phone", profile.phone)
    profile.resume_url = data.get("resume_url", profile.resume_url)

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ──────────────────────────── Resume Upload ────────────────────────────

@student_bp.route("/upload-resume", methods=["POST"])
@student_required
def upload_resume():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    allowed_extensions = {"pdf", "doc", "docx"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        return jsonify({"error": "Only PDF, DOC, and DOCX files are allowed"}), 400

    # Save file
    filename = f"resume_{profile.id}_{int(datetime.utcnow().timestamp())}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    profile.resume_url = f"/api/student/resume/{filename}"
    db.session.commit()

    return jsonify({"message": "Resume uploaded", "resume_url": profile.resume_url}), 200


@student_bp.route("/resume/<filename>", methods=["GET"])
@jwt_required()
def get_resume(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)


# ──────────────────────────── Browse Drives ────────────────────────────

@student_bp.route("/drives", methods=["GET"])
@student_required
@cache.cached(timeout=60, query_string=True)
def get_approved_drives():
    search = request.args.get("search", "").strip()
    branch_filter = request.args.get("branch", "").strip()
    company_filter = request.args.get("company", "").strip()

    query = PlacementDrive.query.filter_by(status="approved")
    query = query.filter(PlacementDrive.deadline > datetime.utcnow())

    if search:
        query = query.filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.job_description.ilike(f"%{search}%"),
            )
        )

    if branch_filter:
        query = query.filter(PlacementDrive.eligibility_branch.ilike(f"%{branch_filter}%"))

    if company_filter:
        query = query.join(CompanyProfile).filter(
            CompanyProfile.company_name.ilike(f"%{company_filter}%")
        )

    drives = query.order_by(PlacementDrive.deadline.asc()).all()

    profile = get_student_profile()
    applied_drive_ids = set()
    if profile:
        applied_drive_ids = {a.drive_id for a in Application.query.filter_by(student_id=profile.id).all()}

    result = []
    for d in drives:
        result.append({
            "id": d.id,
            "company_name": d.company.company_name,
            "job_title": d.job_title,
            "job_description": d.job_description,
            "package": d.package,
            "eligibility_cgpa": d.eligibility_cgpa,
            "eligibility_branch": d.eligibility_branch,
            "eligibility_year": d.eligibility_year,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "created_at": d.created_at.isoformat(),
            "already_applied": d.id in applied_drive_ids,
        })

    return jsonify(result), 200


# ──────────────────────────── Apply ────────────────────────────

@student_bp.route("/drives/<int:drive_id>/apply", methods=["POST"])
@student_required
def apply_to_drive(drive_id):
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != "approved":
        return jsonify({"error": "This drive is not accepting applications"}), 400

    if drive.deadline and drive.deadline < datetime.utcnow():
        return jsonify({"error": "Application deadline has passed"}), 400

    # Eligibility checks
    if drive.eligibility_cgpa and profile.cgpa < drive.eligibility_cgpa:
        return jsonify({"error": f"Minimum CGPA required: {drive.eligibility_cgpa}. Your CGPA: {profile.cgpa}"}), 400

    if drive.eligibility_branch:
        allowed_branches = [b.strip().upper() for b in drive.eligibility_branch.split(",")]
        if profile.branch.upper() not in allowed_branches:
            return jsonify({"error": f"Your branch ({profile.branch}) is not eligible for this drive"}), 400

    if drive.eligibility_year and profile.year != drive.eligibility_year:
        return jsonify({"error": f"This drive is for {drive.eligibility_year} batch only"}), 400

    # Check duplicate application
    existing = Application.query.filter_by(student_id=profile.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"error": "You have already applied to this drive"}), 409

    application = Application(student_id=profile.id, drive_id=drive_id)
    db.session.add(application)
    db.session.commit()
    cache.clear()

    return jsonify({"message": "Applied successfully", "application_id": application.id}), 201


# ──────────────────────────── My Applications (Placement History) ────────────────────────────

@student_bp.route("/applications", methods=["GET"])
@student_required
def get_my_applications():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404

    applications = Application.query.filter_by(student_id=profile.id).order_by(
        Application.applied_at.desc()
    ).all()

    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "drive_id": a.drive_id,
            "job_title": a.drive.job_title,
            "company_name": a.drive.company.company_name,
            "package": a.drive.package,
            "status": a.status,
            "applied_at": a.applied_at.isoformat(),
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            "deadline": a.drive.deadline.isoformat() if a.drive.deadline else None,
            "drive_status": a.drive.status,
        })

    return jsonify(result), 200


# ──────────────────────────── Export CSV (triggers Celery job) ────────────────────────────

@student_bp.route("/export", methods=["POST"])
@student_required
def export_applications():
    profile = get_student_profile()
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404

    try:
        from tasks import export_student_applications
        task = export_student_applications.delay(profile.id, profile.user.email)
        return jsonify({
            "message": "Export started. You will be notified when it's ready.",
            "task_id": task.id,
        }), 202
    except Exception:
        # If Celery/Redis isn't running, do it synchronously as fallback
        import csv
        import io

        applications = Application.query.filter_by(student_id=profile.id).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date", "Updated Date"])

        for a in applications:
            writer.writerow([
                profile.id,
                a.drive.company.company_name,
                a.drive.job_title,
                a.status,
                a.applied_at.isoformat(),
                a.updated_at.isoformat() if a.updated_at else "",
            ])

        return jsonify({
            "message": "Export complete (synchronous fallback)",
            "csv_data": output.getvalue(),
        }), 200
