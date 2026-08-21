from flask import Blueprint, render_template, request
from sqlalchemy import inspect, text

from app import db


ia = Blueprint(
    "ia",
    __name__,
    url_prefix="/ia"
)


def numero(valor):
    try:
        if valor is None:
            return 0.0

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return 0.0

            # Aceita valores como:
            # 1234.56
            # 1.234,56
            # 1234,56
            if "," in valor:
                valor = valor.replace(".", "").replace(",", ".")
            else:
                valor = valor.replace(",", ".")

        return float(valor)

    except (ValueError, TypeError):
        return 0.0


def buscar_tabela(nome_tabela):
    try:
        inspector = inspect(db.engine)

        tabelas = inspector.get_table_names()

        if nome_tabela not in tabelas:
            return []

        resultado = db.session.execute(
            text(f'SELECT * FROM "{nome_tabela}"')
        )

        return [
            dict(linha._mapping)
            for linha in resultado
        ]

    except Exception:
        return []


def analisar_financas():

    receitas = buscar_tabela("receitas")
    despesas = buscar_tabela("despesas")
    cartoes = buscar_tabela("cartoes")
    compras_cartao = buscar_tabela("compras_cartao")
    faturas = buscar_tabela("faturas_pagas")

    total_receitas = 0.0
    total_despesas = 0.0
    total_cartao = 0.0
    total_faturas_pagas = 0.0

    # RECEITAS
    for receita in receitas:

        valor = receita.get("valor")

        if valor is None:
            valor = receita.get("valor_receita")

        total_receitas += numero(valor)

    # DESPESAS
    for despesa in despesas:

        valor = despesa.get("valor")

        total_despesas += numero(valor)

    # COMPRAS NO CARTÃO
    for compra in compras_cartao:

        valor = compra.get("valor")

        total_cartao += numero(valor)

    # FATURAS PAGAS
    for fatura in faturas:

        valor = fatura.get("valor")

        total_faturas_pagas += numero(valor)

    saldo = total_receitas - total_despesas

    analise = []

    # ANÁLISE DAS DESPESAS
    if total_receitas <= 0:

        analise.append(
            "Ainda não encontrei receitas cadastradas suficientes "
            "para calcular sua capacidade financeira."
        )

    else:

        percentual_despesas = (
            total_despesas / total_receitas
        ) * 100

        if percentual_despesas >= 90:

            analise.append(
                "Seu comprometimento com despesas está muito alto. "
                "Antes de assumir uma nova dívida, o ideal é procurar "
                "reduzir despesas ou renegociar dívidas existentes."
            )

        elif percentual_despesas >= 70:

            analise.append(
                "Suas despesas já consomem uma parcela importante "
                "da sua receita. Novas parcelas devem ser avaliadas "
                "com bastante cuidado."
            )

        else:

            analise.append(
                "Existe alguma margem entre suas receitas e despesas, "
                "mas ainda é necessário verificar as dívidas e juros "
                "antes de assumir um novo compromisso."
            )

    # SALDO NEGATIVO
    if saldo < 0:

        analise.append(
            "ATENÇÃO: suas despesas estão maiores que suas receitas. "
            "Neste cenário, a prioridade deve ser equilibrar o orçamento "
            "antes de contratar um novo empréstimo."
        )

    # SALDO POSITIVO
    elif saldo > 0:

        analise.append(
            f"Seu saldo calculado é de aproximadamente "
            f"R$ {saldo:,.2f}. Esse valor pode ser usado para acelerar "
            "a quitação de dívidas ou suas metas."
        )

    # CARTÕES
    if total_cartao > 0:

        analise.append(
            f"Foram encontradas aproximadamente "
            f"R$ {total_cartao:,.2f} em compras registradas nos cartões. "
            "As compras parceladas devem ser consideradas no planejamento "
            "dos próximos meses."
        )

    # FATURAS
    if total_faturas_pagas > 0:

        analise.append(
            f"Também encontrei aproximadamente "
            f"R$ {total_faturas_pagas:,.2f} em faturas de cartão pagas."
        )

    if not analise:

        analise.append(
            "Ainda não existem dados suficientes para fazer "
            "uma análise financeira completa."
        )

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "saldo": saldo,
        "cartoes": total_cartao,
        "faturas": total_faturas_pagas,
        "analise": analise,
    }


def analisar_pergunta(pergunta, dados):

    texto = pergunta.lower()

    respostas = []

    # DÍVIDAS / EMPRÉSTIMOS / JUROS
    if (
        "divida" in texto
        or "dívida" in texto
        or "emprestimo" in texto
        or "empréstimo" in texto
        or "consignado" in texto
        or "juros" in texto
    ):

        if dados["saldo"] <= 0:

            respostas.append(
                "Minha leitura é que não é um bom momento para "
                "assumir um novo empréstimo, porque seu orçamento "
                "atual não apresenta sobra."
            )

        else:

            respostas.append(
                "Para decidir se um empréstimo ou consignado vale a "
                "pena, não devemos olhar somente para a parcela. "
                "É necessário comparar a taxa de juros, o número de "
                "parcelas e principalmente o custo total da dívida atual "
                "com o custo total da nova operação."
            )

            respostas.append(
                "Se a nova operação reduzir significativamente os juros "
                "e também reduzir o custo total da dívida, ela pode ser "
                "uma alternativa interessante. Se apenas reduzir a "
                "parcela aumentando muito o prazo, a troca pode não "
                "compensar."
            )

    # METAS
    if "meta" in texto or "metas" in texto:

        respostas.append(
            "Também considero suas metas. Uma dívida só deve ser "
            "substituída se a mudança ajudar o orçamento sem prejudicar "
            "a capacidade de alcançar suas metas."
        )

    # CARTÕES / PARCELAS
    if (
        "cartao" in texto
        or "cartão" in texto
        or "parcela" in texto
        or "parcelas" in texto
    ):

        respostas.append(
            f"Encontrei aproximadamente "
            f"R$ {dados['cartoes']:,.2f} em compras registradas "
            "nos cartões. As parcelas futuras precisam ser "
            "consideradas antes de assumir novas compras."
        )

    # DESPESAS / GASTOS
    if (
        "despesa" in texto
        or "despesas" in texto
        or "gasto" in texto
        or "gastos" in texto
    ):

        respostas.append(
            f"Suas despesas registradas somam aproximadamente "
            f"R$ {dados['despesas']:,.2f}, enquanto as receitas somam "
            f"R$ {dados['receitas']:,.2f}."
        )

    # RESPOSTA PADRÃO
    if not respostas:

        respostas.append(
            "Fiz uma leitura inicial dos dados disponíveis no sistema. "
            f"Receitas: R$ {dados['receitas']:,.2f}. "
            f"Despesas: R$ {dados['despesas']:,.2f}. "
            f"Saldo: R$ {dados['saldo']:,.2f}. "
            f"Compras no cartão: R$ {dados['cartoes']:,.2f}."
        )

        respostas.append(
            "Posso analisar dívidas, juros, empréstimos, consignado, "
            "cartões, parcelas, despesas e metas para procurar uma "
            "alternativa que reduza o custo financeiro."
        )

    return " ".join(respostas)


@ia.route("/", methods=["GET", "POST"])
def index():

    resposta = None

    dados = analisar_financas()

    if request.method == "POST":

        pergunta = request.form.get(
            "pergunta",
            ""
        ).strip()

        if pergunta:

            resposta = analisar_pergunta(
                pergunta,
                dados
            )

    return render_template(
        "ia/index.html",
        resposta=resposta,
        dados=dados
    )