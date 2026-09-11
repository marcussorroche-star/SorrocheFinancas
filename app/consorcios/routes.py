from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from app import db
from .models import Consorcio


consorcios = Blueprint(
    "consorcios",
    __name__
)


@consorcios.route("/")
def index():

    lista = Consorcio.query.order_by(
        Consorcio.data_inicio.desc()
    ).all()

    return render_template(
        "consorcios/index.html",
        consorcios=lista
    )


@consorcios.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "GET":

        return render_template(
            "consorcios/novo.html"
        )

    try:

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        administradora = request.form.get(
            "administradora",
            ""
        ).strip()

        tipo = request.form.get(
            "tipo",
            ""
        ).strip()

        valor_carta = float(
            request.form.get(
                "valor_carta",
                "0"
            ).strip().replace(",", ".") or 0
        )

        valor_entrada = float(
            request.form.get(
                "valor_entrada",
                "0"
            ).strip().replace(",", ".") or 0
        )

        quantidade_parcelas = int(
            request.form.get(
                "quantidade_parcelas",
                "1"
            )
        )

        valor_parcela = float(
            request.form.get(
                "valor_parcela",
                "0"
            ).strip().replace(",", ".") or 0
        )

        parcelas_pagas = int(
            request.form.get(
                "parcelas_pagas",
                "0"
            )
        )

        valor_pago = float(
            request.form.get(
                "valor_pago",
                "0"
            ).strip().replace(",", ".") or 0
        )

        data_inicio_texto = request.form.get(
            "data_inicio",
            ""
        ).strip()

        primeiro_vencimento_texto = request.form.get(
            "primeiro_vencimento",
            ""
        ).strip()

        dia_vencimento_texto = request.form.get(
            "dia_vencimento",
            ""
        ).strip()

        contem_lance = (
            request.form.get("contem_lance") == "on"
        )

        valor_lance = float(
            request.form.get(
                "valor_lance",
                "0"
            ).strip().replace(",", ".") or 0
        )

        contemplado = (
            request.form.get("contemplado") == "on"
        )

        data_contemplacao_texto = request.form.get(
            "data_contemplacao",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Em andamento"
        ).strip()

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        if not descricao:

            flash(
                "Informe a descrição do consórcio.",
                "danger"
            )

            return redirect(
                url_for("consorcios.novo")
            )

        if valor_carta <= 0:

            flash(
                "Informe um valor de carta maior que zero.",
                "danger"
            )

            return redirect(
                url_for("consorcios.novo")
            )

        if quantidade_parcelas <= 0:

            flash(
                "A quantidade de parcelas deve ser maior que zero.",
                "danger"
            )

            return redirect(
                url_for("consorcios.novo")
            )

        if not data_inicio_texto:

            flash(
                "Informe a data de início.",
                "danger"
            )

            return redirect(
                url_for("consorcios.novo")
            )

        data_inicio = date.fromisoformat(
            data_inicio_texto
        )

        primeiro_vencimento = None

        if primeiro_vencimento_texto:

            primeiro_vencimento = date.fromisoformat(
                primeiro_vencimento_texto
            )

        dia_vencimento = None

        if dia_vencimento_texto:

            dia_vencimento = int(
                dia_vencimento_texto
            )

            if dia_vencimento < 1 or dia_vencimento > 31:

                flash(
                    "O dia de vencimento deve estar entre 1 e 31.",
                    "danger"
                )

                return redirect(
                    url_for("consorcios.novo")
                )

        if valor_parcela <= 0:

            valor_parcela = (
                valor_carta / quantidade_parcelas
            )

        if parcelas_pagas < 0:

            parcelas_pagas = 0

        if parcelas_pagas > quantidade_parcelas:

            parcelas_pagas = quantidade_parcelas

        if valor_pago < 0:

            valor_pago = 0

        if valor_entrada < 0:

            valor_entrada = 0

        if valor_lance < 0:

            valor_lance = 0

        data_contemplacao = None

        if data_contemplacao_texto:

            data_contemplacao = date.fromisoformat(
                data_contemplacao_texto
            )

        saldo_restante = max(
            (quantidade_parcelas * valor_parcela) - valor_pago,
            0
        )

        if parcelas_pagas >= quantidade_parcelas:

            status = "Quitado"

        elif status == "Quitado":

            status = "Em andamento"

        consorcio = Consorcio(
            descricao=descricao,
            administradora=administradora or None,
            tipo=tipo or None,
            valor_carta=valor_carta,
            valor_entrada=valor_entrada,
            quantidade_parcelas=quantidade_parcelas,
            valor_parcela=valor_parcela,
            parcelas_pagas=parcelas_pagas,
            valor_pago=valor_pago,
            saldo_restante=saldo_restante,
            data_inicio=data_inicio,
            primeiro_vencimento=primeiro_vencimento,
            dia_vencimento=dia_vencimento,
            contem_lance=contem_lance,
            valor_lance=valor_lance,
            contemplado=contemplado,
            data_contemplacao=data_contemplacao,
            status=status or "Em andamento",
            observacao=observacao or None,
            usuario_id=1
        )

        db.session.add(
            consorcio
        )

        db.session.commit()

        flash(
            "Consórcio cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("consorcios.index")
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao cadastrar consórcio: {erro}",
            "danger"
        )

        return redirect(
            url_for("consorcios.novo")
        )


@consorcios.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    consorcio = Consorcio.query.get_or_404(
        id
    )

    try:

        db.session.delete(
            consorcio
        )

        db.session.commit()

        flash(
            "Consórcio excluído com sucesso.",
            "success"
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao excluir consórcio: {erro}",
            "danger"
        )

    return redirect(
        url_for("consorcios.index")
    )
