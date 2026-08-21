from flask import Blueprint, render_template, request, redirect, url_for
import os
from datetime import datetime
import re

from app import db
from app.despesas.models import Despesa


leitor_comprovante = Blueprint(
    "leitor_comprovante",
    __name__,
    url_prefix="/leitor"
)


PASTA_UPLOAD = os.path.join(
    "uploads",
    "comprovantes"
)

os.makedirs(
    PASTA_UPLOAD,
    exist_ok=True
)


@leitor_comprovante.route("/", methods=["GET", "POST"])
def index():

    resultado = None

    if request.method == "POST":

        foto = request.files.get("foto")

        if foto and foto.filename:

            nome = (
                datetime.now().strftime("%Y%m%d%H%M%S")
                + "_"
                + foto.filename
            )

            caminho = os.path.join(
                PASTA_UPLOAD,
                nome
            )

            foto.save(caminho)

            resultado = {
                "mensagem": "Comprovante recebido com sucesso.",
                "arquivo": nome
            }

    return render_template(
        "leitor_comprovante/index.html",
        resultado=resultado
    )


def extrair_valor(texto):

    valores = re.findall(
        r"\d+[,\.]\d{2}",
        texto
    )

    if valores:
        return valores[-1]

    return "0,00"


@leitor_comprovante.route("/salvar", methods=["POST"])
def salvar_despesa():

    valor = request.form.get(
        "valor",
        "0"
    )

    valor = (
        valor
        .replace("R$", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        valor = float(valor)
    except ValueError:
        valor = 0.0


    despesa = Despesa(
        descricao=request.form.get(
            "estabelecimento"
        ) or "Comprovante",

        categoria="Comprovante",

        valor=valor,

        data=datetime.now().date(),

        forma_pagamento=request.form.get(
            "pagamento"
        ) or "Não informado",

        status="Pago",

        usuario_id=1
    )


    db.session.add(despesa)
    db.session.commit()


    return redirect(
        url_for("financeiro.index")
    )
