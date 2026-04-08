from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db
from models import User, StudentProfile, CompanyProfile
import bcrypt

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    email, pw, role = d.get("email","").strip(), d.get("password","").strip(), d.get("role","").strip()
    if not email or not pw or role not in ("student","company"):
        return jsonify({"error": "Valid email, password (6+ chars), and role (student/company) required"}), 400
    if len(pw) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, password=hashed, role=role)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        name = d.get("name","").strip()
        branch = d.get("branch","").strip()
        if not name or not branch:
            db.session.rollback()
            return jsonify({"error": "Name and branch are required for students"}), 400
        db.session.add(StudentProfile(
            user_id=user.id, name=name, branch=branch.upper(),
            cgpa=float(d.get("cgpa", 0)), year=int(d.get("year", 2026)),
            phone=d.get("phone","").strip()
        ))
    else:
        cname = d.get("company_name","").strip()
        if not cname:
            db.session.rollback()
            return jsonify({"error": "Company name is required"}), 400
        db.session.add(CompanyProfile(
            user_id=user.id, company_name=cname,
            hr_contact=d.get("hr_contact","").strip(),
            website=d.get("website","").strip(),
            description=d.get("description","").strip()
        ))
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": role})
    return jsonify({"message": "Registration successful", "token": token, "role": role, "user_id": user.id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json() or {}
    email, pw = d.get("email","").strip(), d.get("password","").strip()
    if not email or not pw:
        return jsonify({"error": "Email and password required"}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(pw.encode(), user.password.encode()):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        return jsonify({"error": "Account deactivated"}), 403
    if user.role == "company" and user.company_profile and user.company_profile.is_blacklisted:
        return jsonify({"error": "Company blacklisted"}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    resp = {"message": "Login successful", "token": token, "role": user.role, "user_id": user.id}
    if user.role == "student" and user.student_profile:
        resp["name"] = user.student_profile.name
    elif user.role == "company" and user.company_profile:
        resp["company_name"] = user.company_profile.company_name
        resp["approval_status"] = user.company_profile.approval_status
    return jsonify(resp), 200
