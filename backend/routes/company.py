from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import User, CompanyProfile, PlacementDrive, Application
from utils import role_required
from datetime import datetime

company_bp = Blueprint("company", __name__)


# ─── Company Dashboard ─────────────────────────────────────────
@company_bp.route("/dashboard", methods=["GET"])
@role_required("company")
def dashboard():
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    total_applicants = sum(len(d.applications) for d in drives)

    return jsonify({
        "company": {
            "id": company.id,
            "company_name": company.company_name,
            "hr_contact": company.hr_contact,
            "website": company.website,
            "description": company.description,
            "approval_status": company.approval_status,
            "is_blacklisted": company.is_blacklisted
        },
        "total_drives": len(drives),
        "total_applicants": total_applicants
    }), 200


# ─── Update Company Profile ────────────────────────────────────
@company_bp.route("/profile", methods=["PUT"])
@role_required("company")
def update_profile():
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    data = request.get_json()

    company.company_name = data.get("company_name", company.company_name)
    company.hr_contact = data.get("hr_contact", company.hr_contact)
    company.website = data.get("website", company.website)
    company.description = data.get("description", company.description)

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ─── Placement Drives CRUD ─────────────────────────────────────
@company_bp.route("/drives", methods=["GET"])
@role_required("company")
def get_drives():
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    return jsonify([{
        "id": d.id,
        "job_title": d.job_title,
        "job_description": d.job_description,
        "package": d.package,
        "eligibility_cgpa": d.eligibility_cgpa,
        "eligibility_branch": d.eligibility_branch,
        "eligibility_year": d.eligibility_year,
        "deadline": d.deadline.isoformat() if d.deadline else None,
        "status": d.status,
        "application_count": len(d.applications),
        "created_at": d.created_at.isoformat()
    } for d in drives]), 200


@company_bp.route("/drives", methods=["POST"])
@role_required("company")
def create_drive():
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()

    # Only approved companies can create drives
    if company.approval_status != "approved":
        return jsonify({"error": "Company must be approved by admin before creating drives"}), 403

    if company.is_blacklisted:
        return jsonify({"error": "Company is blacklisted"}), 403

    data = request.get_json()
    job_title = data.get("job_title")
    job_description = data.get("job_description")
    deadline = data.get("deadline")

    if not all([job_title, job_description, deadline]):
        return jsonify({"error": "job_title, job_description, and deadline are required"}), 400

    try:
        deadline_dt = datetime.fromisoformat(deadline)
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use ISO format: YYYY-MM-DDTHH:MM:SS"}), 400

    drive = PlacementDrive(
        company_id=company.id,
        job_title=job_title,
        job_description=job_description,
        package=data.get("package"),
        eligibility_cgpa=float(data.get("eligibility_cgpa", 0)),
        eligibility_branch=data.get("eligibility_branch"),
        eligibility_year=int(data.get("eligibility_year")) if data.get("eligibility_year") else None,
        deadline=deadline_dt
    )

    db.session.add(drive)
    db.session.commit()

    return jsonify({"message": "Drive created, pending admin approval", "drive_id": drive.id}), 201


@company_bp.route("/drives/<int:drive_id>", methods=["PUT"])
@role_required("company")
def update_drive(drive_id):
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    drive = PlacementDrive.query.get_or_404(drive_id)

    # Make sure this drive belongs to this company
    if drive.company_id != company.id:
        return jsonify({"error": "Not your drive"}), 403

    data = request.get_json()
    drive.job_title = data.get("job_title", drive.job_title)
    drive.job_description = data.get("job_description", drive.job_description)
    drive.package = data.get("package", drive.package)
    drive.eligibility_cgpa = float(data.get("eligibility_cgpa", drive.eligibility_cgpa))
    drive.eligibility_branch = data.get("eligibility_branch", drive.eligibility_branch)

    if data.get("eligibility_year"):
        drive.eligibility_year = int(data["eligibility_year"])

    if data.get("deadline"):
        try:
            drive.deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"error": "Invalid deadline format"}), 400

    db.session.commit()
    return jsonify({"message": "Drive updated"}), 200


@company_bp.route("/drives/<int:drive_id>/close", methods=["PUT"])
@role_required("company")
def close_drive(drive_id):
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        return jsonify({"error": "Not your drive"}), 403

    drive.status = "closed"
    db.session.commit()
    return jsonify({"message": "Drive closed"}), 200


# ─── Application Management ────────────────────────────────────
@company_bp.route("/drives/<int:drive_id>/applications", methods=["GET"])
@role_required("company")
def get_applications(drive_id):
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        return jsonify({"error": "Not your drive"}), 403

    applications = Application.query.filter_by(drive_id=drive_id).all()

    return jsonify([{
        "id": a.id,
        "student_id": a.student_id,
        "student_name": a.student.name,
        "student_branch": a.student.branch,
        "student_cgpa": a.student.cgpa,
        "student_email": a.student.user.email,
        "status": a.status,
        "applied_at": a.applied_at.isoformat()
    } for a in applications]), 200


@company_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
@role_required("company")
def update_application_status(app_id):
    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first_or_404()

    application = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.get(application.drive_id)

    # Verify this application belongs to a drive owned by this company
    if drive.company_id != company.id:
        return jsonify({"error": "Not your application to manage"}), 403

    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ("shortlisted", "selected", "rejected"):
        return jsonify({"error": "Status must be shortlisted, selected, or rejected"}), 400

    application.status = new_status
    db.session.commit()

    return jsonify({"message": f"Application status updated to {new_status}"}), 200
