from app import db
from flask_login import UserMixin


class Usuario(UserMixin, db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    salario = db.Column(
        db.Float,
        default=0
    )

    objetivo = db.Column(
        db.Float,
        default=0
    )