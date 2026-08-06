from flask import Flask

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "SorrocheFinancas2026"

    @app.route("/")
    def home():
        return """
        <h1>Sorroche Finanças Inteligentes</h1>
        <h2>🚀 Projeto iniciado com sucesso!</h2>
        """

    return app