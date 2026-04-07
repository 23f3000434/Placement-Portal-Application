from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db
from models import User, StudentProfile, CompanyProfile
import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate required fields
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not email or not password or not role:
        return jsonify({"error": "email, password, and role are required"}), 400

    if role not in ("student", "company"):
        return jsonify({"error": "role must be 'student' or 'company'"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Create user
    user = User(email=email, password=password_hash, role=role)
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    # Create role-specific profile
    if role == "student":
        name = data.get("name")
        branch = data.get("branch")
        cgpa = data.get("cgpa")
        year = data.get("year")

        if not all([name, branch, cgpa, year]):
            db.session.rollback()
            return jsonify({"error": "Student registration requires name, branch, cgpa, year"}), 400

        profile = StudentProfile(
            user_id=user.id,
            name=name,
            branch=branch,
            cgpa=float(cgpa),
            year=int(year),
            phone=data.get("phone")
        )
        db.session.add(profile)

    elif role == "company":
        company_name = data.get("company_name")

        if not company_name:
            db.session.rollback()
            return jsonify({"error": "Company registration requires company_name"}), 400

        profile = CompanyProfile(
            user_id=user.id,
            company_name=company_name,
            hr_contact=data.get("hr_contact"),
            website=data.get("website"),
            description=data.get("description")
        )
        db.session.add(profile)

    db.session.commit()

    return jsonify({"message": f"{role} registered successfully", "user_id": user.id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account has been deactivated"}), 403

    # Check password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create JWT token with user info in the identity
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }), 200
