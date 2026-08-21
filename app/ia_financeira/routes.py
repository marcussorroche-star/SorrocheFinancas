from flask import Blueprint, render_template
from app.receitas.models import Receita
from app.despesas.models import Despesa
from datetime import date


ia_financeira = Blueprint(
    "ia_financeira",
    __name__,
    url_prefix="/ia"
)



@ia_financeira.route("/")
def analisar():

    mes = date.today().month
    ano = date.today().year


    receitas = Receita.query.filter(
        Receita.data_receita.like(
            f"{ano}-{mes:02d}%"
        )
    ).all()


    despesas = Despesa.query.filter(
        Despesa.data_despesa.like(
            f"{ano}-{mes:02d}%"
        )
    ).all()



    total_receitas = sum(
        r.valor for r in receitas
    )


    total_despesas = sum(
        d.valor for d in despesas
    )


    saldo = (
        total_receitas -
        total_despesas
    )


    sugestoes = []


    if saldo < 0:

        situacao = "🔴 Saldo vermelho"

        sugestoes.append(
            "Evite novas compras parceladas."
        )

        sugestoes.append(
            "Revise seus maiores gastos."
        )

        sugestoes.append(
            "Priorize pagar dívidas com juros."
        )


    elif saldo < total_receitas * 0.2:

        situacao = "🟡 Atenção"

        sugestoes.append(
            "Você está comprometendo boa parte da renda."
        )

        sugestoes.append(
            "Tente guardar uma pequena reserva."
        )


    else:

        situacao = "🟢 Situação saudável"

        sugestoes.append(
            "Continue acompanhando seus gastos."
        )

        sugestoes.append(
            "Considere aumentar seus investimentos."
        )


    return render_template(
        "ia_financeira/index.html",
        situacao=situacao,
        receitas=total_receitas,
        despesas=total_despesas,
        saldo=saldo,
        sugestoes=sugestoes
    )