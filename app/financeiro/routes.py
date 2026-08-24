from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date
from sqlalchemy import func

from app import db
from app.receitas.models import Receita
from app.despesas.models import Despesa
from app.financeiro.regra_mensal import calcular_regra_mensal


financeiro = Blueprint(
    "financeiro",
    __name__,
    url_prefix="/financeiro"
)


@financeiro.route("/")
def index():

    receitas = Receita.query.order_by(
        Receita.data.desc()
    ).all()

    despesas = Despesa.query.order_by(
        Despesa.data.desc()
    ).all()

    total_receitas = sum(
        float(r.valor or 0)
        for r in receitas
    )

    total_despesas = sum(
        float(d.valor or 0)
        for d in despesas
        if d.status == "Pago"
    )

    saldo = total_receitas - total_despesas

    # ==========================================
    # REGRA FINANCEIRA MENSAL
    # ==========================================

    regra = calcular_regra_mensal()

    disponivel_regra = regra.get(
        "disponivel",
        0
    )

    limite_gastos = regra.get(
        "limite_gastos"
    )

    para_gastos = regra.get(
        "para_gastos",
        0
    )

    reserva_emergencia = regra.get(
        "reserva_emergencia",
        regra.get("fundo_reserva", 0)
    )

    reserva_gastos = regra.get(
        "reserva_gastos",
        0
    )

    valor_meta = regra.get(
        "meta",
        0
    )

    # ==========================================
    # QUANTO AINDA PODE GASTAR
    # ==========================================

    if limite_gastos is None:

        falta_gastar = 0.0

    else:

        falta_gastar = max(
            0.0,
            float(limite_gastos)
            - float(para_gastos)
        )

    # ==========================================
    # DADOS DO GRÁFICO DE GASTOS
    # ==========================================

    dados_grafico = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor)
    ).group_by(
        Despesa.categoria
    ).all()

    categorias = []
    valores = []

    for categoria, total in dados_grafico:

        categorias.append(
            categoria or "Sem categoria"
        )

        valores.append(
            float(total or 0)
        )

    # ==========================================
    # DESPESAS DO PRÓXIMO MÊS
    # ==========================================

    hoje = date.today()

    if hoje.month == 12:

        proximo_mes = 1
        proximo_ano = hoje.year + 1

    else:

        proximo_mes = hoje.month + 1
        proximo_ano = hoje.year

    despesas_proximo_mes = sum(
        float(d.valor or 0)
        for d in despesas
        if d.vencimento
        and d.vencimento.month == proximo_mes
        and d.vencimento.year == proximo_ano
    )

    return render_template(
        "financeiro.html",

        receitas=receitas,

        despesas=despesas,

        total_receitas=total_receitas,

        total_despesas=total_despesas,

        saldo=saldo,

        despesas_proximo_mes=despesas_proximo_mes,

        categorias=categorias,

        valores=valores,

        # ======================================
        # REGRA FINANCEIRA
        # ======================================

        regra=regra,

        disponivel_regra=disponivel_regra,

        limite_gastos=limite_gastos,

        para_gastos=para_gastos,

        falta_gastar=falta_gastar,

        reserva_emergencia=reserva_emergencia,

        reserva_gastos=reserva_gastos,

        valor_meta=valor_meta
    )


@financeiro.route("/receita/nova", methods=["POST"])
def nova_receita():

    receita = Receita(
        descricao=request.form.get("descricao"),
        valor=float(request.form.get("valor")),
        data=date.today(),
        usuario_id=1
    )

    db.session.add(receita)
    db.session.commit()

    return redirect(
        url_for("financeiro.index")
    )


@financeiro.route("/despesa/nova", methods=["POST"])
def nova_despesa():

    vencimento = request.form.get("vencimento")

    if vencimento:
        vencimento = date.fromisoformat(
            vencimento
        )

    despesa = Despesa(
        descricao=request.form.get("descricao"),
        categoria=request.form.get("categoria"),
        valor=float(request.form.get("valor")),
        data=date.today(),
        vencimento=vencimento,
        forma_pagamento=request.form.get(
            "forma_pagamento"
        ),
        status=request.form.get("status") or "Pendente",
        usuario_id=1
    )

    db.session.add(despesa)
    db.session.commit()

    return redirect(
        url_for("financeiro.index")
    )


@financeiro.route(
    "/receita/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_receita(id):

    receita = Receita.query.get_or_404(id)

    if request.method == "POST":

        receita.descricao = request.form.get(
            "descricao"
        )

        receita.valor = float(
            request.form.get("valor")
        )

        db.session.commit()

        return redirect(
            url_for("financeiro.index")
        )

    return render_template(
        "financeiro/editar_receita.html",
        receita=receita
    )


@financeiro.route(
    "/despesa/editar/<int:id>",
    methods=["GET", "POST"]
)
def editar_despesa(id):

    despesa = Despesa.query.get_or_404(id)

    if request.method == "POST":

        vencimento = request.form.get(
            "vencimento"
        )

        if vencimento:
            vencimento = date.fromisoformat(
                vencimento
            )

        despesa.descricao = request.form.get(
            "descricao"
        )

        despesa.categoria = request.form.get(
            "categoria"
        )

        despesa.valor = float(
            request.form.get("valor")
        )

        despesa.vencimento = vencimento

        despesa.forma_pagamento = request.form.get(
            "forma_pagamento"
        )

        despesa.status = request.form.get(
            "status"
        )

        db.session.commit()

        return redirect(
            url_for("financeiro.index")
        )

    return render_template(
        "financeiro/editar_despesa.html",
        despesa=despesa
    )


@financeiro.route("/receita/excluir/<int:id>")
def excluir_receita(id):

    receita = Receita.query.get_or_404(id)

    db.session.delete(receita)
    db.session.commit()

    return redirect(
        url_for("financeiro.index")
    )


@financeiro.route("/despesa/excluir/<int:id>")
def excluir_despesa(id):

    despesa = Despesa.query.get_or_404(id)

    db.session.delete(despesa)
    db.session.commit()

    return redirect(
        url_for("financeiro.index")
    )


@financeiro.route("/relatorio/mensal")
def relatorio_mensal():

    hoje = date.today()

    mes = request.args.get("mes")

    if mes:

        try:

            ano, numero_mes = map(
                int,
                mes.split("-")
            )

        except (ValueError, AttributeError):

            ano = hoje.year
            numero_mes = hoje.month
            mes = f"{ano:04d}-{numero_mes:02d}"

    else:

        ano = hoje.year
        numero_mes = hoje.month
        mes = f"{ano:04d}-{numero_mes:02d}"

    receitas = Receita.query.filter(
        db.extract("year", Receita.data) == ano,
        db.extract("month", Receita.data) == numero_mes
    ).all()

    despesas = Despesa.query.filter(
        db.extract("year", Despesa.data) == ano,
        db.extract("month", Despesa.data) == numero_mes
    ).all()

    total_receitas = sum(
        float(r.valor or 0)
        for r in receitas
    )

    total_despesas = sum(
        float(d.valor or 0)
        for d in despesas
    )

    saldo = (
        total_receitas
        - total_despesas
    )

    dados = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor)
    ).filter(
        db.extract("year", Despesa.data) == ano,
        db.extract("month", Despesa.data) == numero_mes
    ).group_by(
        Despesa.categoria
    ).all()

    categorias = []
    valores = []

    for categoria, total in dados:

        categorias.append(
            categoria or "Sem categoria"
        )

        valores.append(
            float(total or 0)
        )

    return render_template(
        "relatorios/mensal.html",

        total_receitas=total_receitas,

        total_despesas=total_despesas,

        saldo=saldo,

        mes=mes,

        categorias=categorias,

        valores=valores
    )


@financeiro.route("/relatorio/anual")
def relatorio_anual():

    ano_texto = request.args.get(
        "ano"
    )

    try:

        ano = int(ano_texto)

    except (ValueError, TypeError):

        ano = date.today().year

    receitas = Receita.query.filter(
        db.extract("year", Receita.data) == ano
    ).all()

    despesas = Despesa.query.filter(
        db.extract("year", Despesa.data) == ano
    ).all()

    total_receitas = sum(
        float(r.valor or 0)
        for r in receitas
    )

    total_despesas = sum(
        float(d.valor or 0)
        for d in despesas
    )

    saldo = (
        total_receitas
        - total_despesas
    )

    dados = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor)
    ).filter(
        db.extract("year", Despesa.data) == ano
    ).group_by(
        Despesa.categoria
    ).all()

    categorias = []
    valores = []

    for categoria, total in dados:

        categorias.append(
            categoria or "Sem categoria"
        )

        valores.append(
            float(total or 0)
        )

    return render_template(
        "relatorios/anual.html",

        ano=ano,

        total_receitas=total_receitas,

        total_despesas=total_despesas,

        saldo=saldo,

        categorias=categorias,

        valores=valores
    )


@financeiro.route("/relatorio/categorias")
def relatorio_categorias():

    dados = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor)
    ).group_by(
        Despesa.categoria
    ).all()

    return render_template(
        "relatorios/categoria.html",
        categorias=dados
    )


@financeiro.route("/relatorio/grafico")
def relatorio_grafico():

    dados = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor)
    ).group_by(
        Despesa.categoria
    ).all()

    nomes = []
    valores = []

    for categoria, total in dados:

        nomes.append(
            categoria or "Sem categoria"
        )

        valores.append(
            float(total or 0)
        )

    return render_template(
        "relatorios/grafico.html",
        nomes=nomes,
        valores=valores
    )