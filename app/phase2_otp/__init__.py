from flask import Blueprint

# 1. Define the Blueprint here, exactly as your structure planned
phase2_bp = Blueprint('phase2', __name__)

# 2. Import the routes at the bottom so they attach to the blueprint
from . import routes