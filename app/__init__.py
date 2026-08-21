from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)

    login_manager.init_app(app)

    from .dashboard.routes import dashboard

    app.register_blueprint(dashboard)

    with app.app_context():
        db.create_all()

    return app