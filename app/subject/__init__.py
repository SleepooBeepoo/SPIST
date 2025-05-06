from flask import Blueprint

subject_bp = Blueprint('subject', __name__, url_prefix='/subject')

from app.subject import routes