from app import db


class Investimento(db.Model):

    __tablename__ = "investimentos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    tipo = db.Column(
        db.String(50),
        nullable=False
    )

    valor_investido = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    valor_atual = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    data = db.Column(
        db.Date,
        nullable=False
    )

    observacao = db.Column(
        db.String(255),
        nullable=True
    )

    usuario_id = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )