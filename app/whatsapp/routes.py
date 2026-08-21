import os
import re
import hmac
import hashlib
import json
from datetime import date

import requests
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, render_template

from app import db
from app.despesas.models import Despesa


# ============================================================
# CARREGAR .ENV CORRETAMENTE
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
# CONFIGURAÇÕES WHATSAPP / META
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
# CONFIGURAÇÃO IA - OLLAMA
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
# IA - OLLAMA
# ============================================================

def consultar_ia(texto):

    prompt = f"""
Você é a IA financeira do sistema Sorroche Finanças.

Analise a mensagem recebida abaixo.

Mensagem:
{texto}

Identifique:

1. valor
2. categoria
3. forma de pagamento
4. descrição

Categorias possíveis:
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

Responda SOMENTE com JSON válido, sem explicações.

Formato obrigatório:

{{
  "valor": 0,
  "categoria": "Outros",
  "forma_pagamento": "Outro",
  "descricao": "descrição da compra"
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

        texto_resposta = (
            dados.get("response", "")
            .strip()
        )

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

        valor = resultado.get("valor")

        if valor is None:
            return None

        if isinstance(valor, str):

            valor = (
                valor
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

        valor = float(valor)

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

        return {
            "descricao": descricao,
            "categoria": categoria,
            "valor": valor,
            "forma_pagamento": forma_pagamento,
            "ia": True
        }

    except Exception:

        return None


# ============================================================
# INTERPRETAR MENSAGEM
# ============================================================

def interpretar_mensagem(texto):

    texto = (texto or "").strip()

    if not texto:
        return None

    resultado_ia = consultar_ia(texto)

    if resultado_ia:
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
        "descricao": texto,
        "categoria": categoria,
        "valor": valor,
        "forma_pagamento": forma_pagamento,
        "ia": False
    }


# ============================================================
# CRIAR DESPESA
# ============================================================

def criar_despesa(dados_interpretados):

    despesa = Despesa(
        descricao=dados_interpretados["descricao"],
        categoria=dados_interpretados["categoria"],
        valor=dados_interpretados["valor"],
        data=date.today(),
        vencimento=None,
        forma_pagamento=dados_interpretados[
            "forma_pagamento"
        ],
        status="Pendente",
        usuario_id=1
    )

    db.session.add(despesa)
    db.session.commit()

    return despesa


# ============================================================
# RESPOSTA DA DESPESA
# ============================================================

def resposta_despesa(despesa):

    return {
        "id": despesa.id,
        "descricao": despesa.descricao,
        "categoria": despesa.categoria,
        "valor": despesa.valor,
        "forma_pagamento": despesa.forma_pagamento,
        "status": despesa.status
    }


# ============================================================
# ANALISAR TEXTO
# ============================================================

def analisar_texto_recebido(texto):

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

        despesa = criar_despesa(
            dados
        )

        return {
            "ok": True,
            "mensagem": (
                "Despesa criada com sucesso."
            ),
            "tipo": "texto",
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

        return {
            "ok": False,
            "erro": (
                "Erro ao salvar a despesa: "
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
            dados = {}

        if resposta.status_code >= 400:

            return {
                "ok": False,
                "enviado": False,
                "status_code": resposta.status_code,
                "erro": dados
            }

        return {
            "ok": True,
            "enviado": True,
            "dados": dados
        }

    except requests.exceptions.RequestException as exc:

        return {
            "ok": False,
            "enviado": False,
            "erro": str(exc)
        }


# ============================================================
# VERIFICAR ASSINATURA META
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
        WHATSAPP_APP_SECRET.encode("utf-8"),
        corpo,
        hashlib.sha256
    ).hexdigest()

    esperada = f"sha256={calculada}"

    return hmac.compare_digest(
        assinatura,
        esperada
    )


# ============================================================
# PROCESSAR WEBHOOK META
# ============================================================

def processar_webhook_meta(dados):

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

                if tipo != "text":
                    continue

                texto = (
                    mensagem
                    .get("text", {})
                    .get("body", "")
                    .strip()
                )

                if not texto:
                    continue

                resultado = (
                    analisar_texto_recebido(
                        texto
                    )
                )

                resultado["numero"] = numero

                resultado["message_id"] = (
                    mensagem.get("id")
                )

                mensagens_processadas.append(
                    resultado
                )

                if numero and resultado.get(
                    "ok"
                ):

                    despesa = resultado.get(
                        "despesa",
                        {}
                    )

                    valor = despesa.get(
                        "valor",
                        0
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

                    resposta = (
                        "✅ Sorroche Finanças\n\n"
                        "Despesa registrada!\n\n"
                        f"💰 Valor: R$ {valor:.2f}\n"
                        f"📂 Categoria: {categoria}\n"
                        f"💳 Pagamento: "
                        f"{forma_pagamento}\n"
                        f"📝 Descrição: {texto}\n\n"
                        "🤖 Analisado pela IA "
                        "do Sorroche."
                    )

                    enviar_mensagem_whatsapp(
                        numero,
                        resposta
                    )

                elif numero:

                    enviar_mensagem_whatsapp(
                        numero,
                        (
                            "❌ Não consegui "
                            "registrar essa despesa.\n\n"
                            f"{resultado.get('erro', '')}"
                        )
                    )

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
            "ollama"
        ],
        "ia": {
            "modelo": OLLAMA_MODEL,
            "url": OLLAMA_URL
        },
        "meta_configurada": bool(
            WHATSAPP_ACCESS_TOKEN
            and WHATSAPP_PHONE_NUMBER_ID
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
            "erro": "Informe a mensagem."
        }), 400

    resultado = (
        analisar_texto_recebido(
            mensagem
        )
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
# RECEBER FOTO / OCR
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
            "erro": "Nenhuma foto foi enviada."
        }), 400

    try:

        conteudo = arquivo.read()

        if not conteudo:

            return jsonify({
                "ok": False,
                "erro": "A foto recebida está vazia."
            }), 400

        api_key = os.getenv(
            "OCR_SPACE_API_KEY",
            ""
        )

        if (
            not api_key
            or api_key.startswith("COLE_")
        ):

            return jsonify({
                "ok": False,
                "erro": (
                    "OCR_SPACE_API_KEY "
                    "não está configurada."
                )
            }), 500

        resposta = requests.post(
            "https://api.ocr.space/parse/image",
            files={
                "file": (
                    arquivo.filename,
                    conteudo,
                    arquivo.mimetype
                    or "application/octet-stream"
                )
            },
            data={
                "apikey": api_key,
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

            mensagens = dados.get(
                "ErrorMessage"
            )

            if isinstance(
                mensagens,
                list
            ):

                mensagens = " ".join(
                    str(item)
                    for item in mensagens
                )

            return jsonify({
                "ok": False,
                "erro": (
                    mensagens
                    or (
                        "O serviço OCR retornou "
                        f"HTTP {resposta.status_code}."
                    )
                )
            }), 502

        if dados.get(
            "IsErroredOnProcessing"
        ):

            mensagens = dados.get(
                "ErrorMessage"
            )

            if isinstance(
                mensagens,
                list
            ):

                mensagens = " ".join(
                    str(item)
                    for item in mensagens
                )

            return jsonify({
                "ok": False,
                "erro": (
                    mensagens
                    or (
                        "O OCR não conseguiu "
                        "processar a foto."
                    )
                )
            }), 400

        resultados = dados.get(
            "ParsedResults"
        ) or []

        textos = []

        for resultado in resultados:

            texto = resultado.get(
                "ParsedText",
                ""
            ).strip()

            if texto:
                textos.append(
                    texto
                )

        texto_ocr = "\n\n".join(
            textos
        ).strip()

        if not texto_ocr:

            return jsonify({
                "ok": True,
                "tipo": "foto",
                "mensagem": (
                    "A foto foi recebida, "
                    "mas nenhum texto foi identificado."
                ),
                "texto_ocr": ""
            })

        return jsonify({
            "ok": True,
            "tipo": "foto",
            "mensagem": (
                "Foto recebida e analisada "
                "com sucesso."
            ),
            "texto_ocr": texto_ocr,
            "proxima_etapa": (
                "Interpretar os dados da compra."
            )
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "ok": False,
            "erro": (
                "O serviço de OCR demorou "
                "demais para responder."
            )
        }), 504

    except requests.exceptions.RequestException as exc:

        return jsonify({
            "ok": False,
            "erro": (
                "Não foi possível acessar "
                f"o OCR: {exc}"
            )
        }), 502

    except Exception as exc:

        return jsonify({
            "ok": False,
            "erro": (
                "Erro ao processar a foto: "
                f"{exc}"
            )
        }), 500


# ============================================================
# RECEBER ÁUDIO
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
            "erro": "Nenhum áudio foi enviado."
        }), 400

    try:

        conteudo = arquivo.read()

        if not conteudo:

            return jsonify({
                "ok": False,
                "erro": "O áudio recebido está vazio."
            }), 400

        extensao = os.path.splitext(
            arquivo.filename
        )[1].lower()

        formatos_permitidos = [
            ".ogg",
            ".oga",
            ".mp3",
            ".wav",
            ".m4a",
            ".webm",
            ".mp4"
        ]

        if extensao not in formatos_permitidos:

            return jsonify({
                "ok": False,
                "erro": (
                    "Formato de áudio "
                    "não reconhecido."
                ),
                "formatos_permitidos":
                    formatos_permitidos
            }), 400

        return jsonify({
            "ok": True,
            "tipo": "audio",
            "mensagem": (
                "Áudio recebido com sucesso."
            ),
            "arquivo": arquivo.filename,
            "tamanho": len(conteudo),
            "status": "aguardando_transcricao",
            "proxima_etapa": (
                "Transcrever o áudio e "
                "interpretar a compra."
            )
        })

    except Exception as exc:

        return jsonify({
            "ok": False,
            "erro": (
                "Erro ao receber o áudio: "
                f"{exc}"
            )
        }), 500


# ============================================================
# WEBHOOK WHATSAPP META
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
            ),
            "token_recebido": bool(token),
            "token_configurado": bool(
                WHATSAPP_VERIFY_TOKEN
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

    resultados = (
        processar_webhook_meta(
            dados
        )
    )

    return jsonify({
        "ok": True,
        "mensagem": (
            "Webhook recebido com sucesso."
        ),
        "processados": resultados
    }), 200