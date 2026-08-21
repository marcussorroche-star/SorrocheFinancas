from app import db


class Juro(db.Model):

    __tablename__ = "juros"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    descricao = db.Column(
        db.String(100),
        nullable=False
    )

    categoria = db.Column(
        db.String(50),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    data = db.Column(
        db.Date,
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        nullable=False
    )