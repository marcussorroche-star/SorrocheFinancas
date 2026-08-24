from datetime import date

from app import db


class ItemEstoque(db.Model):
    __tablename__ = "itens_estoque"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(200),
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

    pasta_id = db.Column(
        db.Integer,
        db.ForeignKey("pastas.id"),
        nullable=True
    )

    data = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    tipo = db.Column(
        db.String(20),
        nullable=False,
        default="entrada"
    )

    observacao = db.Column(
        db.Text,
        nullable=True
    )

    pasta = db.relationship(
        "Pasta",
        backref=db.backref(
            "itens_estoque",
            lazy=True
        )
    )

    def calcular_total(self):

        self.valor_total = (
            float(self.quantidade or 0)
            * float(self.valor_unitario or 0)
        )

        return self.valor_total

    def __repr__(self):

        return (
            f"<ItemEstoque "
            f"{self.nome} "
            f"qtd={self.quantidade} "
            f"total={self.valor_total}>"
        )