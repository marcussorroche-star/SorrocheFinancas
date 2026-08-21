import re
from datetime import datetime


CATEGORIAS = {
    "mercado": [
        "mercado",
        "supermercado",
        "hipermercado",
        "mercearia",
        "hortifruti",
        "atacarejo",
        "mattare",
        "mattar",
        "carrefour",
        "atacadao",
        "assai",
        "bh supermercado",
        "epa",
        "bahamas",
        "verdemar",
        "supernosso",
        "paodeacucar",
        "pao de acucar",
        "angeloni",
        "sams club",
        "sam's club",
    ],

    "saude": [
        "farmacia",
        "drogaria",
        "hospital",
        "clinica",
        "laboratorio",
        "medico",
        "medicina",
        "saude",
        "droga raia",
        "drogasil",
        "pague menos",
        "panvel",
    ],

    "casa": [
        "material de construcao",
        "construcao",
        "ferragem",
        "moveis",
        "moveis",
        "utilidades",
        "limpeza",
        "casa",
        "leroy merlin",
        "telhanorte",
        "madeira madeira",
        "tok stok",
        "camicado",
    ],

    "transporte": [
        "posto",
        "combustivel",
        "gasolina",
        "etanol",
        "diesel",
        "estacionamento",
        "uber",
        "99",
        "taxi",
        "pedagio",
        "shell",
        "ipiranga",
        "br distribuidora",
        "ale",
    ],

    "alimentacao": [
        "restaurante",
        "lanchonete",
        "padaria",
        "pizzaria",
        "hamburguer",
        "ifood",
        "cafe",
        "bar",
        "churrascaria",
        "sorveteria",
        "subway",
        "mcdonald",
        "burger king",
        "habibs",
    ],

    "roupas": [
        "roupas",
        "vestuario",
        "calcados",
        "sapatos",
        "moda",
        "boutique",
        "renner",
        "riachuelo",
        "c&a",
        "cea",
        "marisa",
        "hering",
    ],

    "educacao": [
        "escola",
        "faculdade",
        "universidade",
        "curso",
        "livraria",
        "papelaria",
        "educacao",
        "senac",
        "senai",
    ],

    "pets": [
        "petshop",
        "pet shop",
        "veterinaria",
        "veterinario",
        "racao",
        "cobasi",
        "petz",
    ],

    "lazer": [
        "cinema",
        "teatro",
        "parque",
        "jogos",
        "lazer",
        "show",
        "ingresso",
    ],

    "telefonia_internet": [
        "telefonia",
        "internet",
        "celular",
        "claro",
        "vivo",
        "tim",
        "oi",
    ],
}


def normalizar(texto):
    texto = texto.lower()

    substituicoes = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ï": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ö": "o",
        "ú": "u",
        "ü": "u",
        "ç": "c",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    return texto


def encontrar_cnpj(texto):
    padrao = r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"

    encontrado = re.search(padrao, texto)

    if not encontrado:
        return None

    return encontrado.group(0)


def encontrar_valor(texto, nome):
    padrao = rf"(?<!\w){nome}\s*:?\s*R?\$?\s*([\d.,]+)"

    encontrado = re.search(
        padrao,
        texto,
        re.IGNORECASE
    )

    if not encontrado:
        return None

    valor = encontrado.group(1)

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return None


def encontrar_data(texto):
    padrao = r"\b(\d{2}/\d{2}/\d{4})\b"

    encontrado = re.search(padrao, texto)

    if not encontrado:
        return None

    try:
        return datetime.strptime(
            encontrado.group(1),
            "%d/%m/%Y"
        ).date()
    except ValueError:
        return None


def encontrar_horario(texto):
    padrao = r"\b(\d{2}:\d{2}:\d{2})\b"

    encontrado = re.search(padrao, texto)

    if encontrado:
        return encontrado.group(1)

    return None


def encontrar_cartao(texto):
    padroes = [
        r"(?:final|ultimos?|cartao|cartão)\D{0,20}(\d{4})\b",
        r"\*{2,}(\d{4})\b",
        r"x{2,}(\d{4})\b",
    ]

    for padrao in padroes:
        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if encontrado:
            return encontrado.group(1)

    return None


def encontrar_pagamento(texto):
    texto_normalizado = normalizar(texto)

    if "credito loja" in texto_normalizado:
        return "Crédito Loja"

    if "credito" in texto_normalizado:
        return "Crédito"

    if "debito" in texto_normalizado:
        return "Débito"

    if "pix" in texto_normalizado:
        return "Pix"

    if "dinheiro" in texto_normalizado:
        return "Dinheiro"

    if "boleto" in texto_normalizado:
        return "Boleto"

    return None


def encontrar_estabelecimento(texto):
    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    for linha in linhas:
        if "CNPJ" in linha.upper():
            partes = re.split(
                r"CNPJ\s*:\s*",
                linha,
                flags=re.IGNORECASE
            )

            if len(partes) > 1:
                restante = partes[1]

                restante = re.sub(
                    r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
                    "",
                    restante
                ).strip()

                if restante:
                    return restante

    for linha in linhas:
        normalizada = normalizar(linha)

        ignorar = [
            "documento auxiliar",
            "nota fiscal",
            "cupom",
            "cnpj",
            "subtotal",
            "desconto",
            "total",
            "forma de pagamento",
            "chave de acesso",
            "consumidor",
            "caixa",
            "vendedor",
            "tributos",
            "cep",
            "avenida",
            "av.",
            "rua ",
            "logradouro",
        ]

        if any(item in normalizada for item in ignorar):
            continue

        if len(linha) >= 4:
            return linha

    return None


def encontrar_categoria(texto, estabelecimento=None):
    texto_normalizado = normalizar(texto)

    if estabelecimento:
        texto_normalizado += " " + normalizar(estabelecimento)

    # Regras específicas para supermercados/mercados.
    # Isso permite identificar estabelecimentos que não possuem
    # a palavra "mercado" no nome.
    regras_mercado = [
        "mattar",
        "mattare",
        "irmaos mattar",
        "carrefour",
        "atacadao",
        "assai",
        "epa",
        "bahamas",
        "verdemar",
        "supernosso",
        "pao de acucar",
        "paodeacucar",
        "angeloni",
        "sams club",
        "sam's club",
    ]

    for palavra in regras_mercado:
        if palavra in texto_normalizado:
            return "mercado"

    # Depois verifica todas as categorias normalmente.
    for categoria, palavras in CATEGORIAS.items():
        for palavra in palavras:
            palavra_normalizada = normalizar(palavra)

            padrao = rf"\b{re.escape(palavra_normalizada)}\b"

            if re.search(padrao, texto_normalizado):
                return categoria

    return "outros"


def interpretar_compra(texto):
    if not texto:
        return {
            "estabelecimento": None,
            "cnpj": None,
            "data": None,
            "horario": None,
            "subtotal": None,
            "desconto": None,
            "total": None,
            "pagamento": None,
            "cartao_final": None,
            "categoria": "outros",
        }

    estabelecimento = encontrar_estabelecimento(texto)

    return {
        "estabelecimento": estabelecimento,
        "cnpj": encontrar_cnpj(texto),
        "data": encontrar_data(texto),
        "horario": encontrar_horario(texto),
        "subtotal": encontrar_valor(texto, "subtotal"),
        "desconto": encontrar_valor(texto, "desconto"),
        "total": encontrar_valor(texto, "total"),
        "pagamento": encontrar_pagamento(texto),
        "cartao_final": encontrar_cartao(texto),
        "categoria": encontrar_categoria(
            texto,
            estabelecimento
        ),
    }