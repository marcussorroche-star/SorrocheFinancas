from datetime import date

from app import db
from app.receitas.models import Receita
from app.despesas.models import Despesa
from app.cartoes.models import Cartao, CompraCartao, FaturaPaga
from app.metas.models import Meta
from app.investimentos.models import Investimento


# ============================================================
# CONFIGURAÇÃO DA REGRA FINANCEIRA
# ============================================================

# TETO MÁXIMO PARA GASTOS
LIMITE_GASTOS = 2000.00

# LIMITE MÁXIMO DA RESERVA DE EMERGÊNCIA
LIMITE_RESERVA_EMERGENCIA = 3000.00

# LIMITE MÁXIMO DA RESERVA DE GASTOS
LIMITE_RESERVA_GASTOS = 3000.00

# Mantidos para compatibilidade com o sistema.
VALOR_META_MENSAL = 1000.00
VALOR_FUNDO_RESERVA_MENSAL = 6000.00
VALOR_FUNDO_DESPESAS_MENSAL = 1500.00


# ============================================================
# AUXILIAR
# ============================================================

def adicionar_meses(data, meses):

    ano = data.year
    mes = data.month + meses

    while mes > 12:
        mes -= 12
        ano += 1

    while mes < 1:
        mes += 12
        ano -= 1

    return date(
        ano,
        mes,
        1
    )


# ============================================================
# IDENTIFICAR MÊS
# ============================================================

def obter_periodo(ano=None, mes=None):

    hoje = date.today()

    ano = ano or hoje.year
    mes = mes or hoje.month

    inicio = date(
        ano,
        mes,
        1
    )

    inicio_proximo = adicionar_meses(
        inicio,
        1
    )

    return (
        inicio,
        inicio_proximo
    )


# ============================================================
# RECEITAS DO MÊS
# ============================================================

def calcular_receitas_mes(
    ano,
    mes
):

    receitas = Receita.query.filter(
        db.extract(
            "year",
            Receita.data
        ) == ano,

        db.extract(
            "month",
            Receita.data
        ) == mes
    ).all()

    return sum(
        float(receita.valor or 0)
        for receita in receitas
    )


# ============================================================
# DESPESAS FIXAS
# ============================================================

def calcular_despesas_fixas(
    ano,
    mes
):

    despesas = Despesa.query.filter(
        db.extract(
            "year",
            Despesa.data
        ) == ano,

        db.extract(
            "month",
            Despesa.data
        ) == mes
    ).all()

    total = 0.0

    for despesa in despesas:

        categoria = str(
            despesa.categoria or ""
        ).strip().lower()

        forma = str(
            despesa.forma_pagamento or ""
        ).strip().lower()

        # A fatura do cartão é calculada separadamente.
        if categoria == "cartão":
            continue

        if forma == "cartão":
            continue

        if despesa.status != "Pago":
            continue

        total += float(
            despesa.valor or 0
        )

    return total


# ============================================================
# FATURA DO CARTÃO DO MÊS
# ============================================================

def calcular_fatura_cartao_mes(
    ano,
    mes
):

    inicio_mes = date(
        ano,
        mes,
        1
    )

    cartoes = Cartao.query.all()

    total_fatura = 0.0

    for cartao in cartoes:

        compras = CompraCartao.query.filter_by(
            cartao_id=cartao.id
        ).all()

        faturas_pagas = FaturaPaga.query.filter_by(
            cartao_id=cartao.id,
            mes=inicio_mes.strftime("%Y-%m")
        ).all()

        valor_bruto = 0.0

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

            data_compra = (
                compra.data_compra
                or inicio_mes
            )

            for numero_parcela in range(
                1,
                parcelas + 1
            ):

                data_parcela = adicionar_meses(
                    data_compra,
                    numero_parcela - 1
                )

                if (
                    data_parcela.year == ano
                    and data_parcela.month == mes
                ):

                    valor_bruto += valor_parcela

        valor_pago = sum(
            float(fatura.valor or 0)
            for fatura in faturas_pagas
        )

        valor_restante = max(
            0.0,
            valor_bruto - valor_pago
        )

        total_fatura += valor_restante

    return total_fatura


# ============================================================
# LOCALIZAR META
# ============================================================

def encontrar_meta(nome):

    return Meta.query.filter(
        db.func.lower(
            Meta.nome
        ) == nome.lower()
    ).first()


# ============================================================
# VERIFICAR META ATINGIDA
# ============================================================

def meta_atingida(meta):

    if not meta:
        return False

    objetivo = float(
        meta.valor_objetivo or 0
    )

    guardado = float(
        meta.valor_guardado or 0
    )

    if objetivo <= 0:
        return False

    return guardado >= objetivo


# ============================================================
# INVESTIMENTOS EXISTENTES
# ============================================================

def calcular_investimentos():

    investimentos = Investimento.query.all()

    return sum(
        float(
            investimento.valor_atual
            or investimento.valor_investido
            or 0
        )
        for investimento in investimentos
    )


# ============================================================
# REGRA MENSAL COMPLETA
# ============================================================

def calcular_regra_mensal(
    ano=None,
    mes=None
):

    hoje = date.today()

    ano = ano or hoje.year
    mes = mes or hoje.month

    # ========================================================
    # RECEITAS
    # ========================================================

    receitas = calcular_receitas_mes(
        ano,
        mes
    )

    # ========================================================
    # DESPESAS FIXAS
    # ========================================================

    despesas_fixas = calcular_despesas_fixas(
        ano,
        mes
    )

    # ========================================================
    # FATURA DO CARTÃO
    # ========================================================

    fatura_cartao = calcular_fatura_cartao_mes(
        ano,
        mes
    )

    # ========================================================
    # DINHEIRO DISPONÍVEL
    # ========================================================

    disponivel = max(
        0.0,
        receitas
        - despesas_fixas
        - fatura_cartao
    )

    # ========================================================
    # METAS EXISTENTES
    # ========================================================

    meta = encontrar_meta(
        "Meta"
    )

    meta_atingida_flag = meta_atingida(
        meta
    )

    fundo_reserva = encontrar_meta(
        "Fundo de Reserva"
    )

    fundo_reserva_atingido = meta_atingida(
        fundo_reserva
    )

    fundo_despesas = encontrar_meta(
        "Fundo de Despesas"
    )

    fundo_despesas_atingido = meta_atingida(
        fundo_despesas
    )

    # ========================================================
    # REGRA PRINCIPAL
    #
    # O dinheiro disponível é dividido em 3 grupos:
    #
    # 1 - GASTOS
    # 2 - RESERVA DE EMERGÊNCIA
    # 3 - RESERVA DE GASTOS
    #
    # GASTOS:
    # máximo de R$ 2.000
    #
    # RESERVAS:
    # recebem o restante em partes iguais.
    #
    # Quando uma reserva atingir seu limite,
    # o restante vai para a outra reserva.
    #
    # Quando as duas atingirem seus limites,
    # o restante vai para META.
    # ========================================================

    restante = max(
        0.0,
        disponivel
    )

    # ========================================================
    # 1 - GASTOS
    # ========================================================

    if LIMITE_GASTOS is None:

        valor_para_gastos = restante / 3.0

    else:

        limite_gastos = max(
            0.0,
            float(LIMITE_GASTOS)
        )

        valor_inicial_terco = (
            restante / 3.0
        )

        valor_para_gastos = min(
            valor_inicial_terco,
            limite_gastos
        )

    restante_apos_gastos = max(
        0.0,
        restante - valor_para_gastos
    )

    # ========================================================
    # 2 E 3 - RESERVAS
    # ========================================================
    #
    # Se o dinheiro for menor que R$ 6.000,
    # as reservas recebem partes iguais.
    #
    # Exemplo:
    #
    # R$ 3.090
    #
    # Gastos = 1.030
    # Emergência = 1.030
    # Reserva gastos = 1.030
    #
    # Se o disponível for R$ 9.000:
    #
    # Gastos = 2.000
    #
    # Sobram R$ 7.000.
    #
    # As reservas dividem os R$ 7.000:
    #
    # Emergência = 3.000
    # Reserva gastos = 3.000
    #
    # Sobram R$ 1.000 para META.
    # ========================================================

    limite_emergencia = max(
        0.0,
        float(LIMITE_RESERVA_EMERGENCIA)
    )

    limite_reserva_gastos = max(
        0.0,
        float(LIMITE_RESERVA_GASTOS)
    )

    # ========================================================
    # RESERVA DE EMERGÊNCIA
    # ========================================================

    if fundo_reserva_atingido:

        valor_reserva_emergencia = 0.0

    else:

        valor_reserva_emergencia = min(
            restante_apos_gastos / 2.0,
            limite_emergencia
        )

    # ========================================================
    # RESTANTE APÓS RESERVA DE EMERGÊNCIA
    # ========================================================

    restante_apos_emergencia = max(
        0.0,
        restante_apos_gastos
        - valor_reserva_emergencia
    )

    # ========================================================
    # RESERVA DE GASTOS
    # ========================================================

    if fundo_despesas_atingido:

        valor_reserva_gastos = 0.0

    else:

        valor_reserva_gastos = min(
            restante_apos_emergencia,
            limite_reserva_gastos
        )

    # ========================================================
    # RESTANTE APÓS AS RESERVAS
    # ========================================================

    restante_apos_reservas = max(
        0.0,
        restante_apos_emergencia
        - valor_reserva_gastos
    )

    # ========================================================
    # META
    # ========================================================
    #
    # Tudo que ultrapassar os limites das duas reservas
    # vai para a Meta.
    #
    # Se a Meta já estiver atingida, mantemos o valor
    # no resultado para não perder o fechamento.
    # ========================================================

    valor_meta = restante_apos_reservas

    # ========================================================
    # FUNDO DE DESPESAS ANTIGO
    # ========================================================
    #
    # Mantido para compatibilidade com as telas existentes.
    # A nova regra utiliza "Reserva de Gastos".
    # ========================================================

    valor_fundo_despesas = 0.0

    # ========================================================
    # INVESTIMENTOS
    # ========================================================

    investimentos_mes = 0.0

    # ========================================================
    # CORREÇÃO DE CENTAVOS
    # ========================================================

    total_destinado = (
        valor_para_gastos
        + valor_reserva_emergencia
        + valor_reserva_gastos
        + valor_meta
        + valor_fundo_despesas
        + investimentos_mes
    )

    diferenca = (
        disponivel
        - total_destinado
    )

    if abs(diferenca) > 0.0001:

        valor_meta += diferenca

        if valor_meta < 0:

            valor_meta = 0.0

    # ========================================================
    # TOTAL FINAL
    # ========================================================

    total_destinado = (
        valor_para_gastos
        + valor_reserva_emergencia
        + valor_reserva_gastos
        + valor_meta
        + valor_fundo_despesas
        + investimentos_mes
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {

        "ano": ano,

        "mes": mes,

        "receitas": round(
            receitas,
            2
        ),

        "despesas_fixas": round(
            despesas_fixas,
            2
        ),

        "fatura_cartao": round(
            fatura_cartao,
            2
        ),

        "disponivel": round(
            disponivel,
            2
        ),

        "limite_gastos": (
            None
            if LIMITE_GASTOS is None
            else round(
                float(LIMITE_GASTOS),
                2
            )
        ),

        # ====================================================
        # GASTOS
        # ====================================================

        "para_gastos": round(
            valor_para_gastos,
            2
        ),

        # ====================================================
        # RESERVA DE EMERGÊNCIA
        # ====================================================

        "reserva_emergencia": round(
            valor_reserva_emergencia,
            2
        ),

        # ====================================================
        # RESERVA DE GASTOS
        # ====================================================

        "reserva_gastos": round(
            valor_reserva_gastos,
            2
        ),

        # ====================================================
        # META
        # ====================================================

        "meta": round(
            valor_meta,
            2
        ),

        # ====================================================
        # COMPATIBILIDADE COM TELAS ANTIGAS
        # ====================================================

        "fundo_reserva": round(
            valor_reserva_emergencia,
            2
        ),

        "fundo_despesas": round(
            valor_fundo_despesas,
            2
        ),

        "investimentos_mes": round(
            investimentos_mes,
            2
        ),

        "investimentos_total": round(
            calcular_investimentos(),
            2
        ),

        "meta_atingida": meta_atingida_flag,

        "fundo_reserva_atingido":
            fundo_reserva_atingido,

        "fundo_despesas_atingido":
            fundo_despesas_atingido,

        "total_destinado": round(
            total_destinado,
            2
        )
    }