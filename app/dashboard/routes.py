# app/dashboard/routes.py

from flask import Blueprint, render_template
from flask_login import login_required

from app.receitas.models import Receita
from app.despesas.models import Despesa
from app.cartoes.models import CompraCartao
from app.juros.models import Juro
from app.investimentos.models import Investimento
from app.metas.models import Meta


dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/")
@login_required
def home():

    # =========================================================
    # CARREGAMENTO DOS DADOS
    # =========================================================

    receitas = Receita.query.all()
    despesas = Despesa.query.all()
    compras = CompraCartao.query.all()
    juros = Juro.query.all()
    investimentos = Investimento.query.all()
    metas = Meta.query.all()

    # =========================================================
    # RECEITAS
    # =========================================================

    total_receitas = sum(
        (r.valor or 0)
        for r in receitas
    )

    # =========================================================
    # DESPESAS
    # =========================================================

    total_despesas = sum(
        (d.valor or 0)
        for d in despesas
    )

    # =========================================================
    # CARTÕES
    # =========================================================

    total_cartoes = sum(
        (c.valor or 0)
        for c in compras
    )

    # =========================================================
    # JUROS
    # =========================================================

    total_juros = sum(
        (j.valor or 0)
        for j in juros
    )

    # =========================================================
    # INVESTIMENTOS
    # =========================================================

    total_investido = sum(
        (i.valor_investido or 0)
        for i in investimentos
    )

    total_investimentos_atual = sum(
        (i.valor_atual or 0)
        for i in investimentos
    )

    resultado_investimentos = (
        total_investimentos_atual
        - total_investido
    )

    percentual_investimentos = 0

    if total_investido > 0:
        percentual_investimentos = (
            resultado_investimentos
            / total_investido
        ) * 100

    # =========================================================
    # SALDO
    #
    # IMPORTANTE:
    # Compras no cartão não são descontadas novamente aqui.
    # Quando uma fatura é paga, o módulo de cartões registra
    # o pagamento como uma Despesa.
    # =========================================================

    saldo = (
        total_receitas
        - total_despesas
        - total_juros
        - total_investido
    )

    # =========================================================
    # CARTÕES / FATURAS
    # =========================================================

    fatura_mes = 0
    proxima_fatura = 0

    for compra in compras:

        valor = compra.valor or 0
        parcelas = compra.parcelas or 1

        try:
            parcelas = int(parcelas)
        except (TypeError, ValueError):
            parcelas = 1

        if parcelas <= 0:
            parcelas = 1

        valor_parcela = valor / parcelas

        fatura_mes += valor_parcela

        if parcelas > 1:
            proxima_fatura += valor_parcela

    # =========================================================
    # METAS
    # =========================================================

    quantidade_metas = len(metas)

    metas_em_andamento = sum(
        1
        for meta in metas
        if meta.status == "Em andamento"
    )

    metas_concluidas = sum(
        1
        for meta in metas
        if meta.status in (
            "Concluida",
            "Concluída"
        )
    )

    total_metas_objetivo = sum(
        (meta.valor_objetivo or 0)
        for meta in metas
    )

    total_metas_guardado = sum(
        (meta.valor_guardado or 0)
        for meta in metas
    )

    percentual_metas = 0

    if total_metas_objetivo > 0:
        percentual_metas = (
            total_metas_guardado
            / total_metas_objetivo
        ) * 100

    percentual_metas = max(
        0,
        min(100, percentual_metas)
    )

    # =========================================================
    # PERCENTUAL DE DESPESAS
    # =========================================================

    percentual_despesas = 0

    if total_receitas > 0:
        percentual_despesas = (
            total_despesas
            / total_receitas
        ) * 100

    # =========================================================
    # PERCENTUAL DOS CARTÕES
    # =========================================================

    percentual_cartoes = 0

    if total_receitas > 0:
        percentual_cartoes = (
            total_cartoes
            / total_receitas
        ) * 100

    # =========================================================
    # IA FINANCEIRA
    # =========================================================

    ia_status = "azul"

    ia_titulo = (
        "Situação financeira positiva"
    )

    ia_mensagem = (
        "Continue acompanhando seus gastos, "
        "investimentos e metas."
    )

    if saldo < 0:

        ia_status = "vermelho"

        ia_titulo = (
            "Atenção: saldo negativo"
        )

        ia_mensagem = (
            f"Seu saldo está negativo em "
            f"R$ {abs(saldo):.2f}. "
            f"Suas receitas somam "
            f"R$ {total_receitas:.2f}. "
            "É importante reduzir gastos "
            "e acompanhar as próximas contas "
            "e faturas."
        )

    elif percentual_despesas >= 70:

        ia_status = "vermelho"

        ia_titulo = (
            "Atenção: despesas elevadas"
        )

        ia_mensagem = (
            f"Suas despesas representam "
            f"{percentual_despesas:.1f}% "
            "das suas receitas. "
            f"Seu saldo atual é de "
            f"R$ {saldo:.2f}. "
            "É recomendável controlar os gastos."
        )

    elif percentual_cartoes >= 40:

        ia_status = "amarelo"

        ia_titulo = (
            "Atenção aos cartões"
        )

        ia_mensagem = (
            f"Suas compras no cartão representam "
            f"{percentual_cartoes:.1f}% "
            "das suas receitas. "
            f"Seu saldo atual é de "
            f"R$ {saldo:.2f}. "
            "Fique atento às próximas faturas."
        )

    elif (
        total_receitas > 0
        and saldo < total_receitas * 0.20
    ):

        ia_status = "amarelo"

        ia_titulo = (
            "Atenção ao saldo"
        )

        ia_mensagem = (
            f"Seu saldo atual é de "
            f"R$ {saldo:.2f}. "
            "Isso representa aproximadamente "
            f"{(saldo / total_receitas) * 100:.1f}% "
            "das suas receitas. "
            "Procure manter uma reserva financeira."
        )

    else:

        resultado_texto = (
            "positivo"
            if resultado_investimentos >= 0
            else "negativo"
        )

        ia_mensagem = (
            f"Suas receitas somam "
            f"R$ {total_receitas:.2f} "
            f"e seu saldo atual é de "
            f"R$ {saldo:.2f}. "
            "Seus investimentos apresentam "
            f"resultado {resultado_texto} de "
            f"R$ {abs(resultado_investimentos):.2f}. "
        )

        if metas_em_andamento > 0:

            ia_mensagem += (
                f"Você possui "
                f"{metas_em_andamento} "
                "meta(s) em andamento, "
                f"com {percentual_metas:.1f}% "
                "do valor total das metas "
                "já guardado. "
            )

        ia_mensagem += (
            "Continue acompanhando seus gastos, "
            "investimentos e metas."
        )

    # =========================================================
    # DADOS DO GRÁFICO
    # =========================================================

    dados_grafico = [
        {
            "categoria": "Receitas",
            "valor": total_receitas
        },
        {
            "categoria": "Despesas",
            "valor": total_despesas
        },
        {
            "categoria": "Cartões",
            "valor": total_cartoes
        },
        {
            "categoria": "Juros",
            "valor": total_juros
        },
        {
            "categoria": "Investimentos",
            "valor": total_investido
        }
    ]

    # =========================================================
    # DASHBOARD
    # =========================================================

    return render_template(
        "dashboard.html",

        total_receitas=total_receitas,
        total_despesas=total_despesas,
        total_cartoes=total_cartoes,
        total_juros=total_juros,

        total_investido=total_investido,

        total_investimentos_atual=(
            total_investimentos_atual
        ),

        resultado_investimentos=(
            resultado_investimentos
        ),

        percentual_investimentos=(
            percentual_investimentos
        ),

        saldo=saldo,

        quantidade_cartoes=len(compras),

        quantidade_investimentos=(
            len(investimentos)
        ),

        fatura_mes=fatura_mes,

        proxima_fatura=proxima_fatura,

        dados_grafico=dados_grafico,

        quantidade_metas=quantidade_metas,

        metas_em_andamento=(
            metas_em_andamento
        ),

        metas_concluidas=(
            metas_concluidas
        ),

        total_metas_objetivo=(
            total_metas_objetivo
        ),

        total_metas_guardado=(
            total_metas_guardado
        ),

        percentual_metas=percentual_metas,

        percentual_despesas=(
            percentual_despesas
        ),

        percentual_cartoes=(
            percentual_cartoes
        ),

        ia_status=ia_status,

        ia_titulo=ia_titulo,

        ia_mensagem=ia_mensagem
    )