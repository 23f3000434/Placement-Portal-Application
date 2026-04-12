from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, StudentProfile, PlacementDrive, Application, CompanyProfile
from datetime import datetime, timezone
from functools import wraps


def _now_utc_naive():
    """Match naive UTC deadlines stored in the DB (company create / seed)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os

student_bp = Blueprint("student", __name__)
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def student_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "student":
            return jsonify({"error": "Student access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def _profile():
    u = User.query.get(int(get_jwt_identity()))
    return u.student_profile if u else None


def _ineligibility_reason(p, drive):
    """None if student may apply; else human-readable reason (same rules as apply())."""
    if drive.eligibility_cgpa and p.cgpa < drive.eligibility_cgpa:
        return f"Requires minimum CGPA {drive.eligibility_cgpa} (yours: {p.cgpa})"
    if drive.eligibility_branch:
        allowed = [b.strip().upper() for b in drive.eligibility_branch.split(",")]
        if p.branch.upper() not in allowed:
            return f"Open to: {drive.eligibility_branch}. Your branch: {p.branch}"
    if drive.eligibility_year and p.year != drive.eligibility_year:
        return f"For batch year {drive.eligibility_year} only (yours: {p.year})"
    return None


@student_bp.route("/dashboard", methods=["GET"])
@student_required
def dashboard():
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    apps = Application.query.filter_by(student_id=p.id).all()
    return jsonify({
        "name": p.name, "branch": p.branch, "cgpa": p.cgpa, "year": p.year,
        "total_applications": len(apps),
        "selected": sum(1 for a in apps if a.status == "selected"),
        "shortlisted": sum(1 for a in apps if a.status == "shortlisted"),
        "pending": sum(1 for a in apps if a.status == "applied"),
        "rejected": sum(1 for a in apps if a.status == "rejected"),
    }), 200

@student_bp.route("/profile", methods=["GET"])
@student_required
def get_profile():
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    return jsonify({"id": p.id, "name": p.name, "email": p.user.email,
        "branch": p.branch, "cgpa": p.cgpa, "year": p.year,
        "phone": p.phone, "resume_url": p.resume_url}), 200

@student_bp.route("/profile", methods=["PUT"])
@student_required
def update_profile():
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    d = request.get_json() or {}
    if d.get("name","").strip(): p.name = d["name"].strip()
    if d.get("branch","").strip(): p.branch = d["branch"].strip().upper()
    if d.get("cgpa") is not None:
        cgpa = float(d["cgpa"])
        if 0 <= cgpa <= 10: p.cgpa = cgpa
    if d.get("year") is not None: p.year = int(d["year"])
    p.phone = d.get("phone", p.phone)
    p.resume_url = d.get("resume_url", p.resume_url)
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200

@student_bp.route("/resume-upload", methods=["POST"])
@student_required
def upload_resume():
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    if "resume" not in request.files: return jsonify({"error": "No file uploaded"}), 400
    file = request.files["resume"]
    if file.filename == "": return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename): return jsonify({"error": "Only PDF, DOC, DOCX allowed"}), 400
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"resume_{p.user_id}_{p.id}.{ext}")
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "resumes")
    file.save(os.path.join(upload_dir, filename))
    p.resume_url = f"/uploads/resumes/{filename}"
    db.session.commit()
    return jsonify({"message": "Resume uploaded", "resume_url": p.resume_url}), 200

@student_bp.route("/drives", methods=["GET"])
@student_required
def get_drives():
    """Approved drives still accepting applications. Each row includes eligible + reason if not. Not cached."""
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    now = _now_utc_naive()
    q = PlacementDrive.query.filter_by(status="approved").filter(PlacementDrive.deadline > now)
    search = request.args.get("search", "").strip()
    branch = request.args.get("branch", "").strip()
    if search:
        q = q.join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.id).filter(
            db.or_(PlacementDrive.job_title.ilike(f"%{search}%"),
                   PlacementDrive.job_description.ilike(f"%{search}%"),
                   CompanyProfile.company_name.ilike(f"%{search}%")))
    if branch:
        q = q.filter(PlacementDrive.eligibility_branch.ilike(f"%{branch}%"))
    applied_ids = {a.drive_id for a in Application.query.filter_by(student_id=p.id).all()}
    rows = q.order_by(PlacementDrive.deadline.asc()).all()
    out = []
    for d in rows:
        reason = _ineligibility_reason(p, d)
        out.append({
            "id": d.id, "company_name": d.company.company_name, "job_title": d.job_title,
            "job_description": d.job_description, "package": d.package,
            "eligibility_cgpa": d.eligibility_cgpa, "eligibility_branch": d.eligibility_branch,
            "eligibility_year": d.eligibility_year,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "already_applied": d.id in applied_ids,
            "eligible": reason is None,
            "ineligibility_reason": reason,
        })
    return jsonify(out), 200


@student_bp.route("/companies", methods=["GET"])
@student_required
def list_companies():
    """Browse approved, active companies (for company search). Blacklisted excluded."""
    search = request.args.get("search", "").strip()
    q = CompanyProfile.query.filter_by(approval_status="approved", is_blacklisted=False).join(
        User, CompanyProfile.user_id == User.id).filter(User.is_active.is_(True))
    if search:
        q = q.filter(CompanyProfile.company_name.ilike(f"%{search}%"))
    items = q.order_by(CompanyProfile.company_name.asc()).all()
    return jsonify([{
        "id": c.id, "company_name": c.company_name, "hr_contact": c.hr_contact or "",
        "website": c.website or "", "description": (c.description or "")[:280],
        "open_drives": sum(
            1 for d in c.drives
            if d.status == "approved" and d.deadline > _now_utc_naive()
        ),
    } for c in items]), 200

@student_bp.route("/drives/<int:did>/apply", methods=["POST"])
@student_required
def apply(did):
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    drive = PlacementDrive.query.get_or_404(did)
    if drive.status != "approved": return jsonify({"error": "Drive not accepting applications"}), 400
    if drive.deadline and drive.deadline < _now_utc_naive(): return jsonify({"error": "Deadline passed"}), 400
    if drive.eligibility_cgpa and p.cgpa < drive.eligibility_cgpa:
        return jsonify({"error": f"Min CGPA: {drive.eligibility_cgpa}, yours: {p.cgpa}"}), 400
    if drive.eligibility_branch:
        allowed = [b.strip().upper() for b in drive.eligibility_branch.split(",")]
        if p.branch.upper() not in allowed: return jsonify({"error": f"Branch {p.branch} not eligible"}), 400
    if drive.eligibility_year and p.year != drive.eligibility_year:
        return jsonify({"error": f"For {drive.eligibility_year} batch only"}), 400
    if Application.query.filter_by(student_id=p.id, drive_id=did).first():
        return jsonify({"error": "Already applied"}), 409
    db.session.add(Application(student_id=p.id, drive_id=did))
    db.session.commit(); cache.clear()
    return jsonify({"message": "Applied successfully"}), 201

@student_bp.route("/applications", methods=["GET"])
@student_required
def my_applications():
    p = _profile()
    if not p:
        return jsonify({"error": "Student profile not found"}), 404
    apps = (
        Application.query.options(
            joinedload(Application.drive).joinedload(PlacementDrive.company)
        )
        .filter_by(student_id=p.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    out = []
    for a in apps:
        if a.drive is None:
            continue
        co = a.drive.company
        if co is None:
            continue
        out.append({
            "id": a.id, "drive_id": a.drive_id, "job_title": a.drive.job_title,
            "company_name": co.company_name, "package": a.drive.package,
            "status": a.status, "applied_at": a.applied_at.isoformat(),
            "deadline": a.drive.deadline.isoformat() if a.drive.deadline else None,
            "interview_date": a.interview_date.isoformat() if a.interview_date else None,
            "interview_link": a.interview_link, "interview_notes": a.interview_notes,
        })
    return jsonify(out), 200

def _export_csv_sync(p):
    import csv, io
    apps = Application.query.filter_by(student_id=p.id).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date", "Updated Date"])
    for a in apps:
        w.writerow([
            p.id, a.drive.company.company_name, a.drive.job_title, a.status,
            a.applied_at.strftime("%Y-%m-%d %H:%M"),
            a.updated_at.strftime("%Y-%m-%d %H:%M") if a.updated_at else ""
        ])
    return out.getvalue()


@student_bp.route("/export", methods=["POST"])
@student_required
def export_csv():
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    try:
        from tasks import export_student_applications
        task = export_student_applications.delay(p.id, p.user.email)
        return jsonify({
            "message": "Export started. You will get an email when the file is ready, or wait here for download.",
            "task_id": task.id,
        }), 202
    except Exception:
        data = _export_csv_sync(p)
        return jsonify({"message": "Export complete (sync).", "csv_data": data}), 200


@student_bp.route("/export/status/<task_id>", methods=["GET"])
@student_required
def export_status(task_id):
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    from celery.result import AsyncResult
    from tasks import celery_app
    ar = AsyncResult(task_id, app=celery_app)
    if ar.state == "PENDING":
        return jsonify({"state": "PENDING"}), 200
    if ar.state == "FAILURE":
        return jsonify({"state": "FAILURE", "error": "Export failed"}), 200
    if ar.state == "SUCCESS":
        result = ar.result or {}
        if not isinstance(result, dict):
            return jsonify({"state": "FAILURE", "error": "Invalid result"}), 200
        if result.get("error"):
            return jsonify({"state": "FAILURE", "error": result["error"]}), 200
        if result.get("student_id") != p.id:
            return jsonify({"error": "Forbidden"}), 403
        return jsonify({
            "state": "SUCCESS",
            "file": result.get("file"),
            "download_url": f"/api/student/export/download/{result['file']}" if result.get("file") else None,
        }), 200
    return jsonify({"state": ar.state}), 200


@student_bp.route("/export/download/<path:filename>", methods=["GET"])
@student_required
def export_download(filename):
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    safe = secure_filename(filename)
    if not safe or safe != filename:
        return jsonify({"error": "Invalid filename"}), 400
    prefix = f"export_{p.id}_"
    if not safe.startswith(prefix) or not safe.endswith(".csv"):
        return jsonify({"error": "Forbidden"}), 403
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = os.path.join(backend_root, "exports")
    filepath = os.path.join(export_dir, safe)
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True, download_name=safe, mimetype="text/csv")
