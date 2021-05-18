from flask import Blueprint

users = Blueprint('users', __name__, url_prefix='/api/users')


from .auth import *
from .users import *
