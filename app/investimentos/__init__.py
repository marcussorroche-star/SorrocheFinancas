from flask import Blueprint

investimentos = Blueprint(
    "investimentos",
    __name__,
    url_prefix="/investimentos"
)