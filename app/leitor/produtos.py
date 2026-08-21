import re
from decimal import Decimal


# ============================================================
# CATEGORIAS PRINCIPAIS
# ============================================================

CATEGORIAS = {
    "saude": [
        "farmacia",
        "farmacias",
        "drogaria",
        "drogarias",
        "hospital",
        "clinica",
        "laboratorio",
        "medico",
        "medicamento",
        "medicamentos",
        "remedio",
        "remedios",
        "paracetamol",
        "dipirona",
        "ibuprofeno",
        "amoxicilina",
        "azitromicina",
        "omeprazol",
        "losartana",
        "metformina",
        "analgesico",
        "antibiotico",
        "comprimido",
        "capsula",
        "xarope",
        "pomada",
        "vitamina",
        "vitaminas",
    ],

    "mercado": [
        "mercado",
        "supermercado",
        "hipermercado",
        "mercearia",
        "atacarejo",
        "arroz",
        "feijao",
        "macarrao",
        "massa",
        "leite",
        "queijo",
        "presunto",
        "carne",
        "frango",
        "peixe",
        "acucar",
        "cafe",
        "oleo",
        "azeite",
        "farinha",
        "biscoito",
        "bolacha",
        "pao",
        "refrigerante",
        "suco",
        "agua",
        "frutas",
        "legumes",
        "verduras",
    ],

    "pets": [
        "racao",
        "racoes",
        "petisco",
        "petiscos",
        "cachorro",
        "gato",
        "gatos",
        "cao",
        "caes",
        "petshop",
        "pet",
        "veterinaria",
        "veterinario",
        "animal",
        "animais",
        "areia sanitaria",
        "antipulgas",
    ],

    "casa": [
        "casa",
        "construcao",
        "ferragem",
        "cimento",
        "tinta",
        "ferramenta",
        "ferramentas",
        "moveis",
        "utilidades",
        "limpeza",
        "detergente",
        "sabao",
        "amaciante",
        "desinfetante",
        "agua sanitaria",
        "esponja",
        "lampada",
        "vassoura",
        "rodo",
    ],

    "higiene": [
        "sabonete",
        "shampoo",
        "condicionador",
        "desodorante",
        "creme dental",
        "pasta dental",
        "escova dental",
        "papel higienico",
        "absorvente",
    ],

    "transporte": [
        "posto",
        "combustivel",
        "gasolina",
        "etanol",
        "diesel",
        "estacionamento",
        "uber",
        "taxi",
        "pedagio",
    ],

    "alimentacao": [
        "restaurante",
        "lanchonete",
        "padaria",
        "pizzaria",
        "hamburguer",
        "ifood",
        "cafe",
        "sorvete",
        "salgado",
        "lanche",
    ],

    "roupas": [
        "roupa",
        "roupas",
        "vestuario",
        "calcado",
        "calcados",
        "sapato",
        "sapatos",
        "tenis",
        "moda",
        "boutique",
        "camisa",
        "camiseta",
        "calca",
        "bermuda",
        "vestido",
        "blusa",
        "sandalia",
        "meia",
    ],

    "educacao": [
        "escola",
        "faculdade",
        "universidade",
        "curso",
        "livraria",
        "papelaria",
        "caderno",
        "caneta",
        "lapis",
        "borracha",
        "mochila",
        "livro",
        "apostila",
    ],

    "eletronicos": [
        "fone",
        "fone de ouvido",
        "carregador",
        "cabo usb",
        "mouse",
        "teclado",
        "pilha",
        "bateria",
        "eletronico",
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
        "telefone",
    ],
}


# ============================================================
# SUBCATEGORIAS
# ============================================================

SUBCATEGORIAS = {
    "saude": {
        "farmacia": [
            "farmacia",
            "farmacias",
            "drogaria",
            "drogarias",
        ],

        "remedios": [
            "paracetamol",
            "dipirona",
            "ibuprofeno",
            "amoxicilina",
            "azitromicina",
            "omeprazol",
            "losartana",
            "metformina",
            "medicamento",
            "medicamentos",
            "remedio",
            "remedios",
            "analgesico",
            "antibiotico",
            "comprimido",
            "capsula",
            "xarope",
            "pomada",
        ],

        "vitaminas": [
            "vitamina",
            "vitaminas",
            "suplemento",
            "suplementos",
        ],
    },

    "mercado": {
        "alimentos": [
            "arroz",
            "feijao",
            "macarrao",
            "massa",
            "farinha",
            "acucar",
            "leite",
            "queijo",
            "manteiga",
            "carne",
            "frango",
            "peixe",
            "ovo",
            "ovos",
            "pao",
            "frutas",
            "legumes",
            "verduras",
            "biscoito",
            "bolacha",
        ],

        "bebidas": [
            "agua",
            "suco",
            "refrigerante",
            "cafe",
        ],

        "limpeza": [
            "detergente",
            "sabao",
            "amaciante",
            "desinfetante",
            "limpeza",
        ],
    },

    "pets": {
        "racao": [
            "racao",
            "racoes",
        ],

        "animais": [
            "cachorro",
            "gato",
            "gatos",
            "cao",
            "caes",
            "animal",
            "animais",
        ],

        "petshop": [
            "petshop",
            "pet",
            "petisco",
            "petiscos",
        ],

        "saude_animal": [
            "veterinaria",
            "veterinario",
            "antipulgas",
        ],
    },

    "casa": {
        "limpeza": [
            "detergente",
            "sabao",
            "amaciante",
            "desinfetante",
            "agua sanitaria",
            "esponja",
            "vassoura",
            "rodo",
        ],

        "construcao": [
            "construcao",
            "cimento",
            "tinta",
            "ferragem",
            "ferramenta",
            "ferramentas",
        ],

        "moveis": [
            "moveis",
            "utilidades",
        ],
    },

    "higiene": {
        "higiene_pessoal": [
            "sabonete",
            "shampoo",
            "condicionador",
            "desodorante",
            "creme dental",
            "pasta dental",
            "escova dental",
        ],

        "higiene_feminina": [
            "absorvente",
        ],
    },

    "roupas": {
        "vestuario": [
            "roupa",
            "roupas",
            "camisa",
            "camiseta",
            "calca",
            "bermuda",
            "vestido",
            "blusa",
        ],

        "calcados": [
            "sapato",
            "sapatos",
            "tenis",
            "sandalia",
        ],
    },

    "educacao": {
        "material_escolar": [
            "caderno",
            "caneta",
            "lapis",
            "borracha",
            "mochila",
        ],

        "livros": [
            "livro",
            "livraria",
            "apostila",
        ],
    },

    "eletronicos": {
        "acessorios": [
            "fone",
            "fone de ouvido",
            "carregador",
            "cabo usb",
            "mouse",
            "teclado",
        ],

        "energia": [
            "pilha",
            "bateria",
        ],
    },
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):
    if not texto:
        return ""

    texto = str(texto).lower()

    substituicoes = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "ê": "e",
        "è": "e",
        "ë": "e",
        "í": "i",
        "ì": "i",
        "ï": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ö": "o",
        "ú": "u",
        "ù": "u",
        "ü": "u",
        "ç": "c",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    return texto


# ============================================================
# CATEGORIA
# ============================================================

def identificar_categoria_produto(nome):
    texto = normalizar_texto(nome)

    if not texto:
        return "outros"

    ordem = [
        "saude",
        "pets",
        "mercado",
        "casa",
        "higiene",
        "transporte",
        "alimentacao",
        "roupas",
        "educacao",
        "eletronicos",
        "lazer",
        "telefonia_internet",
    ]

    for categoria in ordem:
        palavras = CATEGORIAS.get(categoria, [])

        for palavra in palavras:
            palavra = normalizar_texto(palavra)

            if re.search(
                rf"\b{re.escape(palavra)}\b",
                texto
            ):
                return categoria

    return "outros"


# ============================================================
# SUBCATEGORIA
# ============================================================

def identificar_subcategoria_produto(nome, categoria=None):
    texto = normalizar_texto(nome)

    if not texto:
        return None

    if categoria is None:
        categoria = identificar_categoria_produto(nome)

    subcategorias = SUBCATEGORIAS.get(categoria, {})

    for subcategoria, palavras in subcategorias.items():

        for palavra in palavras:
            palavra = normalizar_texto(palavra)

            if re.search(
                rf"\b{re.escape(palavra)}\b",
                texto
            ):
                return subcategoria

    return None


# ============================================================
# VALOR
# ============================================================

def converter_valor(valor):
    if valor is None:
        return None

    valor = str(valor).strip()
    valor = valor.replace("R$", "")
    valor = valor.replace(" ", "")

    try:
        if "," in valor:
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

        return float(Decimal(valor))

    except Exception:
        return None


def encontrar_preco(texto):
    padroes = [
        r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"R\$\s*(\d+,\d{2})",
        r"(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"(\d+\.\d{2})",
    ]

    for padrao in padroes:
        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if encontrado:
            return converter_valor(
                encontrado.group(1)
            )

    return None


# ============================================================
# LIMPEZA DO NOME
# ============================================================

def limpar_nome_produto(nome):
    nome = nome.strip()

    nome = re.sub(
        r"\s+",
        " ",
        nome
    )

    nome = re.sub(
        r"^[\-\*\|]+",
        "",
        nome
    )

    return nome.strip()


# ============================================================
# IDENTIFICAR LINHA DE PRODUTO
# ============================================================

def linha_parece_produto(linha):
    texto = normalizar_texto(linha)

    if not texto:
        return False

    ignorar = [
        "cnpj",
        "cpf",
        "subtotal",
        "desconto",
        "total",
        "forma de pagamento",
        "chave de acesso",
        "consumidor",
        "documento auxiliar",
        "nota fiscal",
        "cupom",
        "credito",
        "debito",
        "pix",
        "dinheiro",
        "caixa",
        "vendedor",
        "tributos",
        "cep",
        "serie",
        "nfce",
        "data",
        "hora",
        "endereco",
        "avenida",
        "rua",
        "bairro",
        "cidade",
        "loja:",
    ]

    for palavra in ignorar:
        if palavra in texto:
            return False

    if re.search(
        r"\b\d{2}/\d{2}/\d{4}\b",
        texto
    ):
        return False

    if re.search(
        r"\b\d{2}:\d{2}:\d{2}\b",
        texto
    ):
        return False

    if re.search(
        r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
        texto
    ):
        return False

    return True


# ============================================================
# EXTRAIR PRODUTOS
# ============================================================

def extrair_produtos(texto):
    produtos = []

    if not texto:
        return produtos

    linhas = [
        linha.strip()
        for linha in str(texto).splitlines()
        if linha.strip()
    ]

    for linha in linhas:

        if not linha_parece_produto(linha):
            continue

        encontrados = re.findall(
            r"R?\$?\s*(\d{1,6}(?:\.\d{3})*,\d{2})\b",
            linha
        )

        if not encontrados:
            encontrados = re.findall(
                r"R?\$?\s*(\d+\.\d{2})\b",
                linha
            )

        if not encontrados:
            continue

        valor = converter_valor(
            encontrados[-1]
        )

        if valor is None:
            continue

        nome = re.sub(
            r"R?\$?\s*\d{1,6}(?:\.\d{3})*,\d{2}\b",
            "",
            linha
        )

        nome = re.sub(
            r"R?\$?\s*\d+\.\d{2}\b",
            "",
            nome
        )

        nome = limpar_nome_produto(nome)

        if len(nome) < 2:
            continue

        categoria = identificar_categoria_produto(
            nome
        )

        subcategoria = identificar_subcategoria_produto(
            nome,
            categoria
        )

        produtos.append(
            {
                "produto": nome,
                "quantidade": 1,
                "preco": valor,
                "categoria": categoria,
                "subcategoria": subcategoria,
            }
        )

    return produtos


# ============================================================
# COMPARAÇÃO DE PREÇOS
# ============================================================

def comparar_produto(produto_atual, historico):
    if not produto_atual:
        return None

    nome_atual = normalizar_texto(
        produto_atual.get("produto", "")
    )

    if not nome_atual:
        return None

    preco_atual = produto_atual.get("preco")

    if preco_atual is None:
        return None

    encontrados = []

    for item in historico or []:

        nome_historico = normalizar_texto(
            item.get("produto", "")
        )

        if not nome_historico:
            continue

        mesmo_produto = (
            nome_atual == nome_historico
            or nome_atual in nome_historico
            or nome_historico in nome_atual
        )

        if not mesmo_produto:
            continue

        preco_historico = item.get("preco")

        if preco_historico is None:
            continue

        encontrados.append(
            {
                "produto": item.get("produto"),
                "preco": preco_historico,
                "estabelecimento": item.get(
                    "estabelecimento"
                ),
                "cnpj": item.get("cnpj"),
                "data": item.get("data"),
            }
        )

    if not encontrados:
        return None

    menor = min(
        encontrados,
        key=lambda item: item["preco"]
    )

    if menor["preco"] >= preco_atual:
        return {
            "encontrado": True,
            "mais_barato": False,
            "economia": 0,
            "melhor_preco": menor["preco"],
            "estabelecimento": menor["estabelecimento"],
            "cnpj": menor["cnpj"],
            "data": menor["data"],
        }

    economia = round(
        preco_atual - menor["preco"],
        2
    )

    return {
        "encontrado": True,
        "mais_barato": True,
        "economia": economia,
        "melhor_preco": menor["preco"],
        "estabelecimento": menor["estabelecimento"],
        "cnpj": menor["cnpj"],
        "data": menor["data"],
    }