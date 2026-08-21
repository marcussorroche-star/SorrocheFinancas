from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date

from app import db
from .models import Juro


juros = Blueprint(
    "juros",
    __name__,
    url_prefix="/juros"
)


@juros.route("/")
def index():

    lista = Juro.query.order_by(
        Juro.data.desc()
    ).all()

    return render_template(
        "juros/index.html",
        juros=lista
    )


@juros.route("/nova", methods=["POST"])
def nova():

    novo_juro = Juro(

        descricao=request.form.get("descricao"),

        categoria=request.form.get("categoria"),

        valor=float(
            request.form.get("valor")
        ),

        data=date.today(),

        usuario_id=1
    )

    db.session.add(novo_juro)

    db.session.commit()

    return redirect(
        url_for("juros.index")
    )


@juros.route("/excluir/<int:id>")
def excluir(id):

    juro = Juro.query.get_or_404(id)

    db.session.delete(juro)

    db.session.commit()

    return redirect(
        url_for("juros.index")
    )