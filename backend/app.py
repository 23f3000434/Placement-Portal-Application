from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cache, mail
from seed import seed_admin, seed_demo_data
import os


def create_app():
    app = Flask(__name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="/static")
    app.config.from_object(Config)
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    try:
        cache.init_app(app)
        with app.app_context():
            cache.get("_test")
    except Exception:
        app.config["CACHE_TYPE"] = "SimpleCache"
        cache.init_app(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "resumes"), exist_ok=True)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")

    with app.app_context():
        db.create_all()
        seed_admin()
        seed_demo_data()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(404)
    def not_found(e):
        from flask import request as r
        if r.path.startswith("/api/"):
            return {"error": "Not found"}, 404
        return render_template("index.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
