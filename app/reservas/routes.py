from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.reservas.models import Reserva
from app.receitas.models import Receita
from app.despesas.models import Despesa


reservas = Blueprint(
    "reservas",
    __name__,
    url_prefix="/reservas"
)


@reservas.route("/")
def index():

    reserva_despesas = Reserva.query.filter_by(
        tipo="despesas"
    ).first()

    reserva_financeira = Reserva.query.filter_by(
        tipo="financeira"
    ).first()

    total_receitas = 0
    total_despesas = 0

    try:
        total_receitas = (
            db.session.query(
                db.func.coalesce(
                    db.func.sum(Receita.valor),
                    0
                )
            ).scalar()
            or 0
        )
    except Exception:
        total_receitas = 0

    try:
        total_despesas = (
            db.session.query(
                db.func.coalesce(
                    db.func.sum(Despesa.valor),
                    0
                )
            ).scalar()
            or 0
        )
    except Exception:
        total_despesas = 0

    sobra = total_receitas - total_despesas

    if sobra > 0:

        valor_despesas = (
            reserva_despesas.valor_disponivel
            if reserva_despesas
            else 0
        )

        valor_financeira = (
            reserva_financeira.valor_disponivel
            if reserva_financeira
            else 0
        )

        if valor_despesas <= valor_financeira:

            opiniao_ia = (
                "A IA recomenda priorizar a Reserva de Despesas, "
                "pois ela está com menor valor disponível."
            )

            prioridade_ia = "Reserva de Despesas"

        else:

            opiniao_ia = (
                "A IA recomenda priorizar a Reserva Financeira, "
                "pois ela está com menor valor disponível."
            )

            prioridade_ia = "Reserva Financeira"

    elif sobra == 0:

        opiniao_ia = (
            "No momento não existe sobra financeira para direcionar "
            "às reservas."
        )

        prioridade_ia = "Aguardar sobra"

    else:

        opiniao_ia = (
            "No momento as despesas estão maiores que as receitas. "
            "A IA recomenda primeiro equilibrar o orçamento antes "
            "de aumentar as reservas."
        )

        prioridade_ia = "Equilibrar orçamento"

    return render_template(
        "reservas/index.html",
        reserva_despesas=reserva_despesas,
        reserva_financeira=reserva_financeira,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        sobra=sobra,
        opiniao_ia=opiniao_ia,
        prioridade_ia=prioridade_ia
    )


@reservas.route("/salvar", methods=["POST"])
def salvar():

    tipo = request.form.get(
        "tipo",
        ""
    ).strip()

    valor = request.form.get(
        "valor_reservado",
        "0"
    ).replace(",", ".")

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        valor = 0

    if tipo not in [
        "despesas",
        "financeira"
    ]:

        flash(
            "Tipo de reserva inválido.",
            "danger"
        )

        return redirect(
            url_for("reservas.index")
        )

    reserva = Reserva.query.filter_by(
        tipo=tipo
    ).first()

    if reserva is None:

        reserva = Reserva(
            tipo=tipo,
            valor_reservado=valor,
            valor_utilizado=0,
            ativo=True
        )

        db.session.add(reserva)

    else:

        reserva.valor_reservado = valor

    db.session.commit()

    flash(
        "Reserva atualizada com sucesso.",
        "success"
    )

    return redirect(
        url_for("reservas.index")
    )