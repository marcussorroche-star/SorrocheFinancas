from app import db


class ItemDespesa(db.Model):

    __tablename__ = "itens_despesa"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    despesa_id = db.Column(
        db.Integer,
        nullable=False
    )

    pasta_id = db.Column(
        db.Integer,
        nullable=True
    )

    descricao = db.Column(
        db.String(150),
        nullable=False
    )

    quantidade = db.Column(
        db.Float,
        nullable=False,
        default=1
    )

    valor_unitario = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    valor_total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )