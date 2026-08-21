from app import db


class Cartao(db.Model):

    __tablename__ = "cartoes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    # ============================================================
    # IDENTIFICAÇÃO DO CARTÃO
    # ============================================================

    ultimos4 = db.Column(
        db.String(4),
        nullable=True
    )

    limite = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    dia_abertura = db.Column(
        db.Integer,
        nullable=False
    )

    dia_fechamento = db.Column(
        db.Integer,
        nullable=False
    )

    dia_vencimento = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Ativo"
    )

    usuario_id = db.Column(
        db.Integer,
        nullable=False
    )


class CompraCartao(db.Model):

    __tablename__ = "compras_cartao"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cartao_id = db.Column(
        db.Integer,
        nullable=False
    )

    descricao = db.Column(
        db.String(100),
        nullable=False
    )

    categoria = db.Column(
        db.String(50),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    data_compra = db.Column(
        db.Date,
        nullable=False
    )

    parcelas = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )


class FaturaPaga(db.Model):

    __tablename__ = "faturas_pagas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cartao_id = db.Column(
        db.Integer,
        nullable=False
    )

    mes = db.Column(
        db.String(7),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    data_pagamento = db.Column(
        db.Date,
        nullable=False
    )