from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db, cache
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application

admin_bp = Blueprint("admin", __name__)


def admin_required(fn):
    """Decorator: ensures the user is an admin."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


# ──────────────────────────── Dashboard ────────────────────────────

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    stats = {
        "total_students": StudentProfile.query.count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count(),
        "pending_companies": CompanyProfile.query.filter_by(approval_status="pending").count(),
        "pending_drives": PlacementDrive.query.filter_by(status="pending").count(),
        "approved_drives": PlacementDrive.query.filter_by(status="approved").count(),
        "students_placed": Application.query.filter_by(status="selected").count(),
    }
    return jsonify(stats), 200


# ──────────────────────────── Company Management ────────────────────────────

@admin_bp.route("/companies", methods=["GET"])
@admin_required
def get_companies():
    status_filter = request.args.get("status")  # pending / approved / rejected
    search = request.args.get("search", "").strip()

    query = CompanyProfile.query

    if status_filter:
        query = query.filter_by(approval_status=status_filter)

    if search:
        query = query.filter(CompanyProfile.company_name.ilike(f"%{search}%"))

    companies = query.all()

    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "company_name": c.company_name,
            "hr_contact": c.hr_contact,
            "website": c.website,
            "description": c.description,
            "approval_status": c.approval_status,
            "is_blacklisted": c.is_blacklisted,
            "email": c.user.email,
            "total_drives": len(c.drives),
        })

    return jsonify(result), 200


@admin_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
@admin_required
def approve_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"{company.company_name} approved"}), 200


@admin_bp.route("/companies/<int:company_id>/reject", methods=["PUT"])
@admin_required
def reject_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"{company.company_name} rejected"}), 200


@admin_bp.route("/companies/<int:company_id>/blacklist", methods=["PUT"])
@admin_required
def toggle_blacklist_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    cache.clear()
    status = "blacklisted" if company.is_blacklisted else "unblacklisted"
    return jsonify({"message": f"{company.company_name} {status}"}), 200


# ──────────────────────────── Drive Management ────────────────────────────

@admin_bp.route("/drives", methods=["GET"])
@admin_required
def get_drives():
    status_filter = request.args.get("status")
    search = request.args.get("search", "").strip()

    query = PlacementDrive.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(PlacementDrive.job_title.ilike(f"%{search}%"))

    drives = query.order_by(PlacementDrive.created_at.desc()).all()

    result = []
    for d in drives:
        result.append({
            "id": d.id,
            "company_name": d.company.company_name,
            "company_id": d.company_id,
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


@admin_bp.route("/drives/<int:drive_id>/approve", methods=["PUT"])
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Drive '{drive.job_title}' approved"}), 200


@admin_bp.route("/drives/<int:drive_id>/reject", methods=["PUT"])
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "rejected"
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Drive '{drive.job_title}' rejected"}), 200


@admin_bp.route("/drives/<int:drive_id>/close", methods=["PUT"])
@admin_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "closed"
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Drive '{drive.job_title}' closed"}), 200


# ──────────────────────────── Student Management ────────────────────────────

@admin_bp.route("/students", methods=["GET"])
@admin_required
def get_students():
    search = request.args.get("search", "").strip()

    query = StudentProfile.query

    if search:
        query = query.filter(
            db.or_(
                StudentProfile.name.ilike(f"%{search}%"),
                StudentProfile.branch.ilike(f"%{search}%"),
            )
        )

    students = query.all()

    result = []
    for s in students:
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "name": s.name,
            "email": s.user.email,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "year": s.year,
            "phone": s.phone,
            "is_active": s.user.is_active,
            "total_applications": len(s.applications),
            "selected_count": sum(1 for a in s.applications if a.status == "selected"),
        })

    return jsonify(result), 200


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["PUT"])
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        return jsonify({"error": "Cannot deactivate admin"}), 400
    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    return jsonify({"message": f"User {status}"}), 200


# ──────────────────────────── All Applications ────────────────────────────

@admin_bp.route("/applications", methods=["GET"])
@admin_required
def get_all_applications():
    applications = Application.query.order_by(Application.applied_at.desc()).all()

    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "student_name": a.student.name,
            "student_branch": a.student.branch,
            "drive_title": a.drive.job_title,
            "company_name": a.drive.company.company_name,
            "status": a.status,
            "applied_at": a.applied_at.isoformat(),
        })

    return jsonify(result), 200
