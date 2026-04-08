from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    # This is the name of the table that will appear in MySQL Workbench
    __tablename__ = 'users'
    
    # The Primary Key (Unique ID for each user)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    
    # Phase 1: Knowledge (The Hashed Password)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Phase 2: Possession (The 16-character secret key for PyOTP)
    totp_secret = db.Column(db.String(32), nullable=True) 
    
    # Phase 3: Inherence (The mathematical array of the user's face)
    # We use Text here because the face coordinates will be converted to a long string
    face_encoding = db.Column(db.Text, nullable=True)    

    # ... your other columns ...
    phone_number = db.Column(db.String(20), nullable=True) 

    # --- Security Helper Methods ---
    
    def set_password(self, password):
        """Hashes the password before saving it to the database."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if a typed password matches the saved hash."""
        return check_password_hash(self.password_hash, password)
    