from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import User, CompanyProfile, PlacementDrive, Application
from datetime import datetime, timezone
from functools import wraps
import re

company_bp = Blueprint("company", __name__)


def _as_text(val):
    if val is None:
        return ""
    return str(val).strip()


def _parse_deadline(dl: str):
    """Accept datetime-local, ISO 8601, and JS Date.toISOString() (Z). Store naive UTC."""
    s = _as_text(dl)
    if not s:
        raise ValueError("empty deadline")
    s = s.replace("Z", "+00:00")
    if " " in s and "T" not in s:
        s = s.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        s2 = re.sub(r"\.\d+(?=[+-]|$)", "", s)
        try:
            dt = datetime.fromisoformat(s2)
        except ValueError as ex:
            raise ValueError("unparseable deadline") from ex
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _opt_eligibility_year(val):
    if val is None:
        return None
    if isinstance(val, str) and not val.strip():
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        raise ValueError("Invalid eligibility year")


def company_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "company":
            return jsonify({"error": "Company access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def _profile():
    u = User.query.get(int(get_jwt_identity()))
    return u.company_profile if u else None


@company_bp.route("/dashboard", methods=["GET"])
@company_required
def dashboard():
    p = _profile()
    if not p:
        return jsonify({"error": "Profile not found"}), 404
    drives = PlacementDrive.query.filter_by(company_id=p.id).all()
    return jsonify({
        "company_name": p.company_name, "hr_contact": p.hr_contact,
        "website": p.website, "description": p.description,
        "approval_status": p.approval_status, "is_blacklisted": p.is_blacklisted,
        "total_drives": len(drives),
        "total_applicants": sum(len(d.applications) for d in drives),
        "drives": [{
            "id": d.id, "job_title": d.job_title, "status": d.status,
            "total_applications": len(d.applications)
        } for d in drives]
    }), 200


@company_bp.route("/profile", methods=["GET"])
@company_required
def get_profile():
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": p.id, "company_name": p.company_name, "hr_contact": p.hr_contact,
        "website": p.website, "description": p.description,
        "approval_status": p.approval_status, "email": p.user.email
    }), 200


@company_bp.route("/profile", methods=["PUT"])
@company_required
def update_profile():
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    d = request.get_json() or {}
    if d.get("company_name", "").strip():
        p.company_name = d["company_name"].strip()
    p.hr_contact = d.get("hr_contact", p.hr_contact)
    p.website = d.get("website", p.website)
    p.description = d.get("description", p.description)
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ── Drives ──
@company_bp.route("/drives", methods=["GET"])
@company_required
def get_drives():
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    return jsonify([{
        "id": d.id, "job_title": d.job_title, "job_description": d.job_description,
        "package": d.package, "eligibility_cgpa": d.eligibility_cgpa,
        "eligibility_branch": d.eligibility_branch, "eligibility_year": d.eligibility_year,
        "deadline": d.deadline.isoformat() if d.deadline else None,
        "status": d.status, "total_applications": len(d.applications),
        "created_at": d.created_at.isoformat()
    } for d in PlacementDrive.query.filter_by(company_id=p.id).order_by(PlacementDrive.created_at.desc()).all()]), 200


@company_bp.route("/drives", methods=["POST"])
@company_required
def create_drive():
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    if p.approval_status != "approved":
        return jsonify({"error": "Company must be approved first"}), 403
    if p.is_blacklisted:
        return jsonify({"error": "Company is blacklisted"}), 403
    d = request.get_json() or {}
    title = _as_text(d.get("job_title"))
    desc = _as_text(d.get("job_description"))
    dl = _as_text(d.get("deadline"))
    if not title or not desc or not dl:
        return jsonify({"error": "Title, description, and deadline required"}), 400
    try:
        deadline = _parse_deadline(dl)
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use the date picker or ISO date-time."}), 400

    try:
        elig_year = _opt_eligibility_year(d.get("eligibility_year"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        elig_cgpa = float(d.get("eligibility_cgpa", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid min CGPA"}), 400

    drive = PlacementDrive(
        company_id=p.id, job_title=title, job_description=desc,
        package=_as_text(d.get("package")),
        eligibility_cgpa=elig_cgpa,
        eligibility_branch=_as_text(d.get("eligibility_branch")).upper(),
        eligibility_year=elig_year,
        deadline=deadline
    )
    db.session.add(drive)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Drive created (pending approval)", "drive_id": drive.id}), 201


# ── Applications for a drive ──
@company_bp.route("/drives/<int:did>/applications", methods=["GET"])
@company_required
def get_applications(did):
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != p.id:
        return jsonify({"error": "Not your drive"}), 403
    return jsonify([{
        "id": a.id, "student_id": a.student_id, "student_name": a.student.name,
        "student_email": a.student.user.email, "student_branch": a.student.branch,
        "student_cgpa": a.student.cgpa, "student_year": a.student.year,
        "student_phone": a.student.phone, "resume_url": a.student.resume_url,
        "status": a.status, "applied_at": a.applied_at.isoformat(),
        "interview_date": a.interview_date.isoformat() if a.interview_date else None,
        "interview_link": a.interview_link,
        "interview_notes": a.interview_notes,
    } for a in Application.query.filter_by(drive_id=did).all()]), 200


@company_bp.route("/applications/<int:aid>/status", methods=["PUT"])
@company_required
def update_status(aid):
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    app = Application.query.get_or_404(aid)
    drive = PlacementDrive.query.get(app.drive_id)
    if not drive or drive.company_id != p.id:
        return jsonify({"error": "Not authorized"}), 403
    d = request.get_json() or {}
    new_status = d.get("status", "").strip()
    if new_status not in ("applied", "shortlisted", "selected", "rejected"):
        return jsonify({"error": "Invalid status"}), 400
    app.status = new_status
    db.session.commit()
    return jsonify({"message": f"Status updated to {new_status}"}), 200


# ── Interview Scheduling ──
@company_bp.route("/applications/<int:aid>/interview", methods=["PUT"])
@company_required
def schedule_interview(aid):
    """Schedule or update interview details for an application."""
    p = _profile()
    if not p:
        return jsonify({"error": "Not found"}), 404
    app = Application.query.get_or_404(aid)
    drive = PlacementDrive.query.get(app.drive_id)
    if not drive or drive.company_id != p.id:
        return jsonify({"error": "Not authorized"}), 403
    d = request.get_json() or {}
    interview_date = d.get("interview_date", "").strip()
    if interview_date:
        try:
            app.interview_date = datetime.fromisoformat(interview_date)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
    app.interview_link = d.get("interview_link", app.interview_link)
    app.interview_notes = d.get("interview_notes", app.interview_notes)
    # Auto-shortlist when interview is scheduled
    if app.status == "applied" and app.interview_date:
        app.status = "shortlisted"
    db.session.commit()
    return jsonify({"message": "Interview scheduled successfully"}), 200
