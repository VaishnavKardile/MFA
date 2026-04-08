# from flask import render_template, request, redirect, url_for, session
# from ..models import User
# from .. import db
# from .otp_logic import generate_sms_otp, send_otp_via_sms

# from . import phase2_bp

# # ==========================================
# # REGISTRATION FLOW: SETTING UP SMS
# # ==========================================

# @phase2_bp.route('/setup-sms/<username>', methods=['GET', 'POST'])
# def setup_sms(username):
#     if request.method == 'POST':
#         phone = request.form.get('phone_number')
#         otp = generate_sms_otp()
        
#         # Store OTP and Phone temporarily in session for verification
#         session['temp_otp'] = otp
#         session['temp_phone'] = phone
        
#         # Send the code using Twilio
#         if send_otp_via_sms(phone, otp):
#             return redirect(url_for('phase2.verify_sms_page', username=username))
#         return "Failed to send SMS. Check your Twilio credentials and terminal for errors."

#     return render_template('setup_sms.html', username=username)


# @phase2_bp.route('/verify-sms/<username>', methods=['GET', 'POST'])
# def verify_sms_page(username):
#     if request.method == 'POST':
#         user_input = request.form.get('otp_code')
        
#         if user_input == session.get('temp_otp'):
#             # Save the verified phone number to the database permanently
#             user = User.query.filter_by(username=username).first()
#             if user:
#                 user.phone_number = session.get('temp_phone') 
#                 db.session.commit()
            
#             # Move to Phase 3: Biometrics
#             return redirect(url_for('phase3.register_face_page', username=username))
#         return "Invalid Code!"

#     return render_template('verify_sms.html', username=username)


# # ==========================================
# # LOGIN FLOW: SMS GATE
# # ==========================================

# @phase2_bp.route('/login-sms', methods=['GET', 'POST'])
# def login_sms():
#     # Ensure they passed Gate 1 (Password) first
#     if 'login_user' not in session:
#         return redirect(url_for('phase1.login'))

#     username = session['login_user']
#     user = User.query.filter_by(username=username).first_or_404()

#     if request.method == 'POST':
#         user_input = request.form.get('otp_code')
        
#         # Check if the code they typed matches the one we sent
#         if user_input == session.get('temp_otp'):
#             # Move to Gate 3: Biometrics
#             return redirect(url_for('phase3.login_face_page'))
#         return "Invalid SMS Code!"

#     # If it's a GET request (they just arrived on the page), generate and send the code
#     otp = generate_sms_otp()
#     session['temp_otp'] = otp
#     send_otp_via_sms(user.phone_number, otp) 
    
#     return render_template('login_sms.html', username=username)


import time

from flask import render_template, request, redirect, url_for, session, flash
from ..models import User
from .. import db
from .otp_logic import generate_sms_otp, send_otp_via_sms
from . import phase2_bp

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------
OTP_TTL_SECONDS  = 600   # OTP is valid for 10 minutes
MAX_OTP_ATTEMPTS = 3     # Lock out after 3 wrong guesses


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_gate1():
    """
    Returns a redirect response if Gate 1 has not been passed, else None.
    Use at the top of every Phase 2 view that requires an authenticated session.
    """
    if not session.get("gate1_passed") or "login_user" not in session:
        session.clear()
        flash("Access denied. Please complete Gate 1 first.", "error")
        return redirect(url_for("phase1.login"))
    return None


def _otp_is_expired() -> bool:
    """True if the OTP timestamp stored in session is older than OTP_TTL_SECONDS."""
    issued_at = session.get("otp_issued_at")
    if not issued_at:
        return True
    return (time.time() - issued_at) > OTP_TTL_SECONDS


# ===========================================================================
# REGISTRATION FLOW — Phase 2: Possession (SMS Setup)
# ===========================================================================

@phase2_bp.route("/setup-sms/<username>", methods=["GET", "POST"])
def setup_sms(username):
    """
    Registration step: let the user provide their phone number and send an OTP.
    No session-gate needed here because the user just created their account in
    Phase 1 and was immediately redirected — they carry the username in the URL.
    """
    if request.method == "POST":
        phone = request.form.get("phone_number", "").strip()

        if not phone:
            flash("Please enter a valid phone number.", "error")
            return redirect(url_for("phase2.setup_sms", username=username))

        otp = generate_sms_otp()

        # Store OTP, phone, timestamp, and zero the attempt counter
        session["temp_otp"]       = otp
        session["temp_phone"]     = phone
        session["otp_issued_at"]  = time.time()
        session["otp_attempts"]   = 0

        if send_otp_via_sms(phone, otp):
            flash("Verification code sent! Enter it below.", "info")
            return redirect(url_for("phase2.verify_sms_page", username=username))

        flash(
            "Failed to send SMS. Check your Twilio credentials and try again.",
            "error",
        )
        return redirect(url_for("phase2.setup_sms", username=username))

    return render_template("setup_sms.html", username=username)


@phase2_bp.route("/verify-sms/<username>", methods=["GET", "POST"])
def verify_sms_page(username):
    """Registration step: verify the OTP before saving the phone number."""
    if request.method == "POST":
        user_input = request.form.get("otp_code", "").strip()

        # ── Attempt counter guard ─────────────────────────────────────────
        attempts = session.get("otp_attempts", 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            session.clear()
            flash(
                "Too many incorrect codes. Registration has been reset — please start again.",
                "error",
            )
            return redirect(url_for("phase1.signup"))

        # ── Expiry check ──────────────────────────────────────────────────
        if _otp_is_expired():
            flash("Your verification code has expired. Please request a new one.", "error")
            return redirect(url_for("phase2.setup_sms", username=username))

        # ── Code comparison ───────────────────────────────────────────────
        if user_input != session.get("temp_otp"):
            session["otp_attempts"] = attempts + 1
            remaining = MAX_OTP_ATTEMPTS - session["otp_attempts"]
            flash(f"Incorrect code. {remaining} attempt(s) remaining.", "error")
            return redirect(url_for("phase2.verify_sms_page", username=username))

        # ── OTP CORRECT — persist phone number ────────────────────────────
        user = User.query.filter_by(username=username).first_or_404()
        user.phone_number = session.get("temp_phone")
        db.session.commit()

        # Clean up OTP session keys
        for key in ("temp_otp", "temp_phone", "otp_issued_at", "otp_attempts"):
            session.pop(key, None)

        flash("Phone number verified! Now register your face to complete setup.", "success")
        return redirect(url_for("phase3.register_face_page", username=username))

    return render_template("verify_sms.html", username=username)


# ===========================================================================
# LOGIN FLOW — Gate 2: Possession (SMS Verification)
# ===========================================================================

@phase2_bp.route("/login-sms", methods=["GET", "POST"])
def login_sms():
    # ── Gate 1 enforcement ────────────────────────────────────────────────
    gate_check = _require_gate1()
    if gate_check:
        return gate_check

    username = session["login_user"]
    user = User.query.filter_by(username=username).first_or_404()

    if request.method == "POST":
        user_input = request.form.get("otp_code", "").strip()

        # ── Attempt counter guard ─────────────────────────────────────────
        attempts = session.get("otp_attempts", 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            session.clear()
            flash(
                "Too many incorrect codes. Your session has been terminated for security.",
                "error",
            )
            return redirect(url_for("phase1.login"))

        # ── Expiry check ──────────────────────────────────────────────────
        if _otp_is_expired():
            flash(
                "Your code has expired. Please log in again to receive a new one.",
                "error",
            )
            session.clear()
            return redirect(url_for("phase1.login"))

        # ── Code comparison ───────────────────────────────────────────────
        if user_input != session.get("temp_otp"):
            session["otp_attempts"] = attempts + 1
            remaining = MAX_OTP_ATTEMPTS - session["otp_attempts"]
            flash(f"Incorrect code. {remaining} attempt(s) remaining.", "error")
            return redirect(url_for("phase2.login_sms"))

        # ── Gate 2 PASSED ─────────────────────────────────────────────────
        for key in ("temp_otp", "otp_issued_at", "otp_attempts"):
            session.pop(key, None)

        session["gate2_passed"] = True  # Gate sentinel — Phase 3 checks this

        flash("SMS verified. Final step: biometric confirmation.", "info")
        return redirect(url_for("phase3.login_face_page"))

    # ── GET request: generate and dispatch a fresh OTP ───────────────────
    otp = generate_sms_otp()
    session["temp_otp"]      = otp
    session["otp_issued_at"] = time.time()
    session["otp_attempts"]  = 0

    if not send_otp_via_sms(user.phone_number, otp):
        flash(
            "Failed to send SMS. Please try again or contact support.",
            "error",
        )

    return render_template("login_sms.html", username=username)