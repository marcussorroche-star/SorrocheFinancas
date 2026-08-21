from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.despesas.models import Despesa
from app.despesas.itens_models import ItemDespesa
from app.pastas.models import Pasta


itens = Blueprint(
    "itens",
    __name__,
    url_prefix="/despesas"
)


@itens.route("/<int:despesa_id>/itens")
def lista(despesa_id):
    despesa = Despesa.query.get_or_404(despesa_id)

    itens_despesa = ItemDespesa.query.filter_by(
        despesa_id=despesa.id
    ).order_by(
        ItemDespesa.id.asc()
    ).all()

    pastas = Pasta.query.order_by(
        Pasta.nome.asc()
    ).all()

    total_itens = sum(
        item.valor_total or 0
        for item in itens_despesa
    )

    diferenca = (despesa.valor or 0) - total_itens

    return render_template(
        "despesas/itens.html",
        despesa=despesa,
        itens=itens_despesa,
        pastas=pastas,
        total_itens=total_itens,
        diferenca=diferenca
    )


@itens.route("/<int:despesa_id>/itens/novo", methods=["POST"])
def novo(despesa_id):
    despesa = Despesa.query.get_or_404(despesa_id)

    descricao = request.form.get(
        "descricao",
        ""
    ).strip()

    try:
        quantidade = float(
            request.form.get("quantidade") or 1
        )

        valor_unitario = float(
            request.form.get("valor_unitario") or 0
        )

    except ValueError:
        flash("Quantidade ou valor inválido.", "danger")

        return redirect(
            url_for(
                "itens.lista",
                despesa_id=despesa.id
            )
        )

    pasta_id = request.form.get("pasta_id")

    if not descricao:
        flash("Informe o produto ou item.", "danger")

        return redirect(
            url_for(
                "itens.lista",
                despesa_id=despesa.id
            )
        )

    if quantidade <= 0:
        flash("A quantidade deve ser maior que zero.", "danger")

        return redirect(
            url_for(
                "itens.lista",
                despesa_id=despesa.id
            )
        )

    if valor_unitario < 0:
        flash("O valor unitário não pode ser negativo.", "danger")

        return redirect(
            url_for(
                "itens.lista",
                despesa_id=despesa.id
            )
        )

    if pasta_id:
        try:
            pasta_id = int(pasta_id)
        except ValueError:
            pasta_id = None
    else:
        pasta_id = None

    valor_total = quantidade * valor_unitario

    item = ItemDespesa(
        despesa_id=despesa.id,
        pasta_id=pasta_id,
        descricao=descricao,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
        valor_total=valor_total
    )

    db.session.add(item)
    db.session.commit()

    flash(
        f"Item '{descricao}' lançado com sucesso.",
        "success"
    )

    return redirect(
        url_for(
            "itens.lista",
            despesa_id=despesa.id
        )
    )


@itens.route("/itens/excluir/<int:item_id>")
def excluir(item_id):
    item = ItemDespesa.query.get_or_404(item_id)

    despesa_id = item.despesa_id

    db.session.delete(item)
    db.session.commit()

    flash(
        "Item excluído com sucesso.",
        "success"
    )

    return redirect(
        url_for(
            "itens.lista",
            despesa_id=despesa_id
        )
    )