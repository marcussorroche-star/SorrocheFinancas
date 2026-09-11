from flask import Flask
from flask_login import LoginManager

from app.extensions import db


login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "sorroche-financas-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sorroche_unificado.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "usuarios.login"
    login_manager.login_message = "FaÃ§a login para acessar o sistema."
    login_manager.login_message_category = "warning"

    # =========================================================
    # MODELOS
    # =========================================================

    from app.usuarios.models import Usuario
    from app.receitas.models import Receita
    from app.despesas.models import Despesa
    from app.cartoes.models import Cartao, CompraCartao
    from app.juros.models import Juro
    from app.investimentos.models import Investimento
    from app.metas.models import Meta
    from app.pastas.models import Pasta
    from app.estoque.models import ItemEstoque
    from app.emprestimos.models import Emprestimo
    from app.financiamentos.models import Financiamento
    from app.consorcios.models import Consorcio

    @login_manager.user_loader
    def carregar_usuario(usuario_id):
        return Usuario.query.get(int(usuario_id))

    # =========================================================
    # BLUEPRINTS
    # =========================================================

    from app.usuarios.routes import usuarios
    app.register_blueprint(usuarios)

    from app.dashboard.routes import dashboard
    app.register_blueprint(dashboard)

    from app.receitas.routes import receitas
    app.register_blueprint(receitas, url_prefix="/receitas")

    from app.despesas.routes import despesas
    app.register_blueprint(despesas, url_prefix="/despesas")

    from app.cartoes.routes import cartoes
    app.register_blueprint(cartoes, url_prefix="/cartoes")

    from app.juros.routes import juros
    app.register_blueprint(juros, url_prefix="/juros")

    from app.investimentos.routes import investimentos
    app.register_blueprint(investimentos, url_prefix="/investimentos")

    from app.metas.routes import metas
    app.register_blueprint(metas, url_prefix="/metas")

    from app.pastas.routes import pastas
    app.register_blueprint(pastas, url_prefix="/pastas")

    from app.ia.routes import ia
    app.register_blueprint(ia, url_prefix="/ia")

    from app.leitor.routes import leitor
    app.register_blueprint(leitor, url_prefix="/leitor")

    from app.whatsapp.routes import whatsapp
    app.register_blueprint(whatsapp, url_prefix="/whatsapp")

    from app.estoque.routes import estoque
    app.register_blueprint(estoque, url_prefix="/estoque")

    from app.financeiro.routes import financeiro
    app.register_blueprint(financeiro, url_prefix="/financeiro")

    from app.emprestimos.routes import emprestimos
    from app.financiamentos.routes import financiamentos
    from app.consorcios.routes import consorcios
    app.register_blueprint(emprestimos, url_prefix="/emprestimos")
    app.register_blueprint(financiamentos, url_prefix="/financiamentos")
    app.register_blueprint(consorcios, url_prefix="/consorcios")

    # =========================================================
    # CRIAÇÃO DAS TABELAS
    # =========================================================

    with app.app_context():
        db.create_all()

    return app



