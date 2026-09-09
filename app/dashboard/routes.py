from flask import render_template, session, redirect, url_for, flash
from . import dashboard_bp
# # Define the blueprint
# dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def index():
    # THE ULTIMATE SECURITY CHECK
    # If they didn't pass all 3 gates, boot them out!
    if not session.get('fully_authenticated'):
        flash("Unauthorized Access: You must complete all security verification steps.", "error")
        return redirect(url_for('phase1.login'))

    # Grab the user's name from the session backpack
    username = session.get('authenticated_user', 'Authorized Personnel')
    
    return render_template('dashboard.html', username=username)