from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, StudentProfile, PlacementDrive, Application, CompanyProfile
from utils import role_required
from datetime import datetime

student_bp = Blueprint("student", __name__)


# ─── Student Dashboard ─────────────────────────────────────────
@student_bp.route("/dashboard", methods=["GET"])
@role_required("student")
def dashboard():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()

    total_applications = Application.query.filter_by(student_id=student.id).count()
    selected_count = Application.query.filter_by(student_id=student.id, status="selected").count()
    pending_count = Application.query.filter_by(student_id=student.id, status="applied").count()

    return jsonify({
        "student": {
            "id": student.id,
            "name": student.name,
            "branch": student.branch,
            "cgpa": student.cgpa,
            "year": student.year,
            "phone": student.phone,
            "resume_url": student.resume_url,
            "email": student.user.email
        },
        "total_applications": total_applications,
        "selected_count": selected_count,
        "pending_count": pending_count
    }), 200


# ─── Update Profile ────────────────────────────────────────────
@student_bp.route("/profile", methods=["PUT"])
@role_required("student")
def update_profile():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
    data = request.get_json()

    student.name = data.get("name", student.name)
    student.branch = data.get("branch", student.branch)
    student.cgpa = float(data.get("cgpa", student.cgpa))
    student.year = int(data.get("year", student.year))
    student.phone = data.get("phone", student.phone)
    student.resume_url = data.get("resume_url", student.resume_url)

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ─── Browse Approved Drives ────────────────────────────────────
@student_bp.route("/drives", methods=["GET"])
@role_required("student")
def get_drives():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()

    search = request.args.get("search", "")
    branch_filter = request.args.get("branch", "")

    # Only show approved drives that haven't passed their deadline
    query = PlacementDrive.query.filter_by(status="approved").filter(
        PlacementDrive.deadline >= datetime.utcnow()
    )

    if search:
        query = query.filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.job_description.ilike(f"%{search}%")
            )
        )

    if branch_filter:
        query = query.filter(PlacementDrive.eligibility_branch.ilike(f"%{branch_filter}%"))

    drives = query.all()

    result = []
    for d in drives:
        # Check if student already applied
        existing_app = Application.query.filter_by(
            student_id=student.id, drive_id=d.id
        ).first()

        # Check eligibility
        eligible = True
        if d.eligibility_cgpa and student.cgpa < d.eligibility_cgpa:
            eligible = False
        if d.eligibility_branch:
            allowed_branches = [b.strip().upper() for b in d.eligibility_branch.split(",")]
            if student.branch.upper() not in allowed_branches:
                eligible = False
        if d.eligibility_year and student.year != d.eligibility_year:
            eligible = False

        result.append({
            "id": d.id,
            "company_name": d.company.company_name,
            "job_title": d.job_title,
            "job_description": d.job_description,
            "package": d.package,
            "eligibility_cgpa": d.eligibility_cgpa,
            "eligibility_branch": d.eligibility_branch,
            "eligibility_year": d.eligibility_year,
            "deadline": d.deadline.isoformat(),
            "already_applied": existing_app is not None,
            "application_status": existing_app.status if existing_app else None,
            "eligible": eligible
        })

    return jsonify(result), 200


# ─── Apply to Drive ────────────────────────────────────────────
@student_bp.route("/drives/<int:drive_id>/apply", methods=["POST"])
@role_required("student")
def apply_to_drive(drive_id):
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()
    drive = PlacementDrive.query.get_or_404(drive_id)

    # Validations
    if drive.status != "approved":
        return jsonify({"error": "This drive is not open for applications"}), 400

    if drive.deadline < datetime.utcnow():
        return jsonify({"error": "Application deadline has passed"}), 400

    # Check eligibility
    if drive.eligibility_cgpa and student.cgpa < drive.eligibility_cgpa:
        return jsonify({"error": f"Minimum CGPA required: {drive.eligibility_cgpa}"}), 400

    if drive.eligibility_branch:
        allowed = [b.strip().upper() for b in drive.eligibility_branch.split(",")]
        if student.branch.upper() not in allowed:
            return jsonify({"error": f"Your branch is not eligible. Allowed: {drive.eligibility_branch}"}), 400

    if drive.eligibility_year and student.year != drive.eligibility_year:
        return jsonify({"error": f"This drive is for {drive.eligibility_year} batch only"}), 400

    # Check duplicate application
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing:
        return jsonify({"error": "You have already applied to this drive"}), 409

    application = Application(student_id=student.id, drive_id=drive_id)
    db.session.add(application)
    db.session.commit()

    return jsonify({"message": "Application submitted", "application_id": application.id}), 201


# ─── My Applications ──────────────────────────────────────────
@student_bp.route("/applications", methods=["GET"])
@role_required("student")
def get_applications():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()

    applications = Application.query.filter_by(student_id=student.id).order_by(
        Application.applied_at.desc()
    ).all()

    return jsonify([{
        "id": a.id,
        "drive_id": a.drive_id,
        "job_title": a.drive.job_title,
        "company_name": a.drive.company.company_name,
        "package": a.drive.package,
        "status": a.status,
        "applied_at": a.applied_at.isoformat(),
        "updated_at": a.updated_at.isoformat() if a.updated_at else None
    } for a in applications]), 200


# ─── Placement History (past drives) ──────────────────────────
@student_bp.route("/history", methods=["GET"])
@role_required("student")
def placement_history():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first_or_404()

    # History = applications to drives that are closed or past deadline
    applications = Application.query.filter_by(student_id=student.id).all()

    history = []
    for a in applications:
        if a.drive.status == "closed" or a.drive.deadline < datetime.utcnow():
            history.append({
                "id": a.id,
                "job_title": a.drive.job_title,
                "company_name": a.drive.company.company_name,
                "package": a.drive.package,
                "status": a.status,
                "applied_at": a.applied_at.isoformat(),
                "drive_deadline": a.drive.deadline.isoformat()
            })

    return jsonify(history), 200
