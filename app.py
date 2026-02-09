import os
import psycopg
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user
)

# ===============================
# APP
# ===============================
app = Flask(__name__)
app.secret_key = "preload-secret"

# ===============================
# LOGIN
# ===============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

USERS = {
    "admin": "admin123"
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
# BANCO
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
        u = request.form["username"]
        p = request.form["password"]

        if u in USERS and USERS[u] == p:
            login_user(User(u))
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
@app.route("/dashboard")
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

# ===============================
# SALVAR
# ===============================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = dict(request.form)

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
        conn.commit()

    flash("Registro salvo com sucesso")
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
        conn.commit()

    flash("Registro excluído")
    return redirect(url_for("index"))

# ===============================
# START
# ===============================
if __name__ == "__main__":
    app.run()
