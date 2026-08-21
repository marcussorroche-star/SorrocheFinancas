from app import db


class Pasta(db.Model):
    __tablename__ = "pastas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    descricao = db.Column(
        db.String(255),
        nullable=True
    )

    cor = db.Column(
        db.String(20),
        nullable=False,
        default="slate"
    )