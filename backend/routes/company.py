from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, CompanyProfile, PlacementDrive, Application, Interview, StudentProfile
from datetime import datetime

company_bp = Blueprint("company", __name__)


def company_required(fn):
    """Decorator: ensures the user is a company."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "company":
            return jsonify({"error": "Company access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def get_company_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.company_profile:
        return None
    return user.company_profile


# ──────────────────────────── Dashboard ────────────────────────────

@company_bp.route("/dashboard", methods=["GET"])
@company_required
def dashboard():
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Company profile not found"}), 404

    drives = PlacementDrive.query.filter_by(company_id=profile.id).all()
    total_applicants = sum(len(d.applications) for d in drives)
    selected_count = sum(
        1 for d in drives for a in d.applications if a.status == "selected"
    )

    return jsonify({
        "company_name": profile.company_name,
        "hr_contact": profile.hr_contact,
        "website": profile.website,
        "description": profile.description,
        "approval_status": profile.approval_status,
        "is_blacklisted": profile.is_blacklisted,
        "total_drives": len(drives),
        "total_applicants": total_applicants,
        "selected_count": selected_count,
    }), 200


# ──────────────────────────── Profile ────────────────────────────

@company_bp.route("/profile", methods=["GET"])
@company_required
def get_profile():
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({
        "id": profile.id,
        "company_name": profile.company_name,
        "hr_contact": profile.hr_contact,
        "website": profile.website,
        "description": profile.description,
        "approval_status": profile.approval_status,
        "email": profile.user.email,
    }), 200


@company_bp.route("/profile", methods=["PUT"])
@company_required
def update_profile():
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    if data.get("company_name", "").strip():
        profile.company_name = data["company_name"].strip()
    profile.hr_contact = data.get("hr_contact", profile.hr_contact)
    profile.website = data.get("website", profile.website)
    profile.description = data.get("description", profile.description)

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ──────────────────────────── Placement Drives ────────────────────────────

@company_bp.route("/drives", methods=["GET"])
@company_required
def get_drives():
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drives = PlacementDrive.query.filter_by(company_id=profile.id).order_by(
        PlacementDrive.created_at.desc()
    ).all()

    result = []
    for d in drives:
        result.append({
            "id": d.id,
            "job_title": d.job_title,
            "job_description": d.job_description,
            "package": d.package,
            "eligibility_cgpa": d.eligibility_cgpa,
            "eligibility_branch": d.eligibility_branch,
            "eligibility_year": d.eligibility_year,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "status": d.status,
            "total_applications": len(d.applications),
            "created_at": d.created_at.isoformat(),
        })

    return jsonify(result), 200


@company_bp.route("/drives", methods=["POST"])
@company_required
def create_drive():
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    if profile.approval_status != "approved":
        return jsonify({"error": "Your company must be approved by admin before creating drives"}), 403

    if profile.is_blacklisted:
        return jsonify({"error": "Your company is blacklisted"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    job_title = data.get("job_title", "").strip()
    job_description = data.get("job_description", "").strip()
    deadline_str = data.get("deadline", "").strip()

    if not job_title:
        return jsonify({"error": "Job title is required"}), 400
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400
    if not deadline_str:
        return jsonify({"error": "Deadline is required"}), 400

    try:
        deadline = datetime.fromisoformat(deadline_str)
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use ISO format: YYYY-MM-DDTHH:MM:SS"}), 400

    if deadline < datetime.utcnow():
        return jsonify({"error": "Deadline must be in the future"}), 400

    eligibility_cgpa = 0
    if data.get("eligibility_cgpa"):
        try:
            eligibility_cgpa = float(data["eligibility_cgpa"])
            if eligibility_cgpa < 0 or eligibility_cgpa > 10:
                return jsonify({"error": "CGPA must be between 0 and 10"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid CGPA value"}), 400

    drive = PlacementDrive(
        company_id=profile.id,
        job_title=job_title,
        job_description=job_description,
        package=data.get("package", "").strip(),
        eligibility_cgpa=eligibility_cgpa,
        eligibility_branch=data.get("eligibility_branch", "").strip().upper(),
        eligibility_year=int(data["eligibility_year"]) if data.get("eligibility_year") else None,
        deadline=deadline,
    )

    db.session.add(drive)
    db.session.commit()
    cache.clear()

    return jsonify({"message": "Drive created, pending admin approval", "drive_id": drive.id}), 201


@company_bp.route("/drives/<int:drive_id>", methods=["PUT"])
@company_required
def update_drive(drive_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != profile.id:
        return jsonify({"error": "Not your drive"}), 403

    data = request.get_json()
    if data.get("job_title", "").strip():
        drive.job_title = data["job_title"].strip()
    if data.get("job_description", "").strip():
        drive.job_description = data["job_description"].strip()
    drive.package = data.get("package", drive.package)
    if data.get("eligibility_cgpa") is not None:
        drive.eligibility_cgpa = float(data["eligibility_cgpa"])
    drive.eligibility_branch = data.get("eligibility_branch", drive.eligibility_branch)
    drive.eligibility_year = data.get("eligibility_year", drive.eligibility_year)

    if data.get("deadline"):
        try:
            drive.deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"error": "Invalid deadline format"}), 400

    db.session.commit()
    cache.clear()
    return jsonify({"message": "Drive updated"}), 200


@company_bp.route("/drives/<int:drive_id>/close", methods=["PUT"])
@company_required
def close_drive(drive_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != profile.id:
        return jsonify({"error": "Not your drive"}), 403

    drive.status = "closed"
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Drive closed"}), 200


# ──────────────────────────── Application Management ────────────────────────────

@company_bp.route("/drives/<int:drive_id>/applications", methods=["GET"])
@company_required
def get_applications(drive_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != profile.id:
        return jsonify({"error": "Not your drive"}), 403

    applications = Application.query.filter_by(drive_id=drive_id).all()

    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "student_id": a.student_id,
            "student_name": a.student.name,
            "student_email": a.student.user.email,
            "student_branch": a.student.branch,
            "student_cgpa": a.student.cgpa,
            "student_year": a.student.year,
            "student_phone": a.student.phone,
            "resume_url": a.student.resume_url,
            "status": a.status,
            "applied_at": a.applied_at.isoformat(),
        })

    return jsonify(result), 200


@company_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
@company_required
def update_application_status(app_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    application = Application.query.get_or_404(app_id)

    drive = PlacementDrive.query.get(application.drive_id)
    if not drive or drive.company_id != profile.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json()
    new_status = data.get("status", "").strip()

    if new_status not in ("shortlisted", "selected", "rejected"):
        return jsonify({"error": "Status must be 'shortlisted', 'selected', or 'rejected'"}), 400

    application.status = new_status
    db.session.commit()

    return jsonify({"message": f"Application status updated to {new_status}"}), 200


# ──────────────────────────── Interview Scheduling ────────────────────────────

@company_bp.route("/drives/<int:drive_id>/interviews", methods=["GET"])
@company_required
def get_interviews(drive_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != profile.id:
        return jsonify({"error": "Not your drive"}), 403

    interviews = Interview.query.filter_by(drive_id=drive_id).order_by(Interview.scheduled_date.asc()).all()

    result = []
    for i in interviews:
        result.append({
            "id": i.id,
            "student_id": i.student_id,
            "student_name": i.student.name,
            "student_email": i.student.user.email,
            "scheduled_date": i.scheduled_date.isoformat(),
            "interview_type": i.interview_type,
            "location": i.location,
            "notes": i.notes,
            "status": i.status,
        })

    return jsonify(result), 200


@company_bp.route("/drives/<int:drive_id>/interviews", methods=["POST"])
@company_required
def schedule_interview(drive_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != profile.id:
        return jsonify({"error": "Not your drive"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    student_id = data.get("student_id")
    scheduled_date_str = data.get("scheduled_date", "").strip()

    if not student_id:
        return jsonify({"error": "Student ID is required"}), 400
    if not scheduled_date_str:
        return jsonify({"error": "Scheduled date is required"}), 400

    # Verify student has applied to this drive
    application = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    if not application:
        return jsonify({"error": "Student has not applied to this drive"}), 400

    try:
        scheduled_date = datetime.fromisoformat(scheduled_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    interview = Interview(
        drive_id=drive_id,
        student_id=student_id,
        scheduled_date=scheduled_date,
        interview_type=data.get("interview_type", "online").strip(),
        location=data.get("location", "").strip(),
        notes=data.get("notes", "").strip(),
    )

    db.session.add(interview)
    db.session.commit()

    return jsonify({"message": "Interview scheduled", "interview_id": interview.id}), 201


@company_bp.route("/interviews/<int:interview_id>", methods=["PUT"])
@company_required
def update_interview(interview_id):
    profile = get_company_profile()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    interview = Interview.query.get_or_404(interview_id)
    drive = PlacementDrive.query.get(interview.drive_id)
    if not drive or drive.company_id != profile.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json()

    if data.get("scheduled_date"):
        try:
            interview.scheduled_date = datetime.fromisoformat(data["scheduled_date"])
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    interview.interview_type = data.get("interview_type", interview.interview_type)
    interview.location = data.get("location", interview.location)
    interview.notes = data.get("notes", interview.notes)
    interview.status = data.get("status", interview.status)

    db.session.commit()
    return jsonify({"message": "Interview updated"}), 200
