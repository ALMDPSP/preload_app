import os
import psycopg
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)

# ===============================
# App
# ===============================
app = Flask(__name__)
app.secret_key = "preload-secret-key"

# ===============================
# Login Manager
# ===============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===============================
# Usuário fixo (inicial)
# ===============================
USERS = {
    "admin": {
        "password": "admin123"
    }
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None

# ===============================
# Banco
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL)

# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = USERS.get(username)

        if user and user["password"] == password:
            login_user(User(username))
            return redirect(url_for("index"))

        flash("Usuário ou senha inválidos")

    return render_template("login.html")

# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ===============================
# INDEX / DASHBOARD
# ===============================
@app.route("/")
@app.route("/index")
@login_required
def index():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, vd, loja, uf, status, projeto
                FROM preload
                ORDER BY id DESC
            """)
            registros = cur.fetchall()

    return render_template("index.html", registros=registros)

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("index"))

# ===============================
# SALVAR
# ===============================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = {
        "vd": request.form.get("vd"),
        "bandeira": request.form.get("bandeira"),
        "loja": request.form.get("loja"),
        "uf": request.form.get("uf"),
        "municipio": request.form.get("municipio"),
        "cd_supridor": request.form.get("cd_supridor"),
        "montador": request.form.get("montador"),
        "projeto": request.form.get("projeto"),
        "entrada_ti": request.form.get("entrada_ti"),
        "envio_previsto": request.form.get("envio_previsto"),
        "term_obra": request.form.get("term_obra"),
        "cadastro": request.form.get("cadastro"),
        "sep_equip": request.form.get("sep_equip"),
        "emissao_nfe": request.form.get("emissao_nfe"),
        "link": request.form.get("link"),
        "status": request.form.get("status"),
        "cnpj": request.form.get("cnpj"),
        "precos_datahub": request.form.get("precos_datahub"),
        "preloading": request.form.get("preloading"),
        "em_loja": request.form.get("em_loja"),
        "observacoes": request.form.get("observacoes"),
    }

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO preload (
                    vd, bandeira, loja, uf, municipio, cd_supridor, montador,
                    projeto, entrada_ti, envio_previsto, term_obra, cadastro,
                    sep_equip, emissao_nfe, link, status, cnpj, precos_datahub,
                    preloading, em_loja, observacoes
                ) VALUES (
                    %(vd)s, %(bandeira)s, %(loja)s, %(uf)s, %(municipio)s,
                    %(cd_supridor)s, %(montador)s, %(projeto)s, %(entrada_ti)s,
                    %(envio_previsto)s, %(term_obra)s, %(cadastro)s,
                    %(sep_equip)s, %(emissao_nfe)s, %(link)s, %(status)s,
                    %(cnpj)s, %(precos_datahub)s, %(preloading)s,
                    %(em_loja)s, %(observacoes)s
                )
            """, dados)

    flash("Registro salvo com sucesso!")
    return redirect(url_for("index"))

# ===============================
# EXCLUIR
# ===============================
@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM preload WHERE id = %s", (id,))
    flash("Registro excluído")
    return redirect(url_for("index"))

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app.run()
