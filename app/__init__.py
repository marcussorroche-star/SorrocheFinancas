from flask import Flask
from app.extensions import db


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "sorroche-financas-secret-key"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sorroche.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # =========================================================
    # BLUEPRINTS
    # =========================================================

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

    # =========================================================
    # CRIAÇÃO DAS TABELAS
    # =========================================================

    with app.app_context():
        db.create_all()

    return app