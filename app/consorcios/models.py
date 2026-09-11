from app import db


class Consorcio(db.Model):

    __tablename__ = "consorcios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    descricao = db.Column(
        db.String(150),
        nullable=False
    )

    administradora = db.Column(
        db.String(150),
        nullable=True
    )

    tipo = db.Column(
        db.String(50),
        nullable=True
    )

    valor_carta = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    valor_entrada = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

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

    contem_lance = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    valor_lance = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    contemplado = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    data_contemplacao = db.Column(
        db.Date,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Em andamento"
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
