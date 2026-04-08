from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db, cache
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint("admin", __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    return jsonify({
        "total_students": StudentProfile.query.count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count(),
        "pending_companies": CompanyProfile.query.filter_by(approval_status="pending").count(),
        "pending_drives": PlacementDrive.query.filter_by(status="pending").count(),
        "students_placed": Application.query.filter_by(status="selected").count(),
    }), 200

# ── Companies ──
@admin_bp.route("/companies", methods=["GET"])
@admin_required
def get_companies():
    q = CompanyProfile.query
    s = request.args.get("status")
    search = request.args.get("search","").strip()
    if s: q = q.filter_by(approval_status=s)
    if search: q = q.filter(CompanyProfile.company_name.ilike(f"%{search}%"))
    return jsonify([{
        "id": c.id, "user_id": c.user_id, "company_name": c.company_name,
        "hr_contact": c.hr_contact, "website": c.website, "description": c.description,
        "approval_status": c.approval_status, "is_blacklisted": c.is_blacklisted,
        "is_active": c.user.is_active, "email": c.user.email, "total_drives": len(c.drives)
    } for c in q.all()]), 200

@admin_bp.route("/companies/<int:cid>/approve", methods=["PUT"])
@admin_required
def approve_company(cid):
    c = CompanyProfile.query.get_or_404(cid)
    c.approval_status = "approved"; db.session.commit(); cache.clear()
    return jsonify({"message": f"{c.company_name} approved"}), 200

@admin_bp.route("/companies/<int:cid>/reject", methods=["PUT"])
@admin_required
def reject_company(cid):
    c = CompanyProfile.query.get_or_404(cid)
    c.approval_status = "rejected"; db.session.commit(); cache.clear()
    return jsonify({"message": f"{c.company_name} rejected"}), 200

@admin_bp.route("/companies/<int:cid>/blacklist", methods=["PUT"])
@admin_required
def toggle_blacklist(cid):
    c = CompanyProfile.query.get_or_404(cid)
    c.is_blacklisted = not c.is_blacklisted; db.session.commit(); cache.clear()
    return jsonify({"message": f"{c.company_name} {'blacklisted' if c.is_blacklisted else 'unblacklisted'}"}), 200

# ── Drives ──
@admin_bp.route("/drives", methods=["GET"])
@admin_required
def get_drives():
    q = PlacementDrive.query
    s = request.args.get("status")
    search = request.args.get("search","").strip()
    if s: q = q.filter_by(status=s)
    if search: q = q.filter(PlacementDrive.job_title.ilike(f"%{search}%"))
    return jsonify([{
        "id": d.id, "company_name": d.company.company_name, "job_title": d.job_title,
        "job_description": d.job_description, "package": d.package,
        "eligibility_cgpa": d.eligibility_cgpa, "eligibility_branch": d.eligibility_branch,
        "eligibility_year": d.eligibility_year,
        "deadline": d.deadline.isoformat() if d.deadline else None,
        "status": d.status, "total_applications": len(d.applications),
        "created_at": d.created_at.isoformat()
    } for d in q.order_by(PlacementDrive.created_at.desc()).all()]), 200

@admin_bp.route("/drives/<int:did>/approve", methods=["PUT"])
@admin_required
def approve_drive(did):
    d = PlacementDrive.query.get_or_404(did)
    d.status = "approved"; db.session.commit(); cache.clear()
    return jsonify({"message": f"'{d.job_title}' approved"}), 200

@admin_bp.route("/drives/<int:did>/reject", methods=["PUT"])
@admin_required
def reject_drive(did):
    d = PlacementDrive.query.get_or_404(did)
    d.status = "rejected"; db.session.commit(); cache.clear()
    return jsonify({"message": f"'{d.job_title}' rejected"}), 200

@admin_bp.route("/drives/<int:did>/close", methods=["PUT"])
@admin_required
def close_drive(did):
    d = PlacementDrive.query.get_or_404(did)
    d.status = "closed"; db.session.commit(); cache.clear()
    return jsonify({"message": f"'{d.job_title}' closed"}), 200

# ── Students ──
@admin_bp.route("/students", methods=["GET"])
@admin_required
def get_students():
    q = StudentProfile.query
    search = request.args.get("search","").strip()
    if search: q = q.filter(db.or_(StudentProfile.name.ilike(f"%{search}%"), StudentProfile.branch.ilike(f"%{search}%")))
    return jsonify([{
        "id": s.id, "user_id": s.user_id, "name": s.name, "email": s.user.email,
        "branch": s.branch, "cgpa": s.cgpa, "year": s.year, "phone": s.phone,
        "is_active": s.user.is_active, "total_applications": len(s.applications),
        "selected_count": sum(1 for a in s.applications if a.status == "selected")
    } for s in q.all()]), 200

@admin_bp.route("/users/<int:uid>/toggle-active", methods=["PUT"])
@admin_required
def toggle_active(uid):
    u = User.query.get_or_404(uid)
    if u.role == "admin": return jsonify({"error": "Cannot deactivate admin"}), 400
    u.is_active = not u.is_active; db.session.commit()
    return jsonify({"message": f"User {'activated' if u.is_active else 'deactivated'}"}), 200

# ── Applications ──
@admin_bp.route("/applications", methods=["GET"])
@admin_required
def get_applications():
    return jsonify([{
        "id": a.id, "student_name": a.student.name, "student_branch": a.student.branch,
        "drive_title": a.drive.job_title, "company_name": a.drive.company.company_name,
        "status": a.status, "applied_at": a.applied_at.isoformat()
    } for a in Application.query.order_by(Application.applied_at.desc()).all()]), 200

# ── Reports & Stats ──
@admin_bp.route("/stats", methods=["GET"])
@admin_required
@cache.cached(timeout=120)
def get_stats():
    from sqlalchemy import func
    status_counts = db.session.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()

    top_companies = db.session.query(
        CompanyProfile.company_name, func.count(Application.id)
    ).join(PlacementDrive, PlacementDrive.company_id == CompanyProfile.id
    ).join(Application, Application.drive_id == PlacementDrive.id
    ).filter(Application.status == "selected"
    ).group_by(CompanyProfile.company_name
    ).order_by(func.count(Application.id).desc()).limit(10).all()

    branch_stats = db.session.query(
        StudentProfile.branch, func.count(Application.id)
    ).join(Application, Application.student_id == StudentProfile.id
    ).group_by(StudentProfile.branch).all()

    drives_monthly = db.session.query(
        func.strftime('%Y-%m', PlacementDrive.created_at), func.count(PlacementDrive.id)
    ).group_by(func.strftime('%Y-%m', PlacementDrive.created_at)
    ).order_by(func.strftime('%Y-%m', PlacementDrive.created_at)).all()

    return jsonify({
        "status_counts": {s: c for s, c in status_counts},
        "top_companies": [{"company": n, "selections": c} for n, c in top_companies],
        "branch_stats": {b: c for b, c in branch_stats},
        "drives_monthly": [{"month": m, "count": c} for m, c in drives_monthly],
    }), 200
