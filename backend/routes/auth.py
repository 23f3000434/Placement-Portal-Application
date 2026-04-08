from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db
from models import User, StudentProfile, CompanyProfile
import bcrypt
import re

auth_bp = Blueprint("auth", __name__)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "").strip()

    # Backend validation
    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required"}), 400

    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if role not in ("student", "company"):
        return jsonify({"error": "Role must be 'student' or 'company'"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Role-specific validation
    if role == "student":
        name = data.get("name", "").strip()
        branch = data.get("branch", "").strip()
        cgpa = data.get("cgpa")
        year = data.get("year")

        if not name:
            return jsonify({"error": "Name is required"}), 400
        if not branch:
            return jsonify({"error": "Branch is required"}), 400
        if cgpa is None or cgpa == "":
            return jsonify({"error": "CGPA is required"}), 400
        try:
            cgpa = float(cgpa)
            if cgpa < 0 or cgpa > 10:
                return jsonify({"error": "CGPA must be between 0 and 10"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid CGPA value"}), 400
        if year is None or year == "":
            return jsonify({"error": "Graduation year is required"}), 400
        try:
            year = int(year)
            if year < 2020 or year > 2035:
                return jsonify({"error": "Year must be between 2020 and 2035"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid year value"}), 400

    elif role == "company":
        company_name = data.get("company_name", "").strip()
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(email=email, password=password_hash, role=role)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        profile = StudentProfile(
            user_id=user.id,
            name=data.get("name", "").strip(),
            branch=data.get("branch", "").strip().upper(),
            cgpa=float(data.get("cgpa", 0)),
            year=int(data.get("year", 2026)),
            phone=data.get("phone", "").strip(),
        )
        db.session.add(profile)
    elif role == "company":
        profile = CompanyProfile(
            user_id=user.id,
            company_name=data.get("company_name", "").strip(),
            hr_contact=data.get("hr_contact", "").strip(),
            website=data.get("website", "").strip(),
            description=data.get("description", "").strip(),
        )
        db.session.add(profile)

    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({"message": "Registration successful", "token": token, "role": user.role, "user_id": user.id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Your account has been deactivated. Contact admin."}), 403

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

    if user.role == "student" and user.student_profile:
        response["name"] = user.student_profile.name
    elif user.role == "company" and user.company_profile:
        response["company_name"] = user.company_profile.company_name
        response["approval_status"] = user.company_profile.approval_status

    return jsonify(response), 200
