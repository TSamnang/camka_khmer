from flask import Blueprint

front_bp = Blueprint("front_bp", __name__, template_folder='templates')

from . import home
from . import product
from . import our_farm
from . import about
from . import contact
from . import customer
from . import checkout
from . import cart