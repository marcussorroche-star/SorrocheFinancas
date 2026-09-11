from app import db


class Financiamento(db.Model):

    __tablename__ = "financiamentos"

    id = db.Column(db.Integer, primary_key=True)

    descricao = db.Column(db.String(150), nullable=False)

    valor_total = db.Column(db.Float, nullable=False, default=0)

    entrada = db.Column(db.Float, nullable=False, default=0)

    valor_financiado = db.Column(db.Float, nullable=False, default=0)

    quantidade_parcelas = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    valor_parcela = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    juros = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    data_inicio = db.Column(
        db.Date,
        nullable=False
    )

    primeiro_vencimento = db.Column(
        db.Date,
        nullable=True
    )

    dia_vencimento = db.Column(
        db.Integer,
        nullable=True
    )

    parcelas_pagas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    valor_pago = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    saldo_restante = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Em aberto"
    )

    observacao = db.Column(
        db.String(500),
        nullable=True
    )

    usuario_id = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )
