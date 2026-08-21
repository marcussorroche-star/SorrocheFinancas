from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.usuarios.models import Usuario

usuarios = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


@usuarios.route("/")
def listar():
    return "<h2>👤 Módulo de Usuários funcionando!</h2>"


@usuarios.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for("dashboard.home"))

        flash("E-mail ou senha inválidos!")

    return render_template("usuarios/login.html")


@usuarios.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        usuario = Usuario(
            nome=request.form["nome"],
            email=request.form["email"],
            senha=generate_password_hash(request.form["senha"])
        )

        db.session.add(usuario)
        db.session.commit()

        flash("Usuário cadastrado com sucesso!")

        return redirect(url_for("usuarios.login"))

    return render_template("usuarios/cadastro.html")