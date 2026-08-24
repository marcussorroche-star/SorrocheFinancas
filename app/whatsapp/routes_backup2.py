import os
import re
import hmac
import hashlib
import json
import tempfile
from datetime import date

import requests
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, render_template

from app import db
from app.despesas.models import Despesa
from app.receitas.models import Receita
from app.pastas.models import Pasta


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
# WHATSAPP META
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
# OCR
# ============================================================

OCR_SPACE_API_KEY = os.getenv(
    "OCR_SPACE_API_KEY",
    ""
)


# ============================================================
# IDENTIFICAR RECEITA
# ============================================================

def mensagem_e_receita(texto):
    """
    Identifica frases que representam entrada de dinheiro.

    Exemplos:
    - recebi 5000 de salario
    - recebi 3000 reais
    - ganhei 2000
    - salário recebido 5000
    - entrou 1500 na conta
    - recebi pagamento de 2500
    - recebi meu pagamento
    """

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
        "salário",
        "salario",
        "pagamento recebido",
        "pagamento",
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

    # Frases explícitas de despesa têm prioridade.
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

    tipo_sugerido = (
        "RECEITA"
        if mensagem_e_receita(texto)
        else "DESPESA"
    )

    prompt = f"""
Você é a IA financeira do sistema Sorroche Finanças.

Analise a mensagem recebida abaixo.

Mensagem:
{texto}

O sistema identificou inicialmente esta intenção:
{tipo_sugerido}

IMPORTANTE:

Se a mensagem indicar dinheiro RECEBIDO, GANHO, SALÁRIO,
PAGAMENTO RECEBIDO, RENDA, LUCRO, COMISSÃO, BONIFICAÇÃO
ou entrada de dinheiro, o tipo deve ser "receita".

Se a mensagem indicar dinheiro GASTO, PAGO, COMPRADO,
CONTA, MERCADO, GASOLINA, FARMÁCIA ou outra saída de
dinheiro, o tipo deve ser "despesa".

Identifique:

1. tipo
2. valor
3. categoria
4. forma de pagamento
5. descrição

Para receitas, categorias possíveis:

Salário
Pagamento
Renda
Lucro
Comissão
Investimentos
Outros

Para despesas, categorias possíveis:

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

Formas de pagamento possíveis:

Cartão
Pix
Dinheiro
Boleto
Outro

Responda SOMENTE com JSON válido.

Formato obrigatório:

{{
    "tipo": "despesa",
    "valor": 0,
    "categoria": "Outros",
    "forma_pagamento": "Outro",
    "descricao": "descrição"
}}

Se for uma receita, use:

{{
    "tipo": "receita",
    "valor": 0,
    "categoria": "Salário",
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
            timeout=120
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

        texto_json = texto_resposta[
            inicio:fim + 1
        ]

        resultado = json.loads(
            texto_json
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

        valor = float(valor)

        tipo = str(
            resultado.get(
                "tipo",
                tipo_sugerido
            )
        ).strip().lower()

        # Proteção contra erro da IA.
        # A identificação local tem prioridade para
        # frases claramente reconhecidas como receita.
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

        # Corrige categoria para receitas quando a IA
        # retornar categoria inadequada.
        if tipo == "receita":

            categorias_receita = [
                "Salário",
                "Pagamento",
                "Renda",
                "Lucro",
                "Comissão",
                "Investimentos",
                "Outros"
            ]

            categoria_lower = categoria.lower()

            if (
                categoria_lower not in [
                    item.lower()
                    for item in categorias_receita
                ]
            ):

                texto_lower = texto.lower()

                if (
                    "salário" in texto_lower
                    or "salario" in texto_lower
                ):

                    categoria = "Salário"

                elif "pagamento" in texto_lower:

                    categoria = "Pagamento"

                else:

                    categoria = "Outros"

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

    texto = (
        texto or ""
    ).strip()

    if not texto:
        return None

    tipo_local = (
        "receita"
        if mensagem_e_receita(texto)
        else "despesa"
    )

    resultado_ia = consultar_ia(
        texto
    )

    if resultado_ia:

        # A identificação local de uma frase explícita
        # de recebimento sempre vence uma interpretação
        # errada da IA.
        if tipo_local == "receita":

            resultado_ia["tipo"] = "receita"

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

        forma_pagamento = "Pix"

    elif "dinheiro" in texto_lower:

        forma_pagamento = "Dinheiro"

    elif "boleto" in texto_lower:

        forma_pagamento = "Boleto"

    # ========================================================
    # RECEITA
    # ========================================================

    if tipo_local == "receita":

        categoria = "Outros"

        if (
            "salário" in texto_lower
            or "salario" in texto_lower
        ):

            categoria = "Salário"

        elif "pagamento" in texto_lower:

            categoria = "Pagamento"

        elif "lucro" in texto_lower:

            categoria = "Lucro"

        elif "comissão" in texto_lower:

            categoria = "Comissão"

        elif "comissao" in texto_lower:

            categoria = "Comissão"

        elif "renda" in texto_lower:

            categoria = "Renda"

        return {
            "tipo": "receita",
            "descricao": texto,
            "categoria": categoria,
            "valor": valor,
            "forma_pagamento": forma_pagamento,
            "ia": False
        }

    # ========================================================
    # DESPESA
    # ========================================================

    categoria = "Outros"

    if any(
        palavra in texto_lower
        for palavra in [
            "mercado",
            "supermercado",
            "compras",
            "compra de mercado"
        ]
    ):

        categoria = "Mercado"

    elif any(
        palavra in texto_lower
        for palavra in [
            "farmácia",
            "farmacia",
            "remédio",
            "remedio"
        ]
    ):

        categoria = "Farmácia"

    elif any(
        palavra in texto_lower
        for palavra in [
            "combustível",
            "combustivel",
            "gasolina",
            "posto"
        ]
    ):

        categoria = "Combustível"

    return {
        "tipo": "despesa",
        "descricao": texto,
        "categoria": categoria,
        "valor": valor,
        "forma_pagamento": forma_pagamento,
        "ia": False
    }


# ============================================================
# LOCALIZAR PASTA DA CATEGORIA
# ============================================================

def encontrar_pasta_categoria(categoria):

    categoria = str(
        categoria or ""
    ).strip()

    if not categoria:
        return None

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

        print(
            "NENHUMA PASTA ENCONTRADA PARA A CATEGORIA:",
            categoria
        )

        return None

    except Exception as exc:

        print(
            "ERRO AO LOCALIZAR PASTA:",
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

    pasta = encontrar_pasta_categoria(
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

    # Alguns projetos podem possuir categoria e forma
    # de pagamento no modelo Receita. Para manter
    # compatibilidade, verificamos os campos existentes.

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

        # ====================================================
        # RECEITA
        # ====================================================

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

        # ====================================================
        # DESPESA
        # ====================================================

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
# BAIXAR MÍDIA DA META
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
# OCR DA IMAGEM
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
# PROCESSAR FOTO RECEBIDA PELO WHATSAPP
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

    arquivo_temp = None

    try:

        try:

            from faster_whisper import (
                WhisperModel
            )

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

        modelo = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
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
# PROCESSAR ÁUDIO RECEBIDO PELO WHATSAPP
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

def verificar_assinatura_meta():

    if not WHATSAPP_APP_SECRET:

        return True

    assinatura = request.headers.get(
        "X-Hub-Signature-256",
        ""
    )

    if not assinatura:

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

                resultado = None

                # ====================================================
                # TEXTO
                # ====================================================

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

                        resultado = (
                            analisar_texto_recebido(
                                texto
                            )
                        )

                # ====================================================
                # IMAGEM
                # ====================================================

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

                # ====================================================
                # ÁUDIO
                # ====================================================

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

                # ====================================================
                # RESPOSTA AUTOMÁTICA
                # ====================================================

                if numero and resultado.get(
                    "ok"
                ):

                    tipo_lancamento = resultado.get(
                        "tipo",
                        "despesa"
                    )

                    tipo_mensagem = resultado.get(
                        "tipo",
                        "texto"
                    )

                    # =================================================
                    # RECEITA
                    # =================================================

                    if (
                        tipo_lancamento
                        == "receita"
                    ):

                        receita = resultado.get(
                            "receita",
                            {}
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
                            f"Valor: R$ {valor:.2f}\n"
                            f"Categoria: {categoria}\n"
                            f"Descrição: {descricao}\n\n"
                            "Entrada de dinheiro registrada "
                            "no sistema."
                        )

                    # =================================================
                    # DESPESA
                    # =================================================

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
                            f"Valor: R$ {valor:.2f}\n"
                            f"Categoria: {categoria}\n"
                            f"Pagamento: {forma_pagamento}\n"
                            f"Descrição: {descricao}\n"
                            f"{informacao_pasta}\n\n"
                            f"{origem}"
                        )

                    envio = (
                        enviar_mensagem_whatsapp(
                            numero,
                            resposta
                        )
                    )

                    resultado[
                        "resposta_whatsapp"
                    ] = envio

                elif numero:

                    erro = resultado.get(
                        "erro",
                        "Não foi possível processar a mensagem."
                    )

                    envio = (
                        enviar_mensagem_whatsapp(
                            numero,
                            (
                                "Sorroche Finanças\n\n"
                                "Não consegui registrar "
                                "essa informação.\n\n"
                                f"{erro}"
                            )
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
            "despesas"
        ],
        "ia": {
            "modelo": OLLAMA_MODEL,
            "url": OLLAMA_URL
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

    # --------------------------------------------------------
    # VERIFICAÇÃO DA META
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ASSINATURA
    # --------------------------------------------------------

    if not verificar_assinatura_meta():

        return jsonify({
            "ok": False,
            "erro": (
                "Assinatura do webhook inválida."
            )
        }), 401

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PROCESSAMENTO
    # --------------------------------------------------------

    resultados = (
        processar_webhook_meta(
            dados
        )
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

    # --------------------------------------------------------
    # RESPOSTA PARA META
    # --------------------------------------------------------

    return jsonify({
        "ok": True,
        "mensagem": (
            "Webhook recebido com sucesso."
        ),
        "processados": resultados
    }), 200