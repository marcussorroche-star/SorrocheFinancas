from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.estoque.models import ItemEstoque
from app.pastas.models import Pasta


estoque = Blueprint(
    "estoque",
    __name__,
    url_prefix="/estoque"
)


# ============================================================
# LISTAR ESTOQUE
# ============================================================

@estoque.route("/", methods=["GET"])
def index():

    itens = ItemEstoque.query.order_by(
        ItemEstoque.nome.asc()
    ).all()

    pastas = Pasta.query.order_by(
        Pasta.nome.asc()
    ).all()

    total_estoque = sum(
        float(item.valor_total or 0)
        for item in itens
        if item.tipo == "entrada"
    )

    quantidade_itens = sum(
        float(item.quantidade or 0)
        for item in itens
        if item.tipo == "entrada"
    )

    return render_template(
        "estoque/index.html",
        itens=itens,
        pastas=pastas,
        total_estoque=total_estoque,
        quantidade_itens=quantidade_itens
    )


# ============================================================
# ADICIONAR ITEM
# ============================================================

@estoque.route("/adicionar", methods=["POST"])
def adicionar():

    nome = str(
        request.form.get("nome", "")
    ).strip()

    quantidade_texto = str(
        request.form.get("quantidade", "1")
    ).strip()

    valor_texto = str(
        request.form.get("valor_unitario", "0")
    ).strip()

    pasta_id = request.form.get(
        "pasta_id"
    )

    observacao = str(
        request.form.get("observacao", "")
    ).strip()

    if not nome:

        flash(
            "Informe o nome do item.",
            "danger"
        )

        return redirect(
            url_for("estoque.index")
        )

    try:

        quantidade = float(
            quantidade_texto.replace(
                ",",
                "."
            )
        )

        valor_unitario = float(
            valor_texto
            .replace(
                "R$",
                ""
            )
            .replace(
                ".",
                ""
            )
            .replace(
                ",",
                "."
            )
            .strip()
        )

    except ValueError:

        flash(
            "Quantidade ou valor inválido.",
            "danger"
        )

        return redirect(
            url_for("estoque.index")
        )

    if quantidade <= 0:

        flash(
            "A quantidade deve ser maior que zero.",
            "danger"
        )

        return redirect(
            url_for("estoque.index")
        )

    if valor_unitario < 0:

        flash(
            "O valor unitário não pode ser negativo.",
            "danger"
        )

        return redirect(
            url_for("estoque.index")
        )

    pasta = None

    if pasta_id:

        try:

            pasta = Pasta.query.get(
                int(pasta_id)
            )

        except (
            TypeError,
            ValueError
        ):

            pasta = None

    item = ItemEstoque(
        nome=nome,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
        valor_total=(
            quantidade
            * valor_unitario
        ),
        pasta_id=(
            pasta.id
            if pasta
            else None
        ),
        data=date.today(),
        tipo="entrada",
        observacao=(
            observacao
            or None
        )
    )

    db.session.add(
        item
    )

    db.session.commit()

    flash(
        f"Item '{nome}' adicionado ao estoque.",
        "success"
    )

    return redirect(
        url_for("estoque.index")
    )


# ============================================================
# EXCLUIR ITEM
# ============================================================

@estoque.route(
    "/excluir/<int:item_id>",
    methods=["POST"]
)
def excluir(item_id):

    item = ItemEstoque.query.get_or_404(
        item_id
    )

    db.session.delete(
        item
    )

    db.session.commit()

    flash(
        "Item removido do estoque.",
        "success"
    )

    return redirect(
        url_for("estoque.index")
    )