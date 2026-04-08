# from flask import render_template, request, redirect, url_for, session
# from ..models import User
# from .. import db
# from .vision_logic import get_face_encoding_from_base64, verify_face_against_db 

# # Import the Blueprint you already defined in __init__.py
# from . import phase3_bp

# @phase3_bp.route('/register-face/<username>', methods=['GET'])
# def register_face_page(username):
#     # Renders the webpage where the webcam turns on
#     return render_template('register_face.html', username=username)

# @phase3_bp.route('/register-face', methods=['POST'])
# def register_face():
#     username = request.form.get('username')
#     image_data = request.form.get('image_data')

#     if not image_data:
#         return "No image data provided!"

#     # Use the logic file to process the image
#     encoding_bytes, msg = get_face_encoding_from_base64(image_data)
    
#     if not encoding_bytes:
#         # If it failed (no face, multiple faces), return the error message
#         return msg

#     # Save the biometric data to the database
#     user = User.query.filter_by(username=username).first_or_404()
#     user.face_encoding = encoding_bytes
#     db.session.commit()

#     return f"<h1>Phase 3 Complete!</h1><p>Facial biometrics securely saved for {username}. Your 3FA account is now fully registered.</p>"


# # --- LOGIN FLOW: GATE 3 ---

# @phase3_bp.route('/login-face', methods=['GET'])
# def login_face_page():
#     # Security check: Make sure they passed Gate 1 and 2!
#     if 'login_user' not in session:
#         return redirect(url_for('phase1.login'))
#     return render_template('login_face.html', username=session['login_user'])

# @phase3_bp.route('/login-face', methods=['POST'])
# def login_face_submit():
#     if 'login_user' not in session:
#         return redirect(url_for('phase1.login'))
        
#     username = session['login_user']
#     image_data = request.form.get('image_data')
    
#     user = User.query.filter_by(username=username).first_or_404()
    
#     # Run the comparison math
#     is_match, msg = verify_face_against_db(user.face_encoding, image_data)
    
#     if is_match:
#         # FULL SYSTEM UNLOCKED!
#         session['fully_authenticated'] = True
#         return f"<h1 style='color: green;'>ACCESS GRANTED</h1><h2>Welcome, {username}!</h2><p>You have successfully passed all 3 factors of authentication.</p>"
#     else:
#         # BIOMETRIC FAILURE
#         return f"<h1 style='color: red;'>ACCESS DENIED</h1><p>{msg}</p>"


from flask import render_template, request, redirect, url_for, session, flash
from ..models import User
from .. import db
from .vision_logic import get_face_encoding_from_base64, verify_face_against_db
from . import phase3_bp

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------
MAX_FACE_ATTEMPTS = 3   # Allow 3 biometric attempts before killing the session


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_gate1_and_gate2():
    """
    Returns a redirect response if Gate 1 or Gate 2 have not been passed.
    Any attempt to reach Phase 3 without both prior gates clears the session.
    """
    if not session.get("gate1_passed") or "login_user" not in session:
        session.clear()
        flash("Access denied. Please complete Gate 1 first.", "error")
        return redirect(url_for("phase1.login"))

    if not session.get("gate2_passed"):
        # Gate 1 was passed but Gate 2 was skipped — suspicious; clear and boot.
        session.clear()
        flash("Access denied. Please complete Gate 2 (SMS) first.", "error")
        return redirect(url_for("phase1.login"))

    return None


# ===========================================================================
# REGISTRATION FLOW — Phase 3: Inherence (Face Registration)
# ===========================================================================

@phase3_bp.route("/register-face/<username>", methods=["GET"])
def register_face_page(username):
    """Render the webcam capture page for registration."""
    return render_template("register_face.html", username=username)


@phase3_bp.route("/register-face", methods=["POST"])
def register_face():
    """Receive the captured image, encode it, and persist the biometric."""
    username   = request.form.get("username", "").strip()
    image_data = request.form.get("image_data", "")

    if not username:
        flash("Session error: username missing. Please restart registration.", "error")
        return redirect(url_for("phase1.signup"))

    if not image_data:
        flash("No image was captured. Please allow camera access and try again.", "error")
        return redirect(url_for("phase3.register_face_page", username=username))

    # ── Process image and extract face encoding ───────────────────────────
    encoding_bytes, msg = get_face_encoding_from_base64(image_data)

    if not encoding_bytes:
        # msg contains a human-readable reason (no face detected, multiple faces, etc.)
        flash(f"Biometric capture failed: {msg}", "error")
        return redirect(url_for("phase3.register_face_page", username=username))

    # ── Persist encoding ──────────────────────────────────────────────────
    user = User.query.filter_by(username=username).first_or_404()
    user.face_encoding = encoding_bytes
    db.session.commit()

    flash(
        "Biometric registered successfully! Your 3FA account is fully set up. You can now log in.",
        "success",
    )
    return redirect(url_for("phase1.login"))


# ===========================================================================
# LOGIN FLOW — Gate 3: Inherence (Face Verification)
# ===========================================================================

@phase3_bp.route("/login-face", methods=["GET"])
def login_face_page():
    """
    Render the biometric verification webcam page.
    Enforces that Gate 1 AND Gate 2 were both passed before allowing access.
    """
    gate_check = _require_gate1_and_gate2()
    if gate_check:
        return gate_check

    # Initialise face attempt counter for this login session
    if "face_attempts" not in session:
        session["face_attempts"] = 0

    return render_template("login_face.html", username=session["login_user"])


@phase3_bp.route("/login-face", methods=["POST"])
def login_face_submit():
    """
    Receive the captured image and run biometric comparison.
    Enforces gate checks again — the POST endpoint is equally reachable directly.
    """
    gate_check = _require_gate1_and_gate2()
    if gate_check:
        return gate_check

    username   = session["login_user"]
    image_data = request.form.get("image_data", "")

    # ── Input guard ───────────────────────────────────────────────────────
    if not image_data:
        flash("No image was captured. Please allow camera access and try again.", "error")
        return redirect(url_for("phase3.login_face_page"))

    # ── Attempt counter guard ─────────────────────────────────────────────
    attempts = session.get("face_attempts", 0)
    if attempts >= MAX_FACE_ATTEMPTS:
        session.clear()
        flash(
            "Too many failed biometric attempts. Your session has been terminated for security.",
            "error",
        )
        return redirect(url_for("phase1.login"))

    # ── Run face comparison ───────────────────────────────────────────────
    user = User.query.filter_by(username=username).first_or_404()
    is_match, msg = verify_face_against_db(user.face_encoding, image_data)

    if not is_match:
        session["face_attempts"] = attempts + 1
        remaining = MAX_FACE_ATTEMPTS - session["face_attempts"]

        if remaining == 0:
            session.clear()
            flash(
                "Biometric verification failed. Session terminated for security.",
                "error",
            )
            return redirect(url_for("phase1.login"))

        flash(
            f"Face not recognised: {msg} — {remaining} attempt(s) remaining.",
            "error",
        )
        return redirect(url_for("phase3.login_face_page"))

    # ── ALL THREE GATES PASSED ────────────────────────────────────────────
    # Remove the gate sentinels and attempt counters; mark as fully authenticated.
    for key in ("gate1_passed", "gate2_passed", "face_attempts", "login_attempts"):
        session.pop(key, None)

    session["fully_authenticated"] = True
    session["authenticated_user"]  = username

    flash(f"Access granted. Welcome, {username}.", "success")
    return redirect(url_for("dashboard.index"))   # ← point this at your dashboard route