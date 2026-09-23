from flask import Blueprint

admin_bp = Blueprint("admin_bp", __name__, template_folder="/admin")

from . import auth
from . import dashboard
from . import user
from . import catalog
from . import sale
from . import setting