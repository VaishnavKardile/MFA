from flask import Blueprint

# 1. Define the Blueprint here, exactly as your structure planned
phase3_bp = Blueprint('phase3', __name__)

# 2. Import the routes at the bottom so they attach to the blueprint
from . import routes