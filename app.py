import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "preload_secret")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

USUARIO = "admin"
SENHA = "1234"

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if request.form["username"] == USUARIO and request.form["password"] == SENHA:
            session["user"] = USUARIO
            return redirect(url_for("index"))
        erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= INDEX =================
@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM preload ORDER BY id DESC")
    registros = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", registros=registros, edit=None)

# ================= EDITAR =================
@app.route("/editar/<int:id>")
def editar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM preload WHERE id=%s", (id,))
    edit = cur.fetchone()

    cur.execute("SELECT * FROM preload ORDER BY id DESC")
    registros = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", registros=registros, edit=edit)

# ================= SALVAR =================
@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect(url_for("login"))

    dados = dict(request.form)
    id = dados.get("id")

    conn = get_conn()
    cur = conn.cursor()

    if id:
        cur.execute("""
            UPDATE preload SET
                vd=%(vd)s, bandeira=%(bandeira)s, loja=%(loja)s, uf=%(uf)s,
                municipio=%(municipio)s, cd_supridor=%(cd_supridor)s, montador=%(montador)s,
                projeto=%(projeto)s, entrada_ti=%(entrada_ti)s, envio_previsto=%(envio_previsto)s,
                term_obra=%(term_obra)s, cadastro=%(cadastro)s, sep_equip=%(sep_equip)s,
                emissao_nfe=%(emissao_nfe)s, link=%(link)s, status=%(status)s,
                cnpj=%(cnpj)s, precos_datahub=%(precos_datahub)s,
                preloading=%(preloading)s, em_loja=%(em_loja)s,
                observacoes=%(observacoes)s
            WHERE id=%(id)s
        """, dados)
    else:
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

# ================= EXCLUIR =================
@app.route("/excluir/<int:id>")
def excluir(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM preload WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))
