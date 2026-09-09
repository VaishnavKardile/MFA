from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus  # Add this import
import os
from dotenv import load_dotenv

load_dotenv()


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        from . import models 
        from .phase1_basic.routes import phase1_bp
        from .phase2_otp.routes import phase2_bp
        from .phase3_face.routes import phase3_bp
        from .dashboard.routes import dashboard_bp

        app.register_blueprint(phase1_bp)
        app.register_blueprint(phase2_bp)
        app.register_blueprint(phase3_bp)
        app.register_blueprint(dashboard_bp)

        db.create_all()

    return app