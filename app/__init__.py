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

    from app.dashboard.routes import dashboard
    app.register_blueprint(dashboard)

    from app.usuarios.routes import usuarios
    app.register_blueprint(usuarios)

    with app.app_context():
        db.create_all()

    return app
