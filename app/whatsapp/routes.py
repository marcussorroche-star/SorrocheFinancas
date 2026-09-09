import os
import re
import hmac
import hashlib
import json
import tempfile
import unicodedata
from datetime import date

import requests
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, render_template

from app import db
from app.despesas.models import Despesa
from app.receitas.models import Receita
from app.pastas.models import Pasta
from app.whatsapp.leitor_arquivos.leitor import ler_arquivo


# ============================================================
# .ENV
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(
    ENV_FILE,
    override=True
)


# ============================================================
# BLUEPRINT
# ============================================================

whatsapp = Blueprint(
    "whatsapp",
    __name__,
    url_prefix="/whatsapp"
)


# ============================================================
# CONFIGURAÇÕES META
# ============================================================

WHATSAPP_VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN",
    "sorroche-financas-2026"
)

WHATSAPP_ACCESS_TOKEN = os.getenv(
    "WHATSAPP_ACCESS_TOKEN",
    ""
)

WHATSAPP_PHONE_NUMBER_ID = os.getenv(
    "WHATSAPP_PHONE_NUMBER_ID",
    ""
)

WHATSAPP_APP_SECRET = os.getenv(
    "WHATSAPP_APP_SECRET",
    ""
)

WHATSAPP_GRAPH_VERSION = os.getenv(
    "WHATSAPP_GRAPH_VERSION",
    "v23.0"
)

WHATSAPP_NUMERO = "553384592116"


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)


# ============================================================
# AMBIENTE RENDER
# ============================================================

EM_RENDER = bool(
    os.getenv("RENDER")
    or os.getenv("RENDER_SERVICE_ID")
)

OLLAMA_ATIVO = not EM_RENDER


# ============================================================
# OCR
# ============================================================

OCR_SPACE_API_KEY = os.getenv(
    "OCR_SPACE_API_KEY",
    ""
)


# ============================================================
# CONTROLE DE MENSAGENS PROCESSADAS
# ============================================================

MENSAGENS_PROCESSADAS = set()


# ============================================================
# CATEGORIAS
# ============================================================

CATEGORIAS_DESPESA = [
    "Mercado",
    "Farmácia",
    "Combustível",
    "Moradia",
    "Alimentação",
    "Transporte",
    "Saúde",
    "Educação",
    "Lazer",
    "Compras",
    "Contas",
    "Outros"
]


CATEGORIAS_RECEITA = [
    "Salário",
    "Pagamento",
    "Renda",
    "Lucro",
    "Comissão",
    "Investimentos",
    "Outros"
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(texto):

    texto = str(
        texto or ""
    ).lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto


def formatar_reais(valor):

    try:

        valor = float(
            valor or 0
        )

    except (
        TypeError,
        ValueError
    ):

        valor = 0.0

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def inicio_e_fim_mes():

    hoje = date.today()

    inicio = date(
        hoje.year,
        hoje.month,
        1
    )

    if hoje.month == 12:

        proximo = date(
            hoje.year + 1,
            1,
            1
        )

    else:

        proximo = date(
            hoje.year,
            hoje.month + 1,
            1
        )

    return inicio, proximo


def obter_despesas_mes():

    inicio, proximo = inicio_e_fim_mes()

    return Despesa.query.filter(
        Despesa.data >= inicio,
        Despesa.data < proximo
    ).all()


def obter_receitas_mes():

    inicio, proximo = inicio_e_fim_mes()

    return Receita.query.filter(
        Receita.data >= inicio,
        Receita.data < proximo
    ).all()


def valor_seguro(valor):

    try:

        return float(
            valor or 0
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


# ============================================================
# IDENTIFICAR RECEITA
# ============================================================

def mensagem_e_receita(texto):

    texto = str(
        texto or ""
    ).lower().strip()

    if not texto:
        return False

    palavras_receita = [
        "recebi",
        "recebemos",
        "recebeu",
        "ganhei",
        "ganhamos",
        "ganhou",
        "salário recebido",
        "salario recebido",
        "pagamento recebido",
        "entrada",
        "entrou",
        "recebimento",
        "renda",
        "lucro",
        "comissão",
        "comissao",
        "prêmio",
        "premio",
        "bonificação",
        "bonificacao",
        "aposentadoria",
        "pensão",
        "pensao"
    ]

    palavras_despesa = [
        "gastei",
        "gastamos",
        "gastou",
        "paguei",
        "pagamos",
        "pagou",
        "comprei",
        "compramos",
        "comprou",
        "despesa",
        "conta",
        "fatura",
        "boleto",
        "mercado",
        "supermercado",
        "gasolina",
        "combustível",
        "combustivel",
        "farmácia",
        "farmacia",
        "jantar",
        "almoço",
        "almoco"
    ]

    tem_receita = any(
        palavra in texto
        for palavra in palavras_receita
    )

    tem_despesa = any(
        palavra in texto
        for palavra in palavras_despesa
    )

    if tem_despesa and not (
        "recebi" in texto
        or "recebeu" in texto
        or "ganhei" in texto
        or "ganhou" in texto
        or "entrou" in texto
    ):

        return False

    return tem_receita


# ============================================================
# IDENTIFICAR CATEGORIA
# ============================================================

def identificar_categoria_texto(texto):

    texto_lower = str(
        texto or ""
    ).lower()

    if any(
        palavra in texto_lower
        for palavra in [
            "mercado",
            "supermercado",
            "compra de mercado"
        ]
    ):

        return "Mercado"

    if any(
        palavra in texto_lower
        for palavra in [
            "farmácia",
            "farmacia",
            "remédio",
            "remedio",
            "medicamento"
        ]
    ):

        return "Farmácia"

    if any(
        palavra in texto_lower
        for palavra in [
            "gasolina",
            "combustível",
            "combustivel",
            "posto",
            "abasteci",
            "abastecimento"
        ]
    ):

        return "Combustível"

    if any(
        palavra in texto_lower
        for palavra in [
            "almoço",
            "almoco",
            "jantar",
            "lanche",
            "restaurante",
            "comida",
            "ifood"
        ]
    ):

        return "Alimentação"

    if any(
        palavra in texto_lower
        for palavra in [
            "uber",
            "taxi",
            "táxi",
            "ônibus",
            "onibus",
            "transporte"
        ]
    ):

        return "Transporte"

    if any(
        palavra in texto_lower
        for palavra in [
            "aluguel",
            "casa",
            "condomínio",
            "condominio"
        ]
    ):

        return "Moradia"

    if any(
        palavra in texto_lower
        for palavra in [
            "luz",
            "energia",
            "água",
            "agua",
            "internet",
            "telefone",
            "conta de"
        ]
    ):

        return "Contas"

    if any(
        palavra in texto_lower
        for palavra in [
            "escola",
            "faculdade",
            "curso",
            "mensalidade escolar"
        ]
    ):

        return "Educação"

    if any(
        palavra in texto_lower
        for palavra in [
            "médico",
            "medico",
            "hospital",
            "consulta",
            "plano de saúde",
            "plano de saude"
        ]
    ):

        return "Saúde"

    if any(
        palavra in texto_lower
        for palavra in [
            "cinema",
            "viagem",
            "jogo",
            "diversão",
            "diversao"
        ]
    ):

        return "Lazer"

    if (
        "salário" in texto_lower
        or "salario" in texto_lower
    ):

        return "Salário"

    if "pagamento" in texto_lower:
        return "Pagamento"

    if "renda" in texto_lower:
        return "Renda"

    if "lucro" in texto_lower:
        return "Lucro"

    if (
        "comissão" in texto_lower
        or "comissao" in texto_lower
    ):

        return "Comissão"

    if (
        "investimento" in texto_lower
        or "investimentos" in texto_lower
    ):

        return "Investimentos"

    return None


# ============================================================
# IDENTIFICAR CONSULTA FINANCEIRA
# ============================================================

def identificar_consulta_financeira(texto):

    texto_normalizado = normalizar_texto(
        texto
    )

    texto_normalizado = re.sub(
        r"\beu\b",
        "",
        texto_normalizado
    )

    texto_normalizado = re.sub(
        r"\bque\b",
        "",
        texto_normalizado
    )

    texto_normalizado = re.sub(
        r"\s+",
        " ",
        texto_normalizado
    ).strip()

    if not texto_normalizado:
        return None

    if (
        "quanto recebi" in texto_normalizado
        or "quanto entrou" in texto_normalizado
        or "quanto ganhei" in texto_normalizado
        or "total de receitas" in texto_normalizado
        or "minhas receitas" in texto_normalizado
    ):

        return "receitas_mes"

    if (
        "quanto gastei no mercado" in texto_normalizado
        or "quanto gastei com mercado" in texto_normalizado
        or "gastos do mercado" in texto_normalizado
        or "total mercado" in texto_normalizado
    ):

        return "mercado_mes"

    if (
        "quanto gastei no cartao" in texto_normalizado
        or "gastos no cartao" in texto_normalizado
    ):

        return "cartao_mes"

    if (
        "quanto gastei" in texto_normalizado
        or "quanto paguei" in texto_normalizado
        or "total de despesas" in texto_normalizado
        or "minhas despesas" in texto_normalizado
    ):

        return "despesas_mes"

    if (
        "quanto sobrou" in texto_normalizado
        or "saldo do mes" in texto_normalizado
        or "saldo desse mes" in texto_normalizado
        or "saldo deste mes" in texto_normalizado
    ):

        return "saldo_mes"

    if (
        "quanto tenho para gastar" in texto_normalizado
        or "quanto posso gastar" in texto_normalizado
        or "quanto ainda posso gastar" in texto_normalizado
    ):

        return "disponivel_mes"

    if (
        "quanto tenho nas metas" in texto_normalizado
        or "quanto tenho guardado nas metas" in texto_normalizado
        or "minhas metas" in texto_normalizado
        or "status das metas" in texto_normalizado
    ):

        return "metas"

    if (
        "quanto investi" in texto_normalizado
        or "quanto tenho investido" in texto_normalizado
        or "total investido" in texto_normalizado
        or "meus investimentos" in texto_normalizado
    ):

        return "investimentos"

    return None


# ============================================================
# CONSULTA - RECEITAS
# ============================================================

def consulta_receitas_mes():

    receitas = obter_receitas_mes()

    total = sum(
        valor_seguro(
            receita.valor
        )
        for receita in receitas
    )

    linhas = []

    for receita in receitas:

        descricao = str(
            getattr(
                receita,
                "descricao",
                ""
            ) or "Sem descrição"
        )

        categoria = str(
            getattr(
                receita,
                "categoria",
                "Outros"
            ) or "Outros"
        )

        data_receita = getattr(
            receita,
            "data",
            None
        )

        if hasattr(
            data_receita,
            "strftime"
        ):

            data_formatada = data_receita.strftime(
                "%d/%m"
            )

        else:

            data_formatada = ""

        linhas.append(
            f"{data_formatada} - "
            f"{descricao} - "
            f"{formatar_reais(receita.valor)}"
        )

    mensagem = (
        "Sorroche Finanças\n\n"
        "Receitas deste mês\n\n"
        f"Total recebido: {formatar_reais(total)}"
    )

    if linhas:

        mensagem += "\n\nLançamentos:\n"

        mensagem += "\n".join(
            linhas[:20]
        )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "receitas_mes",
        "resposta": mensagem,
        "total": total,
        "quantidade": len(receitas)
    }


# ============================================================
# CONSULTA - DESPESAS
# ============================================================

def consulta_despesas_mes():

    despesas = obter_despesas_mes()

    total = sum(
        valor_seguro(
            despesa.valor
        )
        for despesa in despesas
    )

    linhas = []

    for despesa in despesas:

        descricao = str(
            getattr(
                despesa,
                "descricao",
                ""
            ) or "Sem descrição"
        )

        categoria = str(
            getattr(
                despesa,
                "categoria",
                "Outros"
            ) or "Outros"
        )

        valor = valor_seguro(
            despesa.valor
        )

        data_despesa = getattr(
            despesa,
            "data",
            None
        )

        if hasattr(
            data_despesa,
            "strftime"
        ):

            data_formatada = data_despesa.strftime(
                "%d/%m"
            )

        else:

            data_formatada = ""

        linhas.append(
            f"{data_formatada} - "
            f"{categoria} - "
            f"{descricao} - "
            f"{formatar_reais(valor)}"
        )

    mensagem = (
        "Sorroche Finanças\n\n"
        "Despesas deste mês\n\n"
        f"Total gasto: {formatar_reais(total)}"
    )

    if linhas:

        mensagem += "\n\nLançamentos:\n"

        mensagem += "\n".join(
            linhas[:20]
        )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "despesas_mes",
        "resposta": mensagem,
        "total": total,
        "quantidade": len(despesas)
    }


# ============================================================
# CONSULTA - SALDO
# ============================================================

def consulta_saldo_mes():

    receitas = obter_receitas_mes()
    despesas = obter_despesas_mes()

    total_receitas = sum(
        valor_seguro(
            receita.valor
        )
        for receita in receitas
    )

    total_despesas = sum(
        valor_seguro(
            despesa.valor
        )
        for despesa in despesas
    )

    saldo = (
        total_receitas
        - total_despesas
    )

    mensagem = (
        "Sorroche Finanças\n\n"
        "Saldo deste mês\n\n"
        f"Receitas: {formatar_reais(total_receitas)}\n"
        f"Despesas: {formatar_reais(total_despesas)}\n"
        f"Saldo: {formatar_reais(saldo)}"
    )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "saldo_mes",
        "resposta": mensagem,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo": saldo
    }


# ============================================================
# CONSULTA - DISPONÍVEL PARA GASTAR
# ============================================================

def consulta_disponivel_mes():

    receitas = obter_receitas_mes()
    despesas = obter_despesas_mes()

    total_receitas = sum(
        valor_seguro(
            receita.valor
        )
        for receita in receitas
    )

    total_despesas = sum(
        valor_seguro(
            despesa.valor
        )
        for despesa in despesas
    )

    disponivel = (
        total_receitas
        - total_despesas
    )

    mensagem = (
        "Sorroche Finanças\n\n"
        "Valor disponível no mês\n\n"
        f"Receitas: {formatar_reais(total_receitas)}\n"
        f"Despesas: {formatar_reais(total_despesas)}\n"
        f"Disponível: {formatar_reais(disponivel)}"
    )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "disponivel_mes",
        "resposta": mensagem,
        "disponivel": disponivel
    }


# ============================================================
# CONSULTA - MERCADO
# ============================================================

def consulta_mercado_mes():

    despesas = obter_despesas_mes()

    total = 0.0
    quantidade = 0

    for despesa in despesas:

        categoria = normalizar_texto(
            getattr(
                despesa,
                "categoria",
                ""
            )
        )

        descricao = normalizar_texto(
            getattr(
                despesa,
                "descricao",
                ""
            )
        )

        if (
            categoria == "mercado"
            or "mercado" in descricao
            or "supermercado" in descricao
        ):

            total += valor_seguro(
                despesa.valor
            )

            quantidade += 1

    mensagem = (
        "Sorroche Finanças\n\n"
        "Gastos no Mercado este mês\n\n"
        f"Total: {formatar_reais(total)}\n"
        f"Lançamentos: {quantidade}"
    )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "mercado_mes",
        "resposta": mensagem,
        "total": total,
        "quantidade": quantidade
    }


# ============================================================
# CONSULTA - CARTÃO
# ============================================================

def consulta_cartao_mes():

    despesas = obter_despesas_mes()

    total = 0.0
    quantidade = 0

    for despesa in despesas:

        forma = normalizar_texto(
            getattr(
                despesa,
                "forma_pagamento",
                ""
            )
        )

        if forma in [
            "cartao",
            "credito",
            "cartao de credito"
        ]:

            total += valor_seguro(
                despesa.valor
            )

            quantidade += 1

    mensagem = (
        "Sorroche Finanças\n\n"
        "Gastos no cartão este mês\n\n"
        f"Total: {formatar_reais(total)}\n"
        f"Lançamentos: {quantidade}"
    )

    return {
        "ok": True,
        "tipo": "consulta",
        "consulta": "cartao_mes",
        "resposta": mensagem,
        "total": total,
        "quantidade": quantidade
    }


# ============================================================
# CONSULTA - METAS
# ============================================================

def consulta_metas():

    try:

        from app.metas.models import Meta

    except Exception as exc:

        return {
            "ok": False,
            "tipo": "consulta",
            "consulta": "metas",
            "erro": (
                "Não foi possível carregar as metas: "
                f"{exc}"
            )
        }

    try:

        metas = Meta.query.all()

        total_guardado = 0.0
        total_objetivo = 0.0

        linhas = []

        for meta in metas:

            nome = str(
                getattr(
                    meta,
                    "nome",
                    "Meta"
                ) or "Meta"
            )

            guardado = valor_seguro(
                getattr(
                    meta,
                    "valor_guardado",
                    0
                )
            )

            objetivo = valor_seguro(
                getattr(
                    meta,
                    "valor_objetivo",
                    0
                )
            )

            total_guardado += guardado
            total_objetivo += objetivo

            if objetivo > 0:

                percentual = (
                    guardado
                    / objetivo
                ) * 100

            else:

                percentual = 0

            linhas.append(
                f"{nome}: "
                f"{formatar_reais(guardado)} / "
                f"{formatar_reais(objetivo)} "
                f"({percentual:.1f}%)"
            )

        mensagem = (
            "Sorroche Finanças\n\n"
            "Minhas metas\n\n"
            f"Total guardado: "
            f"{formatar_reais(total_guardado)}\n"
            f"Total das metas: "
            f"{formatar_reais(total_objetivo)}"
        )

        if linhas:

            mensagem += (
                "\n\nDetalhamento:\n"
            )

            mensagem += "\n".join(
                linhas[:20]
            )

        return {
            "ok": True,
            "tipo": "consulta",
            "consulta": "metas",
            "resposta": mensagem,
            "total_guardado": total_guardado,
            "total_objetivo": total_objetivo,
            "quantidade": len(metas)
        }

    except Exception as exc:

        print(
            "ERRO CONSULTA METAS:",
            exc
        )

        return {
            "ok": False,
            "tipo": "consulta",
            "consulta": "metas",
            "erro": (
                "Erro ao consultar as metas: "
                f"{exc}"
            )
        }


# ============================================================
# CONSULTA - INVESTIMENTOS
# ============================================================

def consulta_investimentos():

    try:

        from app.investimentos.models import Investimento

    except Exception as exc:

        return {
            "ok": False,
            "tipo": "consulta",
            "consulta": "investimentos",
            "erro": (
                "Não foi possível carregar os investimentos: "
                f"{exc}"
            )
        }

    try:

        investimentos = Investimento.query.all()

        total = 0.0

        for investimento in investimentos:

            valor = 0.0

            for nome_campo in [
                "valor",
                "valor_investido",
                "valor_aplicado",
                "aporte"
            ]:

                if hasattr(
                    investimento,
                    nome_campo
                ):

                    valor = valor_seguro(
                        getattr(
                            investimento,
                            nome_campo,
                            0
                        )
                    )

                    break

            total += valor

        mensagem = (
            "Sorroche Finanças\n\n"
            "Investimentos\n\n"
            f"Total investido: {formatar_reais(total)}\n"
            f"Registros: {len(investimentos)}"
        )

        return {
            "ok": True,
            "tipo": "consulta",
            "consulta": "investimentos",
            "resposta": mensagem,
            "total": total,
            "quantidade": len(investimentos)
        }

    except Exception as exc:

        print(
            "ERRO CONSULTA INVESTIMENTOS:",
            exc
        )

        return {
            "ok": False,
            "tipo": "consulta",
            "consulta": "investimentos",
            "erro": (
                "Erro ao consultar os investimentos: "
                f"{exc}"
            )
        }


# ============================================================
# PROCESSAR CONSULTA FINANCEIRA
# ============================================================

def processar_consulta_financeira(texto):

    consulta = identificar_consulta_financeira(
        texto
    )

    if not consulta:
        return None

    try:

        if consulta == "receitas_mes":
            return consulta_receitas_mes()

        if consulta == "despesas_mes":
            return consulta_despesas_mes()

        if consulta == "saldo_mes":
            return consulta_saldo_mes()

        if consulta == "disponivel_mes":
            return consulta_disponivel_mes()

        if consulta == "mercado_mes":
            return consulta_mercado_mes()

        if consulta == "cartao_mes":
            return consulta_cartao_mes()

        if consulta == "metas":
            return consulta_metas()

        if consulta == "investimentos":
            return consulta_investimentos()

        return None

    except Exception as exc:

        print(
            "ERRO AO PROCESSAR CONSULTA:",
            exc
        )

        return {
            "ok": False,
            "tipo": "consulta",
            "consulta": consulta,
            "erro": (
                "Erro ao consultar os dados: "
                f"{exc}"
            )
        }


# ============================================================
# QR CODE
# ============================================================

@whatsapp.route(
    "/qr",
    methods=["GET"]
)
def qr():

    numero = WHATSAPP_NUMERO

    mensagem = (
        "Olá! Quero usar o Sorroche Finanças pelo WhatsApp."
    )

    link_whatsapp = (
        f"https://wa.me/{numero}"
        f"?text={requests.utils.quote(mensagem)}"
    )

    return render_template(
        "whatsapp/qr.html",
        numero=numero,
        link_whatsapp=link_whatsapp
    )


# ============================================================
# IA OLLAMA
# ============================================================

def consultar_ia(texto):

    if not OLLAMA_ATIVO:

        print(
            "OLLAMA DESATIVADO NO RENDER."
        )

        return None

    tipo_sugerido = (
        "RECEITA"
        if mensagem_e_receita(texto)
        else "DESPESA"
    )

    categoria_local = identificar_categoria_texto(
        texto
    )

    prompt = f"""
Você é a IA financeira do sistema Sorroche Finanças.

Analise a mensagem recebida.

Mensagem:
{texto}

Tipo identificado inicialmente:
{tipo_sugerido}

Categoria identificada localmente:
{categoria_local or "Nenhuma"}

IMPORTANTE:

Se houver uma categoria claramente identificável
na mensagem, mantenha essa categoria.

Exemplo:

"Gastei 20 reais no mercado via pix"

deve obrigatoriamente resultar em:

categoria = "Mercado"

Nunca transforme Mercado em Outros quando a palavra
mercado estiver presente.

Se a mensagem indicar dinheiro RECEBIDO, GANHO,
SALÁRIO, PAGAMENTO RECEBIDO, RENDA, LUCRO,
COMISSÃO, BONIFICAÇÃO ou entrada de dinheiro,
o tipo deve ser "receita".

Se indicar dinheiro GASTO, PAGO, COMPRADO,
MERCADO, GASOLINA, FARMÁCIA ou outra saída,
o tipo deve ser "despesa".

Categorias de despesas:

Mercado
Farmácia
Combustível
Moradia
Alimentação
Transporte
Saúde
Educação
Lazer
Compras
Contas
Outros

Categorias de receitas:

Salário
Pagamento
Renda
Lucro
Comissão
Investimentos
Outros

Formas de pagamento:

Cartão
Pix
Dinheiro
Boleto
Outro

Responda SOMENTE JSON válido.

Formato:

{{
    "tipo": "despesa",
    "valor": 0,
    "categoria": "Outros",
    "forma_pagamento": "Outro",
    "descricao": "descrição"
}}
"""

    try:

        resposta = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
           timeout=10
        )

        resposta.raise_for_status()

        dados = resposta.json()

        texto_resposta = str(
            dados.get(
                "response",
                ""
            )
        ).strip()

        if not texto_resposta:
            return None

        texto_resposta = (
            texto_resposta
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        inicio = texto_resposta.find("{")
        fim = texto_resposta.rfind("}")

        if inicio == -1 or fim == -1:
            return None

        resultado = json.loads(
            texto_resposta[
                inicio:fim + 1
            ]
        )

        valor = resultado.get(
            "valor"
        )

        if valor is None:
            return None

        if isinstance(
            valor,
            str
        ):

            valor = (
                valor
                .replace("R$", "")
                .replace(" ", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

        valor = float(
            valor
        )

        tipo = str(
            resultado.get(
                "tipo",
                tipo_sugerido
            )
        ).strip().lower()

        if mensagem_e_receita(texto):

            tipo = "receita"

        elif tipo not in [
            "receita",
            "despesa"
        ]:

            tipo = "despesa"

        categoria = str(
            resultado.get(
                "categoria",
                "Outros"
            )
        ).strip()

        forma_pagamento = str(
            resultado.get(
                "forma_pagamento",
                "Outro"
            )
        ).strip()

        descricao = str(
            resultado.get(
                "descricao",
                texto
            )
        ).strip()

        categoria_detectada = identificar_categoria_texto(
            texto
        )

        if categoria_detectada:

            categoria = categoria_detectada

        if tipo == "receita":

            categorias_validas = [
                item.lower()
                for item in CATEGORIAS_RECEITA
            ]

            if categoria.lower() not in categorias_validas:

                if categoria_detectada in CATEGORIAS_RECEITA:

                    categoria = categoria_detectada

                else:

                    categoria = "Outros"

        else:

            categorias_validas = [
                item.lower()
                for item in CATEGORIAS_DESPESA
            ]

            if categoria.lower() not in categorias_validas:

                categoria = "Outros"

        if forma_pagamento.lower() == "pix":

            forma_pagamento = "À vista"

        return {
            "tipo": tipo,
            "descricao": descricao,
            "categoria": categoria,
            "valor": valor,
            "forma_pagamento": forma_pagamento,
            "ia": True
        }

    except Exception as exc:

        print(
            "ERRO OLLAMA:",
            exc
        )

        return None


# ============================================================
# INTERPRETAR TEXTO
# ============================================================

def interpretar_mensagem(texto):

    texto = str(
        texto or ""
    ).strip()

    if not texto:
        return None

    consulta = processar_consulta_financeira(
        texto
    )

    if consulta:
        return consulta

    tipo_local = (
        "receita"
        if mensagem_e_receita(texto)
        else "despesa"
    )

    categoria_local = identificar_categoria_texto(
        texto
    )

    resultado_ia = consultar_ia(
        texto
    )

    if resultado_ia:

        resultado_ia["tipo"] = tipo_local

        if categoria_local:

            resultado_ia["categoria"] = categoria_local

        return resultado_ia

    texto_lower = texto.lower()

    padrao_valor = (
        r"(?:r\$\s*)?"
        r"(\d+(?:[.,]\d{1,2})?)"
        r"\s*(?:reais|real)?"
    )

    valores = re.findall(
        padrao_valor,
        texto_lower
    )

    if not valores:
        return None

    valor_texto = valores[0]

    if "," in valor_texto:

        valor_texto = (
            valor_texto
            .replace(".", "")
            .replace(",", ".")
        )

    else:

        valor_texto = valor_texto.replace(
            ",",
            ""
        )

    try:

        valor = float(
            valor_texto
        )

    except ValueError:

        return None

    forma_pagamento = "Outro"

    if (
        "cartão" in texto_lower
        or "cartao" in texto_lower
    ):

        forma_pagamento = "Cartão"

    elif "pix" in texto_lower:

        forma_pagamento = "À vista"

    elif "dinheiro" in texto_lower:

        forma_pagamento = "Dinheiro"

    elif "boleto" in texto_lower:

        forma_pagamento = "Boleto"

    if tipo_local == "receita":

        categoria = categoria_local or "Outros"

        if categoria not in CATEGORIAS_RECEITA:

            categoria = "Outros"

        return {
            "tipo": "receita",
            "descricao": texto,
            "categoria": categoria,
            "valor": valor,
            "forma_pagamento": forma_pagamento,
            "ia": False
        }

    categoria = categoria_local or "Outros"

    if categoria not in CATEGORIAS_DESPESA:

        categoria = "Outros"

    return {
        "tipo": "despesa",
        "descricao": texto,
        "categoria": categoria,
        "valor": valor,
        "forma_pagamento": forma_pagamento,
        "ia": False
    }


# ============================================================
# LOCALIZAR OU CRIAR PASTA
# ============================================================

def encontrar_ou_criar_pasta_categoria(
    categoria
):

    categoria = str(
        categoria or "Outros"
    ).strip()

    if not categoria:

        categoria = "Outros"

    try:

        pasta = Pasta.query.filter(
            db.func.lower(Pasta.nome)
            == categoria.lower()
        ).first()

        if pasta:

            print(
                "PASTA ENCONTRADA:",
                pasta.id,
                pasta.nome,
                pasta.cor
            )

            return pasta

        cores = [
            "slate",
            "emerald",
            "amber",
            "rose",
            "sky",
            "violet"
        ]

        quantidade = Pasta.query.count()

        cor = cores[
            quantidade % len(cores)
        ]

        pasta = Pasta(
            nome=categoria,
            descricao=(
                f"Pasta automática da categoria "
                f"{categoria}"
            ),
            cor=cor
        )

        db.session.add(
            pasta
        )

        db.session.commit()

        print(
            "PASTA CRIADA AUTOMATICAMENTE:",
            pasta.id,
            pasta.nome,
            pasta.cor
        )

        return pasta

    except Exception as exc:

        db.session.rollback()

        print(
            "ERRO AO LOCALIZAR/CRIAR PASTA:",
            exc
        )

        return None


# ============================================================
# CRIAR DESPESA
# ============================================================

def criar_despesa(
    dados_interpretados
):

    categoria = dados_interpretados.get(
        "categoria",
        "Outros"
    )

    categoria_detectada = identificar_categoria_texto(
        dados_interpretados.get(
            "descricao",
            ""
        )
    )

    if categoria_detectada:

        categoria = categoria_detectada

    pasta = encontrar_ou_criar_pasta_categoria(
        categoria
    )

    dados_despesa = {
        "descricao": dados_interpretados[
            "descricao"
        ],
        "categoria": categoria,
        "valor": dados_interpretados[
            "valor"
        ],
        "data": date.today(),
        "vencimento": None,
        "forma_pagamento": dados_interpretados[
            "forma_pagamento"
        ],
        "status": "Pendente",
        "usuario_id": 1
    }

    if pasta:

        dados_despesa["pasta_id"] = pasta.id

    despesa = Despesa(
        **dados_despesa
    )

    db.session.add(
        despesa
    )

    db.session.commit()

    print(
        "DESPESA CRIADA:",
        despesa.id,
        "CATEGORIA:",
        despesa.categoria,
        "PASTA_ID:",
        getattr(
            despesa,
            "pasta_id",
            None
        )
    )

    return despesa


# ============================================================
# CRIAR RECEITA
# ============================================================

def criar_receita(
    dados_interpretados
):

    dados_receita = {
        "descricao": dados_interpretados[
            "descricao"
        ],
        "valor": dados_interpretados[
            "valor"
        ],
        "data": date.today(),
        "usuario_id": 1
    }

    colunas = Receita.__table__.columns.keys()

    if "categoria" in colunas:

        dados_receita["categoria"] = (
            dados_interpretados.get(
                "categoria",
                "Outros"
            )
        )

    if "forma_pagamento" in colunas:

        dados_receita["forma_pagamento"] = (
            dados_interpretados.get(
                "forma_pagamento",
                "Outro"
            )
        )

    if "status" in colunas:

        dados_receita["status"] = "Recebido"

    receita = Receita(
        **dados_receita
    )

    db.session.add(
        receita
    )

    db.session.commit()

    print(
        "RECEITA CRIADA:",
        receita.id,
        "VALOR:",
        receita.valor
    )

    return receita


# ============================================================
# RESPOSTA DA DESPESA
# ============================================================

def resposta_despesa(
    despesa
):

    pasta = None

    try:

        if getattr(
            despesa,
            "pasta",
            None
        ):

            pasta = despesa.pasta.nome

    except Exception:

        pasta = None

    return {
        "id": despesa.id,
        "descricao": despesa.descricao,
        "categoria": despesa.categoria,
        "valor": despesa.valor,
        "forma_pagamento": despesa.forma_pagamento,
        "status": despesa.status,
        "pasta_id": getattr(
            despesa,
            "pasta_id",
            None
        ),
        "pasta": pasta
    }


# ============================================================
# RESPOSTA DA RECEITA
# ============================================================

def resposta_receita(
    receita,
    dados
):

    resposta = {
        "id": receita.id,
        "descricao": receita.descricao,
        "valor": receita.valor
    }

    colunas = Receita.__table__.columns.keys()

    if "categoria" in colunas:

        resposta["categoria"] = getattr(
            receita,
            "categoria",
            dados.get(
                "categoria",
                "Outros"
            )
        )

    else:

        resposta["categoria"] = dados.get(
            "categoria",
            "Outros"
        )

    if "forma_pagamento" in colunas:

        resposta["forma_pagamento"] = getattr(
            receita,
            "forma_pagamento",
            dados.get(
                "forma_pagamento",
                "Outro"
            )
        )

    else:

        resposta["forma_pagamento"] = dados.get(
            "forma_pagamento",
            "Outro"
        )

    if "status" in colunas:

        resposta["status"] = getattr(
            receita,
            "status",
            "Recebido"
        )

    else:

        resposta["status"] = "Recebido"

    return resposta


# ============================================================
# ANALISAR TEXTO
# ============================================================

def analisar_texto_recebido(
    texto
):

    dados = interpretar_mensagem(
        texto
    )

    if not dados:

        return {
            "ok": False,
            "erro": (
                "Não consegui identificar "
                "um valor na mensagem."
            ),
            "texto": texto
        }

    try:

        tipo = dados.get(
            "tipo",
            "despesa"
        ).lower()

        if tipo == "consulta":

            return dados

        if tipo == "receita":

            receita = criar_receita(
                dados
            )

            return {
                "ok": True,
                "mensagem": (
                    "Receita criada com sucesso."
                ),
                "tipo": "receita",
                "ia": dados.get(
                    "ia",
                    False
                ),
                "receita": resposta_receita(
                    receita,
                    dados
                )
            }

        despesa = criar_despesa(
            dados
        )

        return {
            "ok": True,
            "mensagem": (
                "Despesa criada com sucesso."
            ),
            "tipo": "despesa",
            "ia": dados.get(
                "ia",
                False
            ),
            "despesa": resposta_despesa(
                despesa
            )
        }

    except Exception as exc:

        db.session.rollback()

        print(
            "ERRO AO CRIAR LANÇAMENTO:",
            exc
        )

        return {
            "ok": False,
            "erro": (
                "Erro ao salvar o lançamento: "
                f"{exc}"
            )
        }


# ============================================================
# ENVIAR MENSAGEM WHATSAPP
# ============================================================

def enviar_mensagem_whatsapp(
    numero,
    mensagem
):

    if not WHATSAPP_ACCESS_TOKEN:

        return {
            "ok": False,
            "enviado": False,
            "erro": (
                "WHATSAPP_ACCESS_TOKEN "
                "não configurado."
            )
        }

    if not WHATSAPP_PHONE_NUMBER_ID:

        return {
            "ok": False,
            "enviado": False,
            "erro": (
                "WHATSAPP_PHONE_NUMBER_ID "
                "não configurado."
            )
        }

    numero = str(
        numero or ""
    )

    numero = (
        numero
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if not numero:

        return {
            "ok": False,
            "enviado": False,
            "erro": (
                "Número do destinatário vazio."
            )
        }

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_GRAPH_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": (
            f"Bearer {WHATSAPP_ACCESS_TOKEN}"
        ),
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": mensagem
        }
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        try:

            dados = resposta.json()

        except ValueError:

            dados = {
                "resposta_texto": resposta.text
            }

        if resposta.status_code >= 400:

            print(
                "ERRO ENVIO WHATSAPP:",
                dados
            )

            return {
                "ok": False,
                "enviado": False,
                "status_code": resposta.status_code,
                "erro": dados
            }

        print(
            "MENSAGEM WHATSAPP ENVIADA:",
            dados
        )

        return {
            "ok": True,
            "enviado": True,
            "status_code": resposta.status_code,
            "dados": dados
        }

    except requests.exceptions.RequestException as exc:

        print(
            "ERRO WHATSAPP:",
            exc
        )

        return {
            "ok": False,
            "enviado": False,
            "erro": str(exc)
        }


# ============================================================
# BAIXAR MÍDIA META
# ============================================================

def baixar_midia_meta(
    media_id
):

    if not WHATSAPP_ACCESS_TOKEN:
        return None, None

    if not media_id:
        return None, None

    url_info = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_GRAPH_VERSION}/"
        f"{media_id}"
    )

    headers = {
        "Authorization": (
            f"Bearer {WHATSAPP_ACCESS_TOKEN}"
        )
    }

    try:

        resposta = requests.get(
            url_info,
            headers=headers,
            timeout=30
        )

        resposta.raise_for_status()

        dados = resposta.json()

        url_media = dados.get(
            "url"
        )

        mime_type = dados.get(
            "mime_type",
            "application/octet-stream"
        )

        if not url_media:

            print(
                "META NÃO RETORNOU URL DA MÍDIA:",
                dados
            )

            return None, None

        resposta_media = requests.get(
            url_media,
            headers=headers,
            timeout=60
        )

        resposta_media.raise_for_status()

        return (
            resposta_media.content,
            mime_type
        )

    except Exception as exc:

        print(
            "ERRO AO BAIXAR MÍDIA META:",
            exc
        )

        return None, None


# ============================================================
# OCR
# ============================================================

def extrair_texto_imagem(
    conteudo,
    nome_arquivo="imagem.jpg",
    mime_type="image/jpeg"
):

    if not OCR_SPACE_API_KEY:

        return {
            "ok": False,
            "erro": (
                "OCR_SPACE_API_KEY "
                "não configurada."
            )
        }

    try:

        resposta = requests.post(
            "https://api.ocr.space/parse/image",
            files={
                "file": (
                    nome_arquivo,
                    conteudo,
                    mime_type
                )
            },
            data={
                "apikey": OCR_SPACE_API_KEY,
                "language": "por",
                "isOverlayRequired": "false",
                "OCREngine": "2",
                "scale": "true",
                "detectOrientation": "true"
            },
            timeout=60
        )

        try:

            dados = resposta.json()

        except ValueError:

            dados = {}

        if resposta.status_code >= 400:

            erro = dados.get(
                "ErrorMessage",
                "Erro no OCR."
            )

            if isinstance(
                erro,
                list
            ):

                erro = " ".join(
                    str(item)
                    for item in erro
                )

            return {
                "ok": False,
                "erro": str(erro)
            }

        if dados.get(
            "IsErroredOnProcessing"
        ):

            erro = dados.get(
                "ErrorMessage",
                "O OCR não conseguiu processar a imagem."
            )

            if isinstance(
                erro,
                list
            ):

                erro = " ".join(
                    str(item)
                    for item in erro
                )

            return {
                "ok": False,
                "erro": str(erro)
            }

        resultados = dados.get(
            "ParsedResults",
            []
        )

        textos = []

        for resultado in resultados:

            texto = str(
                resultado.get(
                    "ParsedText",
                    ""
                )
            ).strip()

            if texto:

                textos.append(
                    texto
                )

        texto_ocr = "\n\n".join(
            textos
        ).strip()

        if not texto_ocr:

            return {
                "ok": False,
                "erro": (
                    "Não consegui identificar "
                    "texto na imagem."
                )
            }

        return {
            "ok": True,
            "texto": texto_ocr
        }

    except Exception as exc:

        print(
            "ERRO OCR:",
            exc
        )

        return {
            "ok": False,
            "erro": str(exc)
        }


# ============================================================
# PROCESSAR FOTO
# ============================================================

def processar_foto_whatsapp(
    media_id,
    numero,
    legenda=""
):

    conteudo, mime_type = baixar_midia_meta(
        media_id
    )

    if not conteudo:

        return {
            "ok": False,
            "tipo": "foto",
            "erro": (
                "Recebi sua foto, mas não consegui "
                "baixar a imagem para análise."
            )
        }

    resultado_ocr = extrair_texto_imagem(
        conteudo,
        "comprovante.jpg",
        mime_type or "image/jpeg"
    )

    if not resultado_ocr.get(
        "ok"
    ):

        return {
            "ok": False,
            "tipo": "foto",
            "erro": resultado_ocr.get(
                "erro",
                "Erro no OCR."
            )
        }

    texto_ocr = resultado_ocr[
        "texto"
    ]

    if legenda:

        texto_ocr = (
            f"{legenda}\n"
            f"{texto_ocr}"
        )

    resultado = analisar_texto_recebido(
        texto_ocr
    )

    resultado["tipo"] = "foto"
    resultado["texto_ocr"] = texto_ocr

    return resultado


# ============================================================
# TRANSCRIÇÃO DE ÁUDIO
# ============================================================

def transcrever_audio(
    conteudo,
    mime_type="audio/ogg"
):

    if EM_RENDER:

        print(
            "FASTER-WHISPER DESATIVADO NO RENDER "
            "PARA EVITAR CONSUMO EXCESSIVO DE MEMÓRIA."
        )

        return {
            "ok": False,
            "erro": (
                "A transcrição de áudio está "
                "temporariamente desativada no servidor."
            )
        }

    arquivo_temp = None

    try:

        try:

            from faster_whisper import WhisperModel

        except ImportError:

            return {
                "ok": False,
                "erro": (
                    "A transcrição de áudio ainda "
                    "não está instalada. "
                    "Instale faster-whisper."
                )
            }

        extensao = ".ogg"

        mime_type = str(
            mime_type or ""
        ).lower()

        if "mpeg" in mime_type:

            extensao = ".mp3"

        elif "wav" in mime_type:

            extensao = ".wav"

        elif "mp4" in mime_type:

            extensao = ".m4a"

        elif "webm" in mime_type:

            extensao = ".webm"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extensao
        ) as arquivo:

            arquivo.write(
                conteudo
            )

            arquivo_temp = arquivo.name

        print(
            "INICIANDO FASTER-WHISPER..."
        )

        modelo = getattr(
            transcrever_audio,
            "_modelo_whisper",
            None
        )

        if modelo is None:

            print(
                "CARREGANDO MODELO FASTER-WHISPER..."
            )

            modelo = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8"
            )

            transcrever_audio._modelo_whisper = (
                modelo
            )

            print(
                "MODELO FASTER-WHISPER CARREGADO."
            )

        else:

            print(
                "REUTILIZANDO MODELO FASTER-WHISPER."
            )

        segmentos, info = modelo.transcribe(
            arquivo_temp,
            language="pt"
        )

        partes = []

        for segmento in segmentos:

            texto = str(
                segmento.text
            ).strip()

            if texto:

                partes.append(
                    texto
                )

        texto_transcrito = " ".join(
            partes
        ).strip()

        if not texto_transcrito:

            return {
                "ok": False,
                "erro": (
                    "Não consegui entender "
                    "o áudio."
                )
            }

        print(
            "ÁUDIO TRANSCRITO:",
            texto_transcrito
        )

        return {
            "ok": True,
            "texto": texto_transcrito
        }

    except Exception as exc:

        print(
            "ERRO TRANSCRIÇÃO:",
            exc
        )

        return {
            "ok": False,
            "erro": (
                "Erro ao transcrever o áudio: "
                f"{exc}"
            )
        }

    finally:

        if arquivo_temp:

            try:

                os.remove(
                    arquivo_temp
                )

            except Exception:

                pass


# ============================================================
# PROCESSAR ÁUDIO
# ============================================================

def processar_audio_whatsapp(
    media_id,
    numero
):

    conteudo, mime_type = baixar_midia_meta(
        media_id
    )

    if not conteudo:

        return {
            "ok": False,
            "tipo": "audio",
            "erro": (
                "Recebi o áudio, mas não consegui "
                "baixar o arquivo."
            )
        }

    resultado_audio = transcrever_audio(
        conteudo,
        mime_type or "audio/ogg"
    )

    if not resultado_audio.get(
        "ok"
    ):

        return {
            "ok": False,
            "tipo": "audio",
            "erro": resultado_audio.get(
                "erro",
                "Não consegui transcrever o áudio."
            )
        }

    texto = resultado_audio[
        "texto"
    ]

    resultado = analisar_texto_recebido(
        texto
    )

    resultado["tipo"] = "audio"
    resultado["texto_transcrito"] = texto

    return resultado


# ============================================================
# ASSINATURA META
# ============================================================

# ============================================================
# PROCESSAR DOCUMENTO WHATSAPP
# ============================================================

def processar_documento_whatsapp(
    media_id,
    numero,
    nome_arquivo="arquivo",
    mime_type="application/octet-stream"
):
    """
    Baixa um documento recebido pelo WhatsApp/Meta,
    salva temporariamente, tenta ler o conteúdo e
    devolve o texto extraído.
    """

    arquivo_temp = None

    try:
        arquivo = baixar_midia_meta(media_id)

        if not arquivo:
            return {
                "ok": False,
                "tipo": "documento",
                "erro": (
                    "Recebi o documento, mas não consegui "
                    "baixar o arquivo."
                )
            }

        # --------------------------------------------------------
        # Descobrir nome e extensão do arquivo
        # --------------------------------------------------------

        nome_arquivo = (
            nome_arquivo
            or "arquivo"
        )

        extensao = os.path.splitext(
            nome_arquivo
        )[1].lower()

        extensoes_por_mime = {
            "text/plain": ".txt",
            "text/csv": ".csv",
            "application/json": ".json",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        }

        if not extensao:
            extensao = extensoes_por_mime.get(
                mime_type,
                ""
            )

            if extensao:
                nome_arquivo = (
                    nome_arquivo
                    + extensao
                )

        # --------------------------------------------------------
        # Tipos de arquivo aceitos
        # --------------------------------------------------------

        extensoes_permitidas = {
            ".txt",
            ".csv",
            ".json",
            ".xlsx",
            ".pdf",
        }

        if extensao not in extensoes_permitidas:
            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Tipo de documento não suportado. "
                    "Envie um arquivo TXT, CSV, JSON, XLSX ou PDF."
                )
            }

        # --------------------------------------------------------
        # Criar arquivo temporário
        # --------------------------------------------------------

        arquivo_temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extensao
        )

        arquivo_temp.write(arquivo)
        arquivo_temp.close()

        # --------------------------------------------------------
        # Ler arquivo
        # --------------------------------------------------------

        resultado = ler_arquivo(
            arquivo_temp.name
        )

        if not resultado:
            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Não foi possível ler o conteúdo "
                    "do documento."
                )
            }

        if not resultado.get("ok"):
            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": resultado.get(
                    "erro",
                    "Não foi possível ler o documento."
                )
            }

        texto = resultado.get(
            "texto",
            ""
        )

        return {
            "ok": True,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "extensao": extensao,
            "texto": texto,
            "tamanho_texto": len(texto),
            "numero": numero,
            "mensagem": (
                "Documento recebido e lido com sucesso."
            )
        }

    except Exception as exc:
        return {
            "ok": False,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "erro": str(exc)
        }

    finally:
        if arquivo_temp:
            try:
                if os.path.exists(
                    arquivo_temp.name
                ):
                    os.remove(
                        arquivo_temp.name
                    )
            except Exception:
                pass


# ============================================================
# PROCESSAR DOCUMENTO WHATSAPP
# ============================================================

def processar_documento_whatsapp(
    media_id,
    numero,
    nome_arquivo="arquivo",
    mime_type="application/octet-stream"
):
    """
    Baixa um documento recebido pelo WhatsApp/Meta,
    salva temporariamente, lê o conteúdo e devolve
    o texto extraído.
    """

    arquivo_temp = None

    try:

        # baixar_midia_meta retorna:
        # (conteudo, mime_type)
        conteudo, mime_baixado = baixar_midia_meta(
            media_id
        )

        if not conteudo:

            return {
                "ok": False,
                "tipo": "documento",
                "erro": (
                    "Recebi o documento, mas não consegui "
                    "baixar o arquivo."
                )
            }

        # Se a Meta informou o MIME correto no download,
        # usamos ele.
        if mime_baixado:

            mime_type = mime_baixado

        nome_arquivo = (
            str(nome_arquivo or "arquivo")
            .strip()
        )

        if not nome_arquivo:

            nome_arquivo = "arquivo"

        # --------------------------------------------------------
        # DESCOBRIR EXTENSÃO
        # --------------------------------------------------------

        extensao = os.path.splitext(
            nome_arquivo
        )[1].lower()

        extensoes_por_mime = {
            "text/plain": ".txt",
            "text/csv": ".csv",
            "application/json": ".json",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.ms-excel": ".xls",
        }

        if not extensao:

            extensao = extensoes_por_mime.get(
                mime_type,
                ""
            )

            if extensao:

                nome_arquivo = (
                    nome_arquivo
                    + extensao
                )

        # --------------------------------------------------------
        # TIPOS ACEITOS
        # --------------------------------------------------------

        extensoes_permitidas = {
            ".txt",
            ".csv",
            ".json",
            ".xlsx",
            ".pdf",
        }

        if extensao not in extensoes_permitidas:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Tipo de documento não suportado. "
                    "Envie um arquivo TXT, CSV, JSON, XLSX ou PDF."
                )
            }

        # --------------------------------------------------------
        # CRIAR ARQUIVO TEMPORÁRIO
        # --------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extensao
        ) as arquivo:

            arquivo.write(
                conteudo
            )

            arquivo_temp = arquivo.name

        # --------------------------------------------------------
        # LER DOCUMENTO
        # --------------------------------------------------------

        resultado = ler_arquivo(
            arquivo_temp
        )

        if not resultado:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Não foi possível ler o conteúdo "
                    "do documento."
                )
            }

        if not resultado.get(
            "ok"
        ):

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": resultado.get(
                    "erro",
                    "Não foi possível ler o documento."
                )
            }

        texto = str(
            resultado.get(
                "texto",
                ""
            ) or ""
        ).strip()

        if not texto:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "O documento foi recebido, mas "
                    "não encontrei texto para analisar."
                )
            }

        return {
            "ok": True,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "extensao": extensao,
            "texto": texto,
            "tamanho_texto": len(texto),
            "numero": numero,
            "mensagem": (
                "Documento recebido e lido com sucesso."
            )
        }

    except Exception as exc:

        print(
            "ERRO AO PROCESSAR DOCUMENTO:",
            exc
        )

        return {
            "ok": False,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "erro": str(exc)
        }

    finally:

        if arquivo_temp:

            try:

                if os.path.exists(
                    arquivo_temp
                ):

                    os.remove(
                        arquivo_temp
                    )

            except Exception:

                pass


# ============================================================
# PROCESSAR DOCUMENTO WHATSAPP
# ============================================================

def processar_documento_whatsapp(
    media_id,
    numero,
    nome_arquivo="arquivo",
    mime_type="application/octet-stream"
):
    """
    Baixa um documento recebido pelo WhatsApp/Meta,
    salva temporariamente, lê o conteúdo e devolve
    o texto extraído.
    """

    arquivo_temp = None

    try:

        # baixar_midia_meta retorna:
        # (conteudo, mime_type)
        conteudo, mime_baixado = baixar_midia_meta(
            media_id
        )

        if not conteudo:

            return {
                "ok": False,
                "tipo": "documento",
                "erro": (
                    "Recebi o documento, mas não consegui "
                    "baixar o arquivo."
                )
            }

        if mime_baixado:

            mime_type = mime_baixado

        nome_arquivo = str(
            nome_arquivo or "arquivo"
        ).strip()

        if not nome_arquivo:

            nome_arquivo = "arquivo"

        # --------------------------------------------------------
        # DESCOBRIR EXTENSÃO
        # --------------------------------------------------------

        extensao = os.path.splitext(
            nome_arquivo
        )[1].lower()

        extensoes_por_mime = {
            "text/plain": ".txt",
            "text/csv": ".csv",
            "application/json": ".json",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.ms-excel": ".xls",
        }

        if not extensao:

            extensao = extensoes_por_mime.get(
                mime_type,
                ""
            )

            if extensao:

                nome_arquivo = (
                    nome_arquivo
                    + extensao
                )

        # --------------------------------------------------------
        # TIPOS ACEITOS
        # --------------------------------------------------------

        extensoes_permitidas = {
            ".txt",
            ".csv",
            ".json",
            ".xlsx",
            ".pdf",
        }

        if extensao not in extensoes_permitidas:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Tipo de documento não suportado. "
                    "Envie um arquivo TXT, CSV, JSON, XLSX ou PDF."
                )
            }

        # --------------------------------------------------------
        # CRIAR ARQUIVO TEMPORÁRIO
        # --------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extensao
        ) as arquivo:

            arquivo.write(
                conteudo
            )

            arquivo_temp = arquivo.name

        # --------------------------------------------------------
        # LER DOCUMENTO
        # --------------------------------------------------------

        resultado = ler_arquivo(
            arquivo_temp
        )

        if not resultado:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "Não foi possível ler o conteúdo "
                    "do documento."
                )
            }

        if not resultado.get(
            "ok"
        ):

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": resultado.get(
                    "erro",
                    "Não foi possível ler o documento."
                )
            }

        texto = str(
            resultado.get(
                "texto",
                ""
            ) or ""
        ).strip()

        if not texto:

            return {
                "ok": False,
                "tipo": "documento",
                "arquivo": nome_arquivo,
                "erro": (
                    "O documento foi recebido, mas "
                    "não encontrei texto para analisar."
                )
            }

        return {
            "ok": True,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "extensao": extensao,
            "texto": texto,
            "tamanho_texto": len(texto),
            "numero": numero,
            "mensagem": (
                "Documento recebido e lido com sucesso."
            )
        }

    except Exception as exc:

        print(
            "ERRO AO PROCESSAR DOCUMENTO:",
            exc
        )

        return {
            "ok": False,
            "tipo": "documento",
            "arquivo": nome_arquivo,
            "erro": str(exc)
        }

    finally:

        if arquivo_temp:

            try:

                if os.path.exists(
                    arquivo_temp
                ):

                    os.remove(
                        arquivo_temp
                    )

            except Exception:

                pass


# ============================================================
# ASSINATURA META
# ============================================================

def verificar_assinatura_meta():

    if not WHATSAPP_APP_SECRET:

        return True

    assinatura = request.headers.get(
        "X-Hub-Signature-256",
        ""
    )

    if not assinatura.startswith(
        "sha256="
    ):

        return False

    corpo = request.get_data()

    calculada = hmac.new(
        WHATSAPP_APP_SECRET.encode(
            "utf-8"
        ),
        corpo,
        hashlib.sha256
    ).hexdigest()

    esperada = (
        f"sha256={calculada}"
    )

    return hmac.compare_digest(
        assinatura,
        esperada
    )


# ============================================================
# PROCESSAR WEBHOOK META
# ============================================================

def processar_webhook_meta(
    dados
):

    mensagens_processadas = []

    if not isinstance(
        dados,
        dict
    ):

        return mensagens_processadas

    entradas = dados.get(
        "entry",
        []
    )

    for entrada in entradas:

        if not isinstance(
            entrada,
            dict
        ):

            continue

        changes = entrada.get(
            "changes",
            []
        )

        for change in changes:

            if not isinstance(
                change,
                dict
            ):

                continue

            value = change.get(
                "value",
                {}
            )

            if not isinstance(
                value,
                dict
            ):

                continue

            mensagens = value.get(
                "messages",
                []
            )

            for mensagem in mensagens:

                if not isinstance(
                    mensagem,
                    dict
                ):

                    continue

                tipo = mensagem.get(
                    "type"
                )

                numero = mensagem.get(
                    "from"
                )

                message_id = mensagem.get(
                    "id"
                )

                if message_id:

                    if message_id in MENSAGENS_PROCESSADAS:

                        print(
                            "MENSAGEM JÁ PROCESSADA:",
                            message_id
                        )

                        continue

                    MENSAGENS_PROCESSADAS.add(
                        message_id
                    )

                resultado = None

                if tipo == "text":

                    texto = (
                        mensagem
                        .get(
                            "text",
                            {}
                        )
                        .get(
                            "body",
                            ""
                        )
                        .strip()
                    )

                    if texto:

                        consulta = (
                            processar_consulta_financeira(
                                texto
                            )
                        )

                        if consulta:

                            resultado = consulta

                        else:

                            resultado = (
                                analisar_texto_recebido(
                                    texto
                                )
                            )

                elif tipo == "image":

                    imagem = mensagem.get(
                        "image",
                        {}
                    )

                    media_id = imagem.get(
                        "id"
                    )

                    legenda = imagem.get(
                        "caption",
                        ""
                    )

                    if media_id:

                        resultado = (
                            processar_foto_whatsapp(
                                media_id,
                                numero,
                                legenda
                            )
                        )

                    else:

                        resultado = {
                            "ok": False,
                            "tipo": "foto",
                            "erro": (
                                "A Meta não enviou "
                                "o identificador da imagem."
                            )
                        }

                elif tipo == "audio":

                    audio = mensagem.get(
                        "audio",
                        {}
                    )

                    media_id = audio.get(
                        "id"
                    )

                    if media_id:

                        resultado = (
                            processar_audio_whatsapp(
                                media_id,
                                numero
                            )
                        )

                    else:

                        resultado = {
                            "ok": False,
                            "tipo": "audio",
                            "erro": (
                                "A Meta não enviou "
                                "o identificador do áudio."
                            )
                        }

                else:

                    print(
                        "TIPO DE MENSAGEM NÃO SUPORTADO:",
                        tipo
                    )

                    continue

                if not resultado:

                    continue

                resultado["numero"] = numero

                resultado["message_id"] = (
                    message_id
                )

                mensagens_processadas.append(
                    resultado
)             
                if numero and resultado.get(
                    "ok"
                ):

                    tipo_lancamento = resultado.get(
                        "tipo_lancamento",
                        resultado.get(
                            "tipo",
                            "despesa"
                        )
                    )

                    tipo_mensagem = resultado.get(
                        "tipo_mensagem",
                        tipo
                    )

                    if tipo_lancamento == "consulta":

                        resposta = resultado.get(
                            "resposta",
                            (
                                "Sorroche Finanças\n\n"
                                "Consulta realizada."
                            )
                        )

                        valor = float(
                            receita.get(
                                "valor",
                                0
                            )
                        )

                        categoria = receita.get(
                            "categoria",
                            "Outros"
                        )

                        descricao = receita.get(
                            "descricao",
                            ""
                        )

                        resposta = (
                            "Sorroche Finanças\n\n"
                            "Receita registrada!\n\n"
                            f"Valor: {formatar_reais(valor)}\n"
                            f"Categoria: {categoria}\n"
                            f"Descrição: {descricao}\n\n"
                            "Entrada de dinheiro registrada "
                            "no sistema."
                        )

                    else:

                        despesa = resultado.get(
                            "despesa",
                            {}
                        )

                        valor = float(
                            despesa.get(
                                "valor",
                                0
                            )
                        )

                        categoria = despesa.get(
                            "categoria",
                            "Outros"
                        )

                        forma_pagamento = (
                            despesa.get(
                                "forma_pagamento",
                                "Outro"
                            )
                        )

                        descricao = despesa.get(
                            "descricao",
                            ""
                        )

                        pasta = despesa.get(
                            "pasta",
                            None
                        )

                        if tipo_mensagem == "foto":

                            origem = (
                                "Foto analisada por OCR."
                            )

                        elif tipo_mensagem == "audio":

                            origem = (
                                "Áudio transcrito e analisado."
                            )

                        else:

                            origem = (
                                "Mensagem analisada pela IA."
                            )

                        if pasta:

                            informacao_pasta = (
                                f"Pasta: {pasta}"
                            )

                        else:

                            informacao_pasta = (
                                "Pasta: não vinculada"
                            )

                        resposta = (
                            "Sorroche Finanças\n\n"
                            "Despesa registrada!\n\n"
                            f"Valor: {formatar_reais(valor)}\n"
                            f"Categoria: {categoria}\n"
                            f"Pagamento: {forma_pagamento}\n"
                            f"Descrição: {descricao}\n"
                            f"{informacao_pasta}\n\n"
                            f"{origem}"
                        )

                    envio = enviar_mensagem_whatsapp(
                        numero,
                        resposta
                    )

                    resultado[
                        "resposta_whatsapp"
                    ] = envio

                elif numero:

                    erro = resultado.get(
                        "erro",
                        "Não foi possível processar a mensagem."
                    )

                    envio = enviar_mensagem_whatsapp(
                        numero,
                        (
                            "Sorroche Finanças\n\n"
                            "Não consegui registrar "
                            "essa informação.\n\n"
                            f"{erro}"
                        )
                    )

                    resultado[
                        "resposta_whatsapp"
                    ] = envio

    return mensagens_processadas


# ============================================================
# STATUS
# ============================================================

@whatsapp.route(
    "/",
    methods=["GET"]
)
def index():

    return jsonify({
        "ok": True,
        "modulo": "WhatsApp",
        "status": "funcionando",
        "numero_qr": WHATSAPP_NUMERO,
        "recursos": [
            "texto",
            "foto",
            "audio",
            "webhook_meta",
            "qr_code",
            "ollama",
            "ocr",
            "pastas",
            "receitas",
            "despesas",
            "consultas_financeiras"
        ],
        "consultas": [
            "quanto recebi esse mês",
            "quanto gastei esse mês",
            "quanto sobrou esse mês",
            "quanto tenho para gastar",
            "quais foram minhas despesas",
            "quais foram minhas receitas",
            "quanto gastei no Mercado",
            "quanto gastei no cartão",
            "quanto tenho nas metas",
            "quanto investi"
        ],
        "ia": {
            "modelo": OLLAMA_MODEL,
            "url": OLLAMA_URL,
            "ativo": OLLAMA_ATIVO,
            "render": EM_RENDER
        },
        "ocr_configurado": bool(
            OCR_SPACE_API_KEY
        ),
        "meta_configurada": bool(
            WHATSAPP_ACCESS_TOKEN
            and WHATSAPP_PHONE_NUMBER_ID
        ),
        "graph_version": (
            WHATSAPP_GRAPH_VERSION
        )
    })


# ============================================================
# TESTE INTERNO
# ============================================================

@whatsapp.route(
    "/teste",
    methods=["POST"]
)
def teste():

    dados = request.get_json(
        silent=True
    ) or {}

    mensagem = str(
        dados.get(
            "mensagem",
            ""
        )
    ).strip()

    if not mensagem:

        return jsonify({
            "ok": False,
            "erro": (
                "Informe a mensagem."
            )
        }), 400

    consulta = processar_consulta_financeira(
        mensagem
    )

    if consulta:

        if not consulta.get(
            "ok"
        ):

            return jsonify(
                consulta
            ), 400

        return jsonify(
            consulta
        )

    resultado = analisar_texto_recebido(
        mensagem
    )

    if not resultado.get(
        "ok"
    ):

        return jsonify(
            resultado
        ), 400

    return jsonify(
        resultado
    )


# ============================================================
# TESTE DE FOTO MANUAL
# ============================================================

@whatsapp.route(
    "/foto",
    methods=["POST"]
)
def receber_foto():

    arquivo = request.files.get(
        "imagem"
    )

    if not arquivo or not arquivo.filename:

        arquivo = request.files.get(
            "foto"
        )

    if not arquivo or not arquivo.filename:

        return jsonify({
            "ok": False,
            "erro": (
                "Nenhuma foto foi enviada."
            )
        }), 400

    try:

        conteudo = arquivo.read()

        if not conteudo:

            return jsonify({
                "ok": False,
                "erro": (
                    "A foto recebida está vazia."
                )
            }), 400

        resultado = extrair_texto_imagem(
            conteudo,
            arquivo.filename,
            arquivo.mimetype
            or "image/jpeg"
        )

        if not resultado.get(
            "ok"
        ):

            return jsonify(
                resultado
            ), 400

        texto_ocr = resultado[
            "texto"
        ]

        dados_lancamento = (
            analisar_texto_recebido(
                texto_ocr
            )
        )

        return jsonify({
            "ok": True,
            "tipo": "foto",
            "texto_ocr": texto_ocr,
            "resultado": dados_lancamento
        })

    except Exception as exc:

        db.session.rollback()

        return jsonify({
            "ok": False,
            "erro": (
                "Erro ao processar a foto: "
                f"{exc}"
            )
        }), 500


# ============================================================
# TESTE DE ÁUDIO MANUAL
# ============================================================

@whatsapp.route(
    "/audio",
    methods=["POST"]
)
def receber_audio():

    arquivo = request.files.get(
        "audio"
    )

    if not arquivo or not arquivo.filename:

        arquivo = request.files.get(
            "file"
        )

    if not arquivo or not arquivo.filename:

        return jsonify({
            "ok": False,
            "erro": (
                "Nenhum áudio foi enviado."
            )
        }), 400

    try:

        conteudo = arquivo.read()

        if not conteudo:

            return jsonify({
                "ok": False,
                "erro": (
                    "O áudio recebido está vazio."
                )
            }), 400

        resultado = transcrever_audio(
            conteudo,
            arquivo.mimetype
            or "audio/ogg"
        )

        if not resultado.get(
            "ok"
        ):

            return jsonify(
                resultado
            ), 400

        texto = resultado[
            "texto"
        ]

        dados_lancamento = (
            analisar_texto_recebido(
                texto
            )
        )

        return jsonify({
            "ok": True,
            "tipo": "audio",
            "texto_transcrito": texto,
            "resultado": dados_lancamento
        })

    except Exception as exc:

        db.session.rollback()

        return jsonify({
            "ok": False,
            "erro": (
                "Erro ao processar o áudio: "
                f"{exc}"
            )
        }), 500


# ============================================================
# WEBHOOK META
# ============================================================

@whatsapp.route(
    "/webhook",
    methods=["GET", "POST"]
)
def webhook():

    if request.method == "GET":

        modo = request.args.get(
            "hub.mode"
        )

        token = request.args.get(
            "hub.verify_token"
        )

        desafio = request.args.get(
            "hub.challenge"
        )

        if (
            modo == "subscribe"
            and token == WHATSAPP_VERIFY_TOKEN
        ):

            return desafio or "", 200

        return jsonify({
            "ok": False,
            "erro": (
                "Token de verificação inválido."
            )
        }), 403

    if not verificar_assinatura_meta():

        return jsonify({
            "ok": False,
            "erro": (
                "Assinatura do webhook inválida."
            )
        }), 401

    dados = request.get_json(
        silent=True
    ) or {}

    print(
        "WEBHOOK WHATSAPP RECEBIDO:"
    )

    print(
        json.dumps(
            dados,
            ensure_ascii=False
        )
    )

    resultados = processar_webhook_meta(
        dados
    )

    print(
        "WEBHOOK PROCESSADO:"
    )

    print(
        json.dumps(
            resultados,
            ensure_ascii=False
        )
    )

    return jsonify({
        "ok": True,
        "mensagem": (
            "Webhook recebido com sucesso."
        ),
        "processados": resultados
    }), 200