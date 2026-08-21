from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date

from app import db
from .models import Receita


receitas = Blueprint(
    "receitas",
    __name__,
    url_prefix="/receitas"
)


@receitas.route("/")
def index():

    lista = Receita.query.order_by(
        Receita.data.desc()
    ).all()

    return render_template(
        "receitas/index.html",
        receitas=lista,
        today=date.today()
    )


@receitas.route("/nova", methods=["POST"])
def nova():

    descricao = request.form.get("descricao")
    valor = request.form.get("valor")

    if not descricao or not valor:
        return redirect(
            url_for("receitas.index")
        )

    receita = Receita(
        descricao=descricao,
        valor=float(valor),
        data=date.today(),
        usuario_id=1
    )

    db.session.add(receita)
    db.session.commit()

    return redirect(
        url_for("receitas.index")
    )


@receitas.route("/excluir/<int:id>")
def excluir(id):

    receita = Receita.query.get_or_404(id)

    db.session.delete(receita)
    db.session.commit()

    return redirect(
        url_for("receitas.index")
    )