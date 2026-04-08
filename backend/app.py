from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache, mail
from seed import seed_admin
import os


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="/static",
    )
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Initialize cache with fallback to simple cache if Redis isn't running
    try:
        cache.init_app(app)
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

    # Jinja2 entry point — serves the Vue SPA
    @app.route("/")
    def index():
        return render_template("index.html")

    # Handle client-side routing — all non-API routes serve the SPA
    @app.errorhandler(404)
    def not_found(e):
        from flask import request as req
        if req.path.startswith("/api/"):
            return {"error": "Not found"}, 404
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
