from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import user_farmer
from . import product
from . import category
from . import order
