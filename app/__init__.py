from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus  # Add this import

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # 1. Define your password as a plain string
    raw_password = "Your@Password@With@Special@Chars" 
    
    # 2. Let Python handle the encoding for you safely
    encoded_password = quote_plus(raw_password)
    
    # 3. Build the URI using the encoded password
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:Vaishnav%4023510@127.0.0.1:3306/3fa_db"
    
    app.config['SECRET_KEY'] = 'super_secret_key_for_major_project'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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