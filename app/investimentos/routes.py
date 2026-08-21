from datetime import date

from flask import render_template, request, redirect, url_for

from app import db
from app.investimentos import investimentos
from app.investimentos.models import Investimento


@investimentos.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()

        valor_investido = request.form.get(
            "valor_investido",
            "0"
        )

        valor_atual = request.form.get(
            "valor_atual",
            "0"
        )

        data_investimento = request.form.get(
            "data",
            ""
        )

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        if not nome or not tipo:
            return redirect(
                url_for("investimentos.index")
            )

        try:
            valor_investido = float(
                valor_investido.replace(",", ".")
            )

            valor_atual = float(
                valor_atual.replace(",", ".")
            )

        except (ValueError, AttributeError):
            return redirect(
                url_for("investimentos.index")
            )

        if data_investimento:
            try:
                data_obj = date.fromisoformat(
                    data_investimento
                )
            except ValueError:
                data_obj = date.today()
        else:
            data_obj = date.today()

        investimento = Investimento(
            nome=nome,
            tipo=tipo,
            valor_investido=valor_investido,
            valor_atual=valor_atual,
            data=data_obj,
            observacao=observacao or None,
            usuario_id=1
        )

        db.session.add(investimento)
        db.session.commit()

        return redirect(
            url_for("investimentos.index")
        )

    investimentos_lista = Investimento.query.order_by(
        Investimento.id.desc()
    ).all()

    total_investido = sum(
        item.valor_investido
        for item in investimentos_lista
    )

    total_atual = sum(
        item.valor_atual
        for item in investimentos_lista
    )

    rendimento = total_atual - total_investido

    percentual = 0

    if total_investido > 0:
        percentual = (
            rendimento / total_investido
        ) * 100

    return render_template(
        "investimentos/index.html",
        investimentos=investimentos_lista,
        total_investido=total_investido,
        total_atual=total_atual,
        rendimento=rendimento,
        percentual=percentual
    )


@investimentos.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    investimento = Investimento.query.get_or_404(id)

    db.session.delete(investimento)
    db.session.commit()

    return redirect(
        url_for("investimentos.index")
    )