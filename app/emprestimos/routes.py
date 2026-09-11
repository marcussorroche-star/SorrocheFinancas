from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from app import db
from .models import Emprestimo


emprestimos = Blueprint(
    "emprestimos",
    __name__
)


@emprestimos.route("/")
def index():

    lista = Emprestimo.query.order_by(
        Emprestimo.data_emprestimo.desc()
    ).all()

    return render_template(
        "emprestimos/index.html",
        emprestimos=lista
    )


@emprestimos.route("/novo", methods=["GET", "POST"])
def novo():

    if request.method == "GET":

        return render_template(
            "emprestimos/novo.html"
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

        valor_total = float(
            valor_total_texto or 0
        )

        data_emprestimo_texto = request.form.get(
            "data_emprestimo",
            ""
        ).strip()

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

        valor_parcela = float(
            valor_parcela_texto or 0
        )

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

        valor_pago = float(
            valor_pago_texto or 0
        )

        status = request.form.get(
            "status",
            "Em aberto"
        ).strip()

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        if not descricao:

            flash(
                "Informe a descrição do empréstimo.",
                "danger"
            )

            return redirect(
                url_for("emprestimos.novo")
            )

        if valor_total <= 0:

            flash(
                "Informe um valor total maior que zero.",
                "danger"
            )

            return redirect(
                url_for("emprestimos.novo")
            )

        if not data_emprestimo_texto:

            flash(
                "Informe a data do empréstimo.",
                "danger"
            )

            return redirect(
                url_for("emprestimos.novo")
            )

        data_emprestimo = date.fromisoformat(
            data_emprestimo_texto
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
                url_for("emprestimos.novo")
            )

        if valor_parcela <= 0:

            valor_parcela = (
                valor_total / quantidade_parcelas
            )

        if parcelas_pagas < 0:

            parcelas_pagas = 0

        if parcelas_pagas > quantidade_parcelas:

            parcelas_pagas = quantidade_parcelas

        if valor_pago < 0:

            valor_pago = 0

        saldo_restante = max(
            valor_total - valor_pago,
            0
        )

        if saldo_restante <= 0:

            status = "Quitado"

        elif status == "Quitado":

            status = "Em aberto"

        emprestimo = Emprestimo(
            descricao=descricao,
            valor_total=valor_total,
            data_emprestimo=data_emprestimo,
            quantidade_parcelas=quantidade_parcelas,
            valor_parcela=valor_parcela,
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
            emprestimo
        )

        db.session.commit()

        flash(
            "Empréstimo cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("emprestimos.index")
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao cadastrar empréstimo: {erro}",
            "danger"
        )

        return redirect(
            url_for("emprestimos.novo")
        )


@emprestimos.route(
    "/excluir/<int:id>",
    methods=["POST"]
)
def excluir(id):

    emprestimo = Emprestimo.query.get_or_404(
        id
    )

    try:

        db.session.delete(
            emprestimo
        )

        db.session.commit()

        flash(
            "Empréstimo excluído com sucesso.",
            "success"
        )

    except Exception as erro:

        db.session.rollback()

        flash(
            f"Erro ao excluir empréstimo: {erro}",
            "danger"
        )

    return redirect(
        url_for("emprestimos.index")
    )