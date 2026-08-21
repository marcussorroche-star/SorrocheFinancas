from app import db

class Receita(db.Model):

    __tablename__ = "receitas"

    id = db.Column(db.Integer, primary_key=True)

    descricao = db.Column(db.String(200))

    valor = db.Column(db.Float)

    categoria = db.Column(db.String(100))

    data = db.Column(db.Date)

    recorrente = db.Column(db.Boolean, default=False)

    observacao = db.Column(db.Text)
    class Despesa(db.Model):

    __tablename__ = "despesas"

    id = db.Column(db.Integer, primary_key=True)

    descricao = db.Column(db.String(200))

    valor = db.Column(db.Float)

    categoria = db.Column(db.String(100))

    data = db.Column(db.Date)

    recorrente = db.Column(db.Boolean, default=False)

    observacao = db.Column(db.Text)