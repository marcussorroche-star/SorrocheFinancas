from app import db

class CompraCartao(db.Model):

    __tablename__ = "compras_cartao"

    id = db.Column(db.Integer, primary_key=True)

    cartao_id = db.Column(db.Integer)

    descricao = db.Column(db.String(200))

    valor_total = db.Column(db.Float)

    parcelas = db.Column(db.Integer)

    parcela_atual = db.Column(db.Integer)

    valor_parcela = db.Column(db.Float)

    data_compra = db.Column(db.Date)

    mes_lancamento = db.Column(db.Integer)

    ano_lancamento = db.Column(db.Integer)

    pago = db.Column(db.Boolean, default=False)