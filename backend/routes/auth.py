from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db
from models import User, StudentProfile, CompanyProfile
import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "").strip()

    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required"}), 400

    if role not in ("student", "company"):
        return jsonify({"error": "Role must be 'student' or 'company'"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(email=email, password=password_hash, role=role)
    db.session.add(user)
    db.session.flush()  # get user.id before committing

    if role == "student":
        profile = StudentProfile(
            user_id=user.id,
            name=data.get("name", ""),
            branch=data.get("branch", ""),
            cgpa=float(data.get("cgpa", 0)),
            year=int(data.get("year", 2026)),
            phone=data.get("phone", ""),
        )
        db.session.add(profile)
    elif role == "company":
        profile = CompanyProfile(
            user_id=user.id,
            company_name=data.get("company_name", ""),
            hr_contact=data.get("hr_contact", ""),
            website=data.get("website", ""),
            description=data.get("description", ""),
        )
        db.session.add(profile)

    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({"message": "Registration successful", "token": token, "role": user.role, "user_id": user.id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Your account has been deactivated. Contact admin."}), 403

    # For company users, check if blacklisted
    if user.role == "company" and user.company_profile:
        if user.company_profile.is_blacklisted:
            return jsonify({"error": "Your company has been blacklisted. Contact admin."}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    response = {
        "message": "Login successful",
        "token": token,
        "role": user.role,
        "user_id": user.id,
    }

    # Add profile info
    if user.role == "student" and user.student_profile:
        response["name"] = user.student_profile.name
    elif user.role == "company" and user.company_profile:
        response["company_name"] = user.company_profile.company_name
        response["approval_status"] = user.company_profile.approval_status

    return jsonify(response), 200
