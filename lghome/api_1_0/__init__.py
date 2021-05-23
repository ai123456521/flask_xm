# @ Time    : 2020/11/16 22:00

from flask import Blueprint

api = Blueprint('api_1_0', __name__, url_prefix='/api/v1.0')

from . import dmeo, verify_code, passport, profile, houses, orders, pay


