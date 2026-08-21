from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.pastas.models import Pasta


pastas = Blueprint(
    "pastas",
    __name__,
    url_prefix="/pastas"
)


CORES_VALIDAS = [
    "slate",
    "emerald",
    "amber",
    "rose",
    "sky",
    "violet"
]


@pastas.route("/")
def index():

    lista_pastas = Pasta.query.order_by(
        Pasta.nome.asc()
    ).all()

    return render_template(
        "pastas/index.html",
        pastas=lista_pastas,
        cores=CORES_VALIDAS
    )


@pastas.route("/nova", methods=["POST"])
def nova():

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    descricao = request.form.get(
        "descricao",
        ""
    ).strip()

    cor = request.form.get(
        "cor",
        "slate"
    ).strip()

    if not nome:

        flash(
            "Informe o nome da pasta.",
            "danger"
        )

        return redirect(
            url_for("pastas.index")
        )

    if cor not in CORES_VALIDAS:
        cor = "slate"

    pasta = Pasta(
        nome=nome,
        descricao=descricao or None,
        cor=cor
    )

    db.session.add(pasta)

    db.session.commit()

    flash(
        "Pasta criada com sucesso.",
        "success"
    )

    return redirect(
        url_for("pastas.index")
    )