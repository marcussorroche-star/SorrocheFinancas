from app import db


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo = db.Column(
        db.String(30),
        nullable=False
    )

    valor_reservado = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    valor_utilizado = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    @property
    def valor_disponivel(self):
        return max(
            (self.valor_reservado or 0)
            - (self.valor_utilizado or 0),
            0
        )