from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache, mail
from seed import seed_admin
import os


def create_app():
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Initialize cache with fallback to simple cache if Redis isn't running
    try:
        cache.init_app(app)
        # Test Redis connection
        with app.app_context():
            cache.get("test")
    except Exception:
        app.config["CACHE_TYPE"] = "SimpleCache"
        cache.init_app(app)
        print("WARNING: Redis not available, using SimpleCache")

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")

    # Create tables and seed admin
    with app.app_context():
        db.create_all()
        seed_admin()

    # Serve Vue frontend in production
    @app.route("/")
    def serve_frontend():
        return send_from_directory(app.static_folder, "index.html")

    @app.errorhandler(404)
    def not_found(e):
        # If API route not found, return JSON error
        from flask import request
        if request.path.startswith("/api/"):
            return {"error": "Not found"}, 404
        # Otherwise serve Vue app (client-side routing)
        return send_from_directory(app.static_folder, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
