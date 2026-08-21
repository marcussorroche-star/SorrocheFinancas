from app import db


class Meta(db.Model):

    __tablename__ = "metas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    valor_objetivo = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    valor_guardado = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    prazo_meses = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Em andamento"
    )

    usuario_id = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )