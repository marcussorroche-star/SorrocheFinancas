from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from app import db
from .models import Financiamento


financiamentos = Blueprint(
    "financiamentos",
    __name__
)


@financiamentos.route("/")
def index():

    lista = Financiamento.query.order_by(
        Financiamento.data_inicio.desc()
    ).all()

    return render_template(
        "financiamentos/index.html",
        financiamentos=lista
    )


@financiamentos.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "GET":

        return render_template(
            "financiamentos/novo.html"
        )

    try:

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        valor_total_texto = request.form.get(
            "valor_total",
            "0"
        ).strip().replace(",", ".")

        entrada_texto = request.form.get(
            "entrada",
            "0"
        ).strip().replace(",", ".")

        valor_financiado_texto = request.form.get(
            "valor_financiado",
            "0"
        ).strip().replace(",", ".")

        quantidade_parcelas = int(
            request.form.get(
                "quantidade_parcelas",
                "1"
            )
        )

        valor_parcela_texto = request.form.get(
            "valor_parcela",
            "0"
        ).strip().replace(",", ".")

        juros_texto = request.form.get(
            "juros",
            "0"
        ).strip().replace(",", ".")

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

        parcelas_pagas = int(
            request.form.get(
                "parcelas_pagas",
                "0"
            )
        )

        valor_pago_texto = request.form.get(
            "valor_pago",
            "0"
        ).strip().replace(",", ".")

        status = request.form.get(
            "status",
            "Em aberto"
        ).strip()

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        valor_total = float(
            valor_total_texto or 0
        )

        entrada = float(
            entrada_texto or 0
        )

        valor_financiado = float(
            valor_financiado_texto or 0
        )

        valor_parcela = float(
            valor_parcela_texto or 0
        )

        juros = float(
            juros_texto or 0
        )

        valor_pago = float(
            valor_pago_texto or 0
        )

        if not descricao:

            flash(
                "Informe a descrição do financiamento.",
                "danger"
            )

            return redirect(
                url_for("financiamentos.novo")
            )

        if valor_total <= 0:

            flash(
                "Informe um valor total maior que zero.",
                "danger"
            )

            return redirect(
                url_for("financiamentos.novo")
            )

        if entrada < 0:

            entrada = 0

        if valor_financiado <= 0:

            valor_financiado = max(
                valor_total - entrada,
                0
            )

        if valor_financiado <= 0:

            flash(
                "O valor financiado deve ser maior que zero.",
                "danger"
            )

            return redirect(
                url_for("financiamentos.novo")
            )

        if not data_inicio_texto:

            flash(
                "Informe a data de início.",
                "danger"
            )

            return redirect(
                url_for("financiamentos.novo")
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

        if quantidade_parcelas <= 0:

            flash(
                "A quantidade de parcelas deve ser maior que zero.",
                "danger"
            )

            return redirect(
                url_for("financiamentos.novo")
            )

        if valor_parcela <= 0:

            valor_parcela = (
                valor_financiado / quantidade_parcelas
            )

        if parcelas_pagas < 0:

            parcelas_pagas = 0

        if parcelas_pagas > quantidade_parcelas:

            parcelas_pagas = quantidade_parcelas

        if valor_pago < 0:

            valor_pago = 0

        saldo_restante = max(
            valor_financiado - valor_pago,
            0
        )

        if saldo_restante <= 0:

            status = "Quitado"

        elif status == "Quitado":

            status = "Em aberto"

        financiamento = Financiamento(
            descricao=descricao,
            valor_total=valor_total,
            entrada=entrada,
            valor_financiado=valor_financiado,
            quantidade_parcelas=quantidade_parcelas,
            valor_parcela=valor_parcela,
            juros=juros,
            data_inicio=data_inicio,
            primeiro_vencimento=primeiro_vencimento,
            dia_vencimento=dia_vencimento,
            parcelas_pagas=parcelas_pagas,
            valor_pago=valor_pago,
            saldo_restante=saldo_restante,
            status=status or "Em aberto",
            observacao=observacao or None,
            usuario_id=1
        )

        db.session.add(
            financiamento
        )

        db.session.commit()

        flash(
            "Financiamento cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("financiamentos.index")
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao cadastrar financiamento: {erro}",
            "danger"
        )

        return redirect(
            url_for("financiamentos.novo")
        )


@financiamentos.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    financiamento = Financiamento.query.get_or_404(
        id
    )

    try:

        db.session.delete(
            financiamento
        )

        db.session.commit()

        flash(
            "Financiamento excluído com sucesso.",
            "success"
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao excluir financiamento: {erro}",
            "danger"
        )

    return redirect(
        url_for("financiamentos.index")
    )
