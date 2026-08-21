from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from .models import Meta


metas = Blueprint(
    "metas",
    __name__,
    url_prefix="/metas"
)


@metas.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        valor_objetivo = request.form.get(
            "valor_objetivo",
            "0"
        ).replace(",", ".")

        valor_guardado = request.form.get(
            "valor_guardado",
            "0"
        ).replace(",", ".")

        prazo_meses = request.form.get(
            "prazo_meses",
            "1"
        )

        if not nome:

            flash(
                "Informe o nome da meta.",
                "danger"
            )

            return redirect(
                url_for("metas.index")
            )

        try:

            valor_objetivo = float(
                valor_objetivo or 0
            )

            valor_guardado = float(
                valor_guardado or 0
            )

            prazo_meses = int(
                prazo_meses or 1
            )

        except ValueError:

            flash(
                "Informe valores validos.",
                "danger"
            )

            return redirect(
                url_for("metas.index")
            )

        if valor_objetivo <= 0:

            flash(
                "O valor da meta deve ser maior que zero.",
                "danger"
            )

            return redirect(
                url_for("metas.index")
            )

        if prazo_meses <= 0:

            prazo_meses = 1

        if valor_guardado >= valor_objetivo:

            status = "Concluida"

        else:

            status = "Em andamento"

        meta = Meta(
            nome=nome,
            valor_objetivo=valor_objetivo,
            valor_guardado=valor_guardado,
            prazo_meses=prazo_meses,
            status=status,
            usuario_id=1
        )

        db.session.add(meta)
        db.session.commit()

        flash(
            "Meta cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for("metas.index")
        )

    lista = Meta.query.order_by(
        Meta.id.desc()
    ).all()

    dados = []

    for meta in lista:

        objetivo = float(
            meta.valor_objetivo or 0
        )

        guardado = float(
            meta.valor_guardado or 0
        )

        restante = max(
            0,
            objetivo - guardado
        )

        mensal = (
            restante / meta.prazo_meses
            if meta.prazo_meses > 0
            else restante
        )

        if objetivo > 0:

            percentual = (
                guardado / objetivo
            ) * 100

        else:

            percentual = 0

        percentual = max(
            0,
            min(100, percentual)
        )

        dados.append({
            "meta": meta,
            "restante": restante,
            "mensal": mensal,
            "percentual": percentual
        })

    return render_template(
        "metas/index.html",
        dados=dados
    )


@metas.route(
    "/<int:id>/excluir",
    methods=["POST"]
)
def excluir(id):

    meta = Meta.query.get_or_404(
        id
    )

    db.session.delete(meta)

    db.session.commit()

    flash(
        "Meta excluida.",
        "success"
    )

    return redirect(
        url_for("metas.index")
    )