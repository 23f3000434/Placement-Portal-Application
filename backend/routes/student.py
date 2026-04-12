from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, StudentProfile, PlacementDrive, Application, CompanyProfile
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
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
@cache.cached(timeout=60, query_string=True)
def get_drives():
    q = PlacementDrive.query.filter_by(status="approved").filter(PlacementDrive.deadline > datetime.utcnow())
    search = request.args.get("search","").strip()
    branch = request.args.get("branch","").strip()
    if search:
        q = q.join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.id).filter(
            db.or_(PlacementDrive.job_title.ilike(f"%{search}%"),
                   PlacementDrive.job_description.ilike(f"%{search}%"),
                   CompanyProfile.company_name.ilike(f"%{search}%")))
    if branch:
        q = q.filter(PlacementDrive.eligibility_branch.ilike(f"%{branch}%"))
    p = _profile()
    applied_ids = {a.drive_id for a in Application.query.filter_by(student_id=p.id).all()} if p else set()
    return jsonify([{
        "id": d.id, "company_name": d.company.company_name, "job_title": d.job_title,
        "job_description": d.job_description, "package": d.package,
        "eligibility_cgpa": d.eligibility_cgpa, "eligibility_branch": d.eligibility_branch,
        "eligibility_year": d.eligibility_year,
        "deadline": d.deadline.isoformat() if d.deadline else None,
        "already_applied": d.id in applied_ids
    } for d in q.order_by(PlacementDrive.deadline.asc()).all()]), 200

@student_bp.route("/drives/<int:did>/apply", methods=["POST"])
@student_required
def apply(did):
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    drive = PlacementDrive.query.get_or_404(did)
    if drive.status != "approved": return jsonify({"error": "Drive not accepting applications"}), 400
    if drive.deadline and drive.deadline < datetime.utcnow(): return jsonify({"error": "Deadline passed"}), 400
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
    if not p: return jsonify({"error": "Not found"}), 404
    return jsonify([{
        "id": a.id, "drive_id": a.drive_id, "job_title": a.drive.job_title,
        "company_name": a.drive.company.company_name, "package": a.drive.package,
        "status": a.status, "applied_at": a.applied_at.isoformat(),
        "deadline": a.drive.deadline.isoformat() if a.drive.deadline else None,
        "interview_date": a.interview_date.isoformat() if a.interview_date else None,
        "interview_link": a.interview_link, "interview_notes": a.interview_notes,
    } for a in Application.query.filter_by(student_id=p.id).order_by(Application.applied_at.desc()).all()]), 200

@student_bp.route("/export", methods=["POST"])
@student_required
def export_csv():
    p = _profile()
    if not p: return jsonify({"error": "Not found"}), 404
    try:
        from tasks import export_student_applications
        task = export_student_applications.delay(p.id, p.user.email)
        return jsonify({"message": "Export started! You'll get an email when ready.", "task_id": task.id}), 202
    except Exception:
        import csv, io
        apps = Application.query.filter_by(student_id=p.id).all()
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Student ID","Company Name","Drive Title","Status","Applied Date"])
        for a in apps:
            w.writerow([p.id, a.drive.company.company_name, a.drive.job_title, a.status, a.applied_at.isoformat()])
        return jsonify({"message": "Export complete!", "csv_data": out.getvalue()}), 200
