from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, CompanyProfile, PlacementDrive, Application
from datetime import datetime

company_bp = Blueprint("company", __name__)


def company_required(fn):
    """Decorator: ensures the user is an approved company."""
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
    """Helper to get the current company's profile."""
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

    return jsonify({
        "company_name": profile.company_name,
        "hr_contact": profile.hr_contact,
        "website": profile.website,
        "description": profile.description,
        "approval_status": profile.approval_status,
        "is_blacklisted": profile.is_blacklisted,
        "total_drives": len(drives),
        "total_applicants": total_applicants,
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
    profile.company_name = data.get("company_name", profile.company_name)
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

    job_title = data.get("job_title", "").strip()
    job_description = data.get("job_description", "").strip()
    deadline_str = data.get("deadline", "").strip()

    if not job_title or not job_description or not deadline_str:
        return jsonify({"error": "Job title, description, and deadline are required"}), 400

    try:
        deadline = datetime.fromisoformat(deadline_str)
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use ISO format: YYYY-MM-DDTHH:MM:SS"}), 400

    drive = PlacementDrive(
        company_id=profile.id,
        job_title=job_title,
        job_description=job_description,
        package=data.get("package", ""),
        eligibility_cgpa=float(data.get("eligibility_cgpa", 0)),
        eligibility_branch=data.get("eligibility_branch", ""),
        eligibility_year=int(data.get("eligibility_year", 0)) if data.get("eligibility_year") else None,
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
    drive.job_title = data.get("job_title", drive.job_title)
    drive.job_description = data.get("job_description", drive.job_description)
    drive.package = data.get("package", drive.package)
    drive.eligibility_cgpa = float(data.get("eligibility_cgpa", drive.eligibility_cgpa))
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

    # Verify this application belongs to one of the company's drives
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
