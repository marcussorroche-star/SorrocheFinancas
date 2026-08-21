import os

import requests
from flask import Blueprint, render_template, request
from dotenv import load_dotenv

from app.leitor.interpretador import interpretar_compra
from app.leitor.produtos import extrair_produtos

load_dotenv()

leitor = Blueprint(
    "leitor",
    __name__,
    url_prefix="/leitor",
    template_folder="templates"
)


@leitor.route("/", methods=["GET", "POST"])
def index():
    imagem_recebida = False
    texto_ocr = None
    erro = None

    compra = None
    produtos = []

    if request.method == "POST":
        imagem = request.files.get("imagem")

        if not imagem or not imagem.filename:
            erro = "Nenhuma imagem foi selecionada."

        else:
            imagem_recebida = True

            api_key = os.getenv("OCR_SPACE_API_KEY")

            if not api_key or api_key.startswith("COLE_"):
                erro = "A chave do OCR não está configurada corretamente."

            else:
                try:
                    imagem.seek(0)

                    resposta = requests.post(
                        "https://api.ocr.space/parse/image",
                        files={
                            "file": (
                                imagem.filename,
                                imagem.stream,
                                imagem.mimetype or "application/octet-stream"
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

                    resposta.raise_for_status()

                    dados = resposta.json()

                    if dados.get("IsErroredOnProcessing"):
                        mensagens = dados.get("ErrorMessage")

                        if isinstance(mensagens, list):
                            mensagens = " ".join(
                                str(item) for item in mensagens
                            )

                        erro = (
                            mensagens
                            or "O OCR não conseguiu processar a imagem."
                        )

                    else:
                        resultados = dados.get("ParsedResults") or []

                        textos = []

                        for resultado in resultados:
                            texto = resultado.get(
                                "ParsedText",
                                ""
                            ).strip()

                            if texto:
                                textos.append(texto)

                        texto_ocr = "\n\n".join(textos).strip()

                        if not texto_ocr:
                            erro = (
                                "A imagem foi recebida, mas o OCR "
                                "não encontrou texto legível."
                            )

                        else:
                            # Interpreta os dados gerais da compra.
                            compra = interpretar_compra(texto_ocr)

                            # Extrai os produtos encontrados na compra.
                            produtos = extrair_produtos(texto_ocr)

                except requests.exceptions.Timeout:
                    erro = (
                        "O serviço de OCR demorou demais para responder."
                    )

                except requests.exceptions.RequestException as exc:
                    erro = f"Não foi possível acessar o OCR: {exc}"

                except ValueError:
                    erro = "O OCR retornou uma resposta inválida."

                except Exception as exc:
                    erro = f"Erro ao analisar a compra: {exc}"

    return render_template(
        "leitor/index.html",
        imagem_recebida=imagem_recebida,
        texto_ocr=texto_ocr,
        erro=erro,
        compra=compra,
        produtos=produtos
    )