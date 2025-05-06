from flask import Blueprint

submission_bp = Blueprint('submission', __name__, url_prefix='/submission')

from app.submission import routes