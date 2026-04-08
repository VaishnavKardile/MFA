# from flask import render_template, request, redirect, url_for, session
# from ..models import User
# from .. import db
# from . import phase1_bp

# # ==========================================
# # REGISTRATION FLOW: GATE 1 (Knowledge)
# # ==========================================

# @phase1_bp.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         # Check if user already exists
#         existing_user = User.query.filter_by(username=username).first()
#         if existing_user:
#             return "Username already exists! Try another one."

#         # Create new user and hash the password
#         new_user = User(username=username)
#         new_user.set_password(password)
        
#         db.session.add(new_user)
#         db.session.commit()

#         # Gate 1 Passed: Send them to Gate 2 (SMS Registration)
#         return redirect(url_for('phase2.setup_sms', username=username))

#     return render_template('signup.html')


# # ==========================================
# # LOGIN FLOW: GATE 1 (Knowledge)
# # ==========================================

# @phase1_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         user = User.query.filter_by(username=username).first()

#         # Check if the user exists AND the typed password matches the hash
#         if user and user.check_password(password):
            
#             # Put their name in the session "backpack" so Phase 2 and 3 remember them
#             session['login_user'] = user.username
            
#             # Gate 1 Passed: Send them to Gate 2 (SMS Verification)
#             return redirect(url_for('phase2.login_sms'))
        
#         return "Invalid username or password!"

#     return render_template('login.html')


# # ==========================================
# # LOGOUT ROUTE
# # ==========================================

# @phase1_bp.route('/logout')
# def logout():
#     # Empty the session backpack
#     session.clear() 
#     return redirect(url_for('phase1.login'))


# @phase1_bp.route('/')
# def home():
#     # If they visit the base URL, automatically send them to the login page
#     return redirect(url_for('phase1.login'))

from flask import render_template, request, redirect, url_for, session, flash
from ..models import User
from .. import db
from . import phase1_bp

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------
MAX_LOGIN_ATTEMPTS = 5   # Lock session after this many failed password attempts


# ===========================================================================
# HELPER — Gate enforcement decorator factory
# ===========================================================================

def _abort_to_login(message: str = "Session expired. Please log in again."):
    """Clear session and send the user back to login with a flash message."""
    session.clear()
    flash(message, "error")
    return redirect(url_for("phase1.login"))


# ===========================================================================
# REGISTRATION FLOW — Gate 1: Knowledge (Sign Up)
# ===========================================================================

@phase1_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # ── Input validation ──────────────────────────────────────────────
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("phase1.signup"))

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return redirect(url_for("phase1.signup"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("phase1.signup"))

        # ── Duplicate check ───────────────────────────────────────────────
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken. Choose another.", "error")
            return redirect(url_for("phase1.signup"))

        # ── Persist new user ──────────────────────────────────────────────
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Now link your phone number.", "success")
        return redirect(url_for("phase2.setup_sms", username=username))

    return render_template("signup.html")


# ===========================================================================
# LOGIN FLOW — Gate 1: Knowledge (Login)
# ===========================================================================

@phase1_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # ── Initialise attempt counter (persists across failed attempts) ──
        if "login_attempts" not in session:
            session["login_attempts"] = 0

        # ── Hard lockout check ────────────────────────────────────────────
        if session["login_attempts"] >= MAX_LOGIN_ATTEMPTS:
            session.clear()
            flash(
                "Too many failed attempts. Your session has been reset for security.",
                "error",
            )
            return redirect(url_for("phase1.login"))

        # ── Credential validation ─────────────────────────────────────────
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            session["login_attempts"] += 1
            remaining = MAX_LOGIN_ATTEMPTS - session["login_attempts"]
            flash(
                f"Invalid username or password. {remaining} attempt(s) remaining.",
                "error",
            )
            return redirect(url_for("phase1.login"))

        # ── Gate 1 PASSED ─────────────────────────────────────────────────
        # Store only what downstream gates need; reset attempt counter.
        session.pop("login_attempts", None)
        session["login_user"]    = user.username
        session["gate1_passed"]  = True     # Gate sentinel — Phase 2 checks this
        session["gate2_passed"]  = False    # Pre-emptively mark Gate 2 as not yet done

        flash(f"Password verified. Sending SMS code to your registered number.", "info")
        return redirect(url_for("phase2.login_sms"))

    return render_template("login.html")


# ===========================================================================
# LOGOUT
# ===========================================================================

@phase1_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been securely logged out.", "success")
    return redirect(url_for("phase1.login"))


# ===========================================================================
# ROOT — redirect to login
# ===========================================================================

@phase1_bp.route("/")
def home():
    return redirect(url_for("phase1.login"))