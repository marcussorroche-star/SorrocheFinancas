from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from app.usuarios.models import Usuario
    return Usuario.query.get(int(user_id))


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "sorroche-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sorroche.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "usuarios.login"

    # =========================================================
    # DASHBOARD
    # =========================================================

    from app.dashboard.routes import dashboard
    app.register_blueprint(dashboard)

    # =========================================================
    # USUÁRIOS
    # =========================================================

    from app.usuarios.routes import usuarios
    app.register_blueprint(usuarios)

    # =========================================================
    # RECEITAS
    # =========================================================

    try:
        from app.receitas.routes import receitas
        app.register_blueprint(receitas)
    except ImportError:
        pass

    # =========================================================
    # DESPESAS
    # =========================================================

    try:
        from app.despesas.routes import despesas
        app.register_blueprint(despesas)
    except ImportError:
        pass

    # =========================================================
    # CARTÕES
    # =========================================================

    try:
        from app.cartoes.routes import cartoes
        app.register_blueprint(cartoes)
    except ImportError:
        pass

    # =========================================================
    # JUROS
    # =========================================================

    try:
        from app.juros.routes import juros
        app.register_blueprint(juros)
    except ImportError:
        pass

    # =========================================================
    # INVESTIMENTOS
    # =========================================================

    try:
        from app.investimentos.routes import investimentos
        app.register_blueprint(investimentos)
    except ImportError:
        pass

    # =========================================================
    # METAS
    # =========================================================

    try:
        from app.metas.routes import metas
        app.register_blueprint(metas)
    except ImportError:
        pass

    # =========================================================
    # PASTAS
    # =========================================================

    try:
        from app.pastas.routes import pastas
        app.register_blueprint(pastas)
    except ImportError:
        pass

    # =========================================================
    # RELATÓRIOS / FINANCEIRO
    # =========================================================

    try:
        from app.financeiro.routes import financeiro
        app.register_blueprint(financeiro)
    except ImportError:
        pass

    # =========================================================
    # IA FINANCEIRA
    # =========================================================

    try:
        from app.ia.routes import ia
        app.register_blueprint(ia)
    except ImportError:
        pass

    # =========================================================
    # LEITOR
    # =========================================================

    try:
        from app.leitor.routes import leitor
        app.register_blueprint(leitor)
    except ImportError:
        pass

    # =========================================================
    # WHATSAPP
    # =========================================================

    try:
        from app.whatsapp.routes import whatsapp
        app.register_blueprint(whatsapp)
    except ImportError:
        pass

    # =========================================================
    # RESERVAS
    # =========================================================

    try:
        from app.reservas.routes import reservas
        app.register_blueprint(reservas)
    except ImportError:
        pass

    # =========================================================
    # BANCO DE DADOS
    # =========================================================

    with app.app_context():
        db.create_all()

    return app