from flask import Blueprint

estoque = Blueprint(
    "estoque",
    __name__,
    url_prefix="/estoque"
)