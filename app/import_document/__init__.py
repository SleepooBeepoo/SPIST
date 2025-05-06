# Import document module
from flask import Blueprint

import_document_bp = Blueprint('import_document', __name__)

from app.import_document import routes