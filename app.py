import os
import psycopg
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = "preload-secret"

# ==========================
# BANCO DE DADOS
# ==========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL)

# ==========================
# LOGIN
# ==========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

# ==========================
# LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password FROM users WHERE username=%s",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and user[2] == password:
            login_user(User(*user))
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha inválidos")

    return render_template("login.html")

# ==========================
# LOGOUT
# ==========================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ==========================
# INDEX / GRID
# ==========================
@app.route("/")
@app.route("/index")
@login_required
def index():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id, vd, bandeira, loja, uf, municipio, cd_supridor, montador,
            projeto, entrada_ti, envio_previsto, term_obra, cadastro,
            sep_equip, emissao_nfe, link, status, cnpj, precos_datahub,
            preloading, em_loja, observacoes
        FROM preload
        ORDER BY id DESC
    """)
    registros = cur.fetchall()
    conn.close()

    return render_template("index.html", registros=registros)

# ==========================
# SALVAR
# ==========================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = request.form.to_dict()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO preload (
            vd, bandeira, loja, uf, municipio, cd_supridor, montador,
            projeto, entrada_ti, envio_previsto, term_obra, cadastro,
            sep_equip, emissao_nfe, link, status, cnpj, precos_datahub,
            preloading, em_loja, observacoes
        ) VALUES (
            %(vd)s, %(bandeira)s, %(loja)s, %(uf)s, %(municipio)s,
            %(cd_supridor)s, %(montador)s, %(projeto)s,
            %(entrada_ti)s, %(envio_previsto)s, %(term_obra)s,
            %(cadastro)s, %(sep_equip)s, %(emissao_nfe)s,
            %(link)s, %(status)s, %(cnpj)s, %(precos_datahub)s,
            %(preloading)s, %(em_loja)s, %(observacoes)s
        )
    """, dados)

    conn.commit()
    conn.close()

    return redirect(url_for("index"))

# ==========================
# EXCLUIR
# ==========================
@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM preload WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# ==========================
# DASHBOARD
# ==========================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ==========================
if __name__ == "__main__":
    app.run(debug=True)
