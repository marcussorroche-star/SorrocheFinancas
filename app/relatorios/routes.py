from flask import Blueprint, render_template
from datetime import date

from sqlalchemy import extract

from app.receitas.models import Receita
from app.despesas.models import Despesa


relatorios = Blueprint(
    "relatorios",
    __name__,
    url_prefix="/relatorios"
)


@relatorios.route("/mensal")
def mensal():

    hoje = date.today()


    receitas = Receita.query.filter(
        extract("month", Receita.data) == hoje.month,
        extract("year", Receita.data) == hoje.year
    ).all()


    despesas = Despesa.query.filter(
        extract("month", Despesa.data) == hoje.month,
        extract("year", Despesa.data) == hoje.year
    ).all()


    total_receitas = sum(
        receita.valor or 0
        for receita in receitas
    )


    total_despesas = sum(
        despesa.valor or 0
        for despesa in despesas
    )


    saldo = total_receitas - total_despesas


    return render_template(
        "relatorios/mensal.html",
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=saldo
    )