from app import db


class Despesa(db.Model):
    __tablename__ = "despesas"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False)
    vencimento = db.Column(db.Date, nullable=True)
    forma_pagamento = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pendente")
    usuario_id = db.Column(db.Integer, nullable=False)

    pasta_id = db.Column(
        db.Integer,
        db.ForeignKey("pastas.id"),
        nullable=True
    )

    pasta = db.relationship(
        "Pasta",
        backref="despesas",
        lazy=True
    )