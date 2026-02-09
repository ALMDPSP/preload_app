import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "preload_secret")

# ===============================
# CONEXÃO COM POSTGRES (RENDER)
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ===============================
# LOGIN FIXO (SIMPLIFICADO)
# ===============================
USUARIO = "admin"
SENHA = "1234"

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if request.form["username"] == USUARIO and request.form["password"] == SENHA:
            session["user"] = USUARIO
            return redirect(url_for("index"))
        else:
            erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ===============================
# TELA PRINCIPAL (NOVO + LISTA)
# ===============================
@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, vd, loja, uf, status FROM preload ORDER BY id DESC")
    registros = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", registros=registros)

# ===============================
# SALVAR PRELOAD
# ===============================
@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect(url_for("login"))

    dados = {k: request.form.get(k) for k in request.form}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO preload (
            vd, bandeira, loja, uf, municipio, cd_supridor, montador,
            projeto, entrada_ti, envio_previsto, term_obra, cadastro,
            sep_equip, emissao_nfe, link, status, cnpj, precos_datahub,
            preloading, em_loja, observacoes
        ) VALUES (
            %(vd)s, %(bandeira)s, %(loja)s, %(uf)s, %(municipio)s, %(cd_supridor)s, %(montador)s,
            %(projeto)s, %(entrada_ti)s, %(envio_previsto)s, %(term_obra)s, %(cadastro)s,
            %(sep_equip)s, %(emissao_nfe)s, %(link)s, %(status)s, %(cnpj)s, %(precos_datahub)s,
            %(preloading)s, %(em_loja)s, %(observacoes)s
        )
    """, dados)
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))

# ===============================
# EXCLUIR
# ===============================
@app.route("/excluir/<int:id>")
def excluir(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM preload WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))

# ===============================
# DASHBOARD (SIMPLIFICADO)
# ===============================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")
