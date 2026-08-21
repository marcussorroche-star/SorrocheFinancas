from app import db

class Cartao(db.Model):

    __tablename__ = "cartoes"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))

    banco = db.Column(db.String(100))

    limite = db.Column(db.Float)

    limite_disponivel = db.Column(db.Float)

    fechamento = db.Column(db.Integer)

    vencimento = db.Column(db.Integer)

    fatura_atual = db.Column(db.Float, default=0)

    ativa = db.Column(db.Boolean, default=True)