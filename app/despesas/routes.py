from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from app import db
from .models import Despesa

despesas = Blueprint(
    "despesas",
    __name__,
    url_prefix="/despesas"
)

@despesas.route("/")
def index():
    lista = Despesa.query.order_by(
        Despesa.data.desc()
    ).all()

    return render_template(
        "despesas/lista.html",
        despesas=lista
    )

@despesas.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "GET":
        return render_template(
            "despesas/nova.html"
        )

    try:
        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        categoria = request.form.get(
            "categoria",
            ""
        ).strip()

        valor_texto = request.form.get(
            "valor",
            "0"
        ).strip().replace(",", ".")

        valor = float(valor_texto or 0)

        vencimento_texto = request.form.get(
            "vencimento",
            ""
        ).strip()

        vencimento = None

        if vencimento_texto:
            vencimento = date.fromisoformat(
                vencimento_texto
            )

        forma_pagamento = request.form.get(
            "forma_pagamento",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Pendente"
        ).strip()

        if not descricao:
            flash(
                "Informe a descricao da despesa.",
                "danger"
            )
            return redirect(
                url_for("despesas.nova")
            )

        if not categoria:
            flash(
                "Informe a categoria da despesa.",
                "danger"
            )
            return redirect(
                url_for("despesas.nova")
            )

        if valor <= 0:
            flash(
                "Informe um valor maior que zero.",
                "danger"
            )
            return redirect(
                url_for("despesas.nova")
            )

        despesa = Despesa(
            descricao=descricao,
            categoria=categoria,
            valor=valor,
            data=date.today(),
            vencimento=vencimento,
            forma_pagamento=forma_pagamento,
            status=status or "Pendente",
            usuario_id=1
        )

        db.session.add(despesa)
        db.session.commit()

        flash(
            "Despesa lancada com sucesso.",
            "success"
        )

        return redirect(
            url_for("despesas.index")
        )

    except Exception as erro:
        db.session.rollback()

        flash(
            f"Erro ao lancar despesa: {erro}",
            "danger"
        )

        return redirect(
            url_for("despesas.nova")
        )

@despesas.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    despesa = Despesa.query.get_or_404(id)

    try:
        db.session.delete(despesa)
        db.session.commit()

        flash(
            "Despesa excluida com sucesso.",
            "success"
        )

    except Exception as erro:
        db.session.rollback()

        flash(
            f"Erro ao excluir despesa: {erro}",
            "danger"
        )

    return redirect(
        url_for("despesas.index")
    )