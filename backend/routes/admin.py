from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from utils import role_required

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard Stats ───────────────────────────────────────────
@admin_bp.route("/dashboard", methods=["GET"])
@role_required("admin")
def dashboard():
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    pending_companies = CompanyProfile.query.filter_by(approval_status="pending").count()
    pending_drives = PlacementDrive.query.filter_by(status="pending").count()

    return jsonify({
        "total_students": total_students,
        "total_companies": total_companies,
        "total_drives": total_drives,
        "total_applications": total_applications,
        "pending_companies": pending_companies,
        "pending_drives": pending_drives
    }), 200


# ─── Company Management ───────────────────────────────────────
@admin_bp.route("/companies", methods=["GET"])
@role_required("admin")
def get_companies():
    status_filter = request.args.get("status")  # pending/approved/rejected
    search = request.args.get("search", "")

    query = CompanyProfile.query

    if status_filter:
        query = query.filter_by(approval_status=status_filter)

    if search:
        query = query.filter(CompanyProfile.company_name.ilike(f"%{search}%"))

    companies = query.all()

    return jsonify([{
        "id": c.id,
        "user_id": c.user_id,
        "company_name": c.company_name,
        "hr_contact": c.hr_contact,
        "website": c.website,
        "description": c.description,
        "approval_status": c.approval_status,
        "is_blacklisted": c.is_blacklisted,
        "email": c.user.email
    } for c in companies]), 200


@admin_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
@role_required("admin")
def approve_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    return jsonify({"message": f"{company.company_name} approved"}), 200


@admin_bp.route("/companies/<int:company_id>/reject", methods=["PUT"])
@role_required("admin")
def reject_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    return jsonify({"message": f"{company.company_name} rejected"}), 200


@admin_bp.route("/companies/<int:company_id>/blacklist", methods=["PUT"])
@role_required("admin")
def blacklist_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    status = "blacklisted" if company.is_blacklisted else "unblacklisted"
    return jsonify({"message": f"{company.company_name} {status}"}), 200


# ─── Drive Management ─────────────────────────────────────────
@admin_bp.route("/drives", methods=["GET"])
@role_required("admin")
def get_drives():
    status_filter = request.args.get("status")
    search = request.args.get("search", "")

    query = PlacementDrive.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(PlacementDrive.job_title.ilike(f"%{search}%"))

    drives = query.all()

    return jsonify([{
        "id": d.id,
        "company_name": d.company.company_name,
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


@admin_bp.route("/drives/<int:drive_id>/approve", methods=["PUT"])
@role_required("admin")
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    return jsonify({"message": f"Drive '{drive.job_title}' approved"}), 200


@admin_bp.route("/drives/<int:drive_id>/reject", methods=["PUT"])
@role_required("admin")
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "rejected"
    db.session.commit()
    return jsonify({"message": f"Drive '{drive.job_title}' rejected"}), 200


# ─── Student Management ───────────────────────────────────────
@admin_bp.route("/students", methods=["GET"])
@role_required("admin")
def get_students():
    search = request.args.get("search", "")

    query = StudentProfile.query

    if search:
        query = query.filter(
            db.or_(
                StudentProfile.name.ilike(f"%{search}%"),
                StudentProfile.branch.ilike(f"%{search}%")
            )
        )

    students = query.all()

    return jsonify([{
        "id": s.id,
        "user_id": s.user_id,
        "name": s.name,
        "branch": s.branch,
        "cgpa": s.cgpa,
        "year": s.year,
        "phone": s.phone,
        "email": s.user.email,
        "is_active": s.user.is_active,
        "application_count": len(s.applications)
    } for s in students]), 200


@admin_bp.route("/students/<int:user_id>/deactivate", methods=["PUT"])
@role_required("admin")
def deactivate_student(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != "student":
        return jsonify({"error": "User is not a student"}), 400
    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    return jsonify({"message": f"Student {status}"}), 200


# ─── All Applications ─────────────────────────────────────────
@admin_bp.route("/applications", methods=["GET"])
@role_required("admin")
def get_all_applications():
    applications = Application.query.all()

    return jsonify([{
        "id": a.id,
        "student_name": a.student.name,
        "student_branch": a.student.branch,
        "drive_title": a.drive.job_title,
        "company_name": a.drive.company.company_name,
        "status": a.status,
        "applied_at": a.applied_at.isoformat()
    } for a in applications]), 200
