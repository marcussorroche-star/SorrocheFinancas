from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime

from app import db
from .models import Cartao, CompraCartao, FaturaPaga
from app.despesas.models import Despesa


cartoes = Blueprint(
    "cartoes",
    __name__,
    url_prefix="/cartoes"
)


def adicionar_meses(data, meses):
    ano = data.year
    mes = data.month + meses

    while mes > 12:
        mes -= 12
        ano += 1

    while mes < 1:
        mes += 12
        ano -= 1

    return date(ano, mes, 1)


def normalizar_ultimos4(valor):
    """
    Mantém somente números e pega os últimos 4.
    Exemplo:
    1234 -> 1234
    **** 1234 -> 1234
    5123 4567 1234 -> 1234
    """
    valor = str(valor or "").strip()

    somente_numeros = "".join(
        caractere
        for caractere in valor
        if caractere.isdigit()
    )

    if not somente_numeros:
        return ""

    return somente_numeros[-4:]


@cartoes.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        ultimos4 = normalizar_ultimos4(
            request.form.get(
                "ultimos4",
                ""
            )
        )

        limite = request.form.get(
            "limite",
            "0"
        ).replace(",", ".")

        dia_abertura = request.form.get(
            "dia_abertura",
            "1"
        )

        dia_fechamento = request.form.get(
            "dia_fechamento",
            "1"
        )

        dia_vencimento = request.form.get(
            "dia_vencimento",
            "1"
        )

        if nome:

            try:

                if ultimos4:

                    cartao_existente = Cartao.query.filter_by(
                        ultimos4=ultimos4,
                        usuario_id=1
                    ).first()

                    if cartao_existente:

                        flash(
                            f"Já existe um cartão cadastrado "
                            f"com os últimos 4 números {ultimos4}.",
                            "danger"
                        )

                        return redirect(
                            url_for("cartoes.index")
                        )

                cartao = Cartao(
                    nome=nome,
                    ultimos4=ultimos4 or None,
                    limite=float(limite or 0),
                    dia_abertura=int(
                        dia_abertura or 1
                    ),
                    dia_fechamento=int(
                        dia_fechamento or 1
                    ),
                    dia_vencimento=int(
                        dia_vencimento or 1
                    ),
                    status="Ativo",
                    usuario_id=1
                )

                db.session.add(cartao)
                db.session.commit()

                flash(
                    "Cartão cadastrado com sucesso.",
                    "success"
                )

            except Exception as erro:

                db.session.rollback()

                flash(
                    f"Erro ao cadastrar cartão: {erro}",
                    "danger"
                )

        return redirect(
            url_for("cartoes.index")
        )

    cartoes_lista = Cartao.query.order_by(
        Cartao.id.asc()
    ).all()

    hoje = date.today()

    inicio_mes_atual = date(
        hoje.year,
        hoje.month,
        1
    )

    inicio_proximo_mes = adicionar_meses(
        inicio_mes_atual,
        1
    )

    mes_atual = inicio_mes_atual.strftime(
        "%Y-%m"
    )

    mes_proximo = inicio_proximo_mes.strftime(
        "%Y-%m"
    )

    dados = []

    for cartao in cartoes_lista:

        compras = CompraCartao.query.filter_by(
            cartao_id=cartao.id
        ).order_by(
            CompraCartao.data_compra.desc()
        ).all()

        faturas = FaturaPaga.query.filter_by(
            cartao_id=cartao.id
        ).order_by(
            FaturaPaga.data_pagamento.desc()
        ).all()

        pagamentos_por_mes = {}

        for fatura in faturas:

            mes = fatura.mes

            pagamentos_por_mes[mes] = (
                pagamentos_por_mes.get(
                    mes,
                    0.0
                )
                + float(fatura.valor or 0)
            )

        fatura_atual = 0.0
        fatura_proximo_mes = 0.0
        total_comprometido = 0.0

        for compra in compras:

            valor_total = float(
                compra.valor or 0
            )

            parcelas = int(
                compra.parcelas or 1
            )

            if parcelas < 1:
                parcelas = 1

            valor_parcela = (
                valor_total / parcelas
            )

            total_comprometido += valor_total

            data_compra = compra.data_compra

            if not data_compra:
                data_compra = hoje

            for numero_parcela in range(
                1,
                parcelas + 1
            ):

                data_parcela = adicionar_meses(
                    data_compra,
                    numero_parcela - 1
                )

                mes_parcela = data_parcela.strftime(
                    "%Y-%m"
                )

                if mes_parcela == mes_atual:

                    fatura_atual += valor_parcela

                elif mes_parcela == mes_proximo:

                    fatura_proximo_mes += valor_parcela

        valor_pago_atual = pagamentos_por_mes.get(
            mes_atual,
            0.0
        )

        fatura_restante = max(
            0.0,
            fatura_atual - valor_pago_atual
        )

        limite = float(
            cartao.limite or 0
        )

        disponivel = (
            limite - total_comprometido
        )

        dados.append({
            "cartao": cartao,
            "compras": compras,
            "total_usado": total_comprometido,
            "disponivel": disponivel,
            "fatura_atual": fatura_restante,
            "fatura_bruta_atual": fatura_atual,
            "fatura_paga_atual": valor_pago_atual,
            "proxima_fatura": fatura_proximo_mes,
            "faturas": faturas
        })

    return render_template(
        "cartoes/index.html",
        dados=dados
    )


@cartoes.route(
    "/<int:cartao_id>/compra",
    methods=["GET", "POST"]
)
def nova_compra(cartao_id):

    cartao = Cartao.query.get_or_404(
        cartao_id
    )

    if request.method == "GET":

        return redirect(
            url_for("cartoes.index")
        )

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
    ).replace(",", ".")

    parcelas_texto = request.form.get(
        "parcelas",
        "1"
    )

    data_compra_texto = request.form.get(
        "data_compra",
        ""
    ).strip()

    try:

        valor = float(
            valor_texto or 0
        )

        parcelas = int(
            parcelas_texto or 1
        )

    except ValueError:

        flash(
            "Valor ou parcelas inválidos.",
            "danger"
        )

        return redirect(
            url_for("cartoes.index")
        )

    if not descricao:

        flash(
            "Informe a descrição da compra.",
            "danger"
        )

        return redirect(
            url_for("cartoes.index")
        )

    if valor <= 0:

        flash(
            "Informe um valor maior que zero.",
            "danger"
        )

        return redirect(
            url_for("cartoes.index")
        )

    if parcelas < 1:
        parcelas = 1

    data_compra = date.today()

    if data_compra_texto:

        try:

            data_compra = datetime.strptime(
                data_compra_texto,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Data da compra inválida.",
                "danger"
            )

            return redirect(
                url_for("cartoes.index")
            )

    compra = CompraCartao(
        cartao_id=cartao.id,
        descricao=descricao,
        categoria=categoria or "Outros",
        valor=valor,
        data_compra=data_compra,
        parcelas=parcelas
    )

    db.session.add(compra)
    db.session.commit()

    flash(
        "Compra adicionada ao cartão.",
        "success"
    )

    return redirect(
        url_for("cartoes.index")
    )


@cartoes.route(
    "/compra/<int:compra_id>/cancelar",
    methods=["POST"]
)
def cancelar_compra(compra_id):

    compra = CompraCartao.query.get_or_404(
        compra_id
    )

    db.session.delete(compra)
    db.session.commit()

    flash(
        "Compra cancelada.",
        "success"
    )

    return redirect(
        url_for("cartoes.index")
    )


@cartoes.route(
    "/<int:cartao_id>/cancelar",
    methods=["POST"]
)
def cancelar_cartao(cartao_id):

    cartao = Cartao.query.get_or_404(
        cartao_id
    )

    cartao.status = "Cancelado"

    db.session.commit()

    flash(
        "Cartão cancelado.",
        "success"
    )

    return redirect(
        url_for("cartoes.index")
    )


@cartoes.route(
    "/<int:cartao_id>/excluir",
    methods=["POST"]
)
def excluir(cartao_id):

    cartao = Cartao.query.get_or_404(
        cartao_id
    )

    compras = CompraCartao.query.filter_by(
        cartao_id=cartao.id
    ).all()

    for compra in compras:
        db.session.delete(compra)

    faturas = FaturaPaga.query.filter_by(
        cartao_id=cartao.id
    ).all()

    for fatura in faturas:
        db.session.delete(fatura)

    db.session.delete(cartao)

    db.session.commit()

    flash(
        "Cartão excluído.",
        "success"
    )

    return redirect(
        url_for("cartoes.index")
    )


@cartoes.route(
    "/<int:cartao_id>/pagar-fatura",
    methods=["POST"]
)
def pagar_fatura(cartao_id):

    cartao = Cartao.query.get_or_404(
        cartao_id
    )

    valor_texto = request.form.get(
        "valor",
        "0"
    ).replace(",", ".")

    try:

        valor = float(
            valor_texto or 0
        )

    except ValueError:

        valor = 0

    if valor <= 0:

        flash(
            "Informe um valor válido para pagar a fatura.",
            "danger"
        )

        return redirect(
            url_for("cartoes.index")
        )

    hoje = date.today()

    fatura = FaturaPaga(
        cartao_id=cartao.id,
        mes=hoje.strftime("%Y-%m"),
        valor=valor,
        data_pagamento=hoje
    )

    db.session.add(fatura)

    despesa = Despesa(
        descricao=f"Fatura cartão - {cartao.nome}",
        categoria="Cartão",
        valor=valor,
        data=hoje,
        vencimento=hoje,
        forma_pagamento="Cartão",
        status="Pago",
        usuario_id=1
    )

    db.session.add(despesa)

    db.session.commit()

    flash(
        "Fatura paga e registrada nas despesas.",
        "success"
    )

    return redirect(
        url_for("cartoes.index")
    )