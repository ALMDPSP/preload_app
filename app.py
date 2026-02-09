from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "preload_secret_key"

# =========================
# CONEXÃO COM POSTGRES
# =========================
def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

# =========================
# LOGIN SIMPLES
# =========================
@app.route("/", methods=["GET"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "123":
            session["user"] = "admin"
            return redirect(url_for("index"))
        return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# INDEX / DASHBOARD
# =========================
@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, vd, loja, uf, status, projeto
        FROM preload
        ORDER BY id DESC
    """)
    registros = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", registros=registros)

# =========================
# SALVAR (INSERT / UPDATE)
# =========================
@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect(url_for("login"))

    campos = [
        "vd","bandeira","loja","uf","municipio","cd_supridor","montador",
        "projeto","entrada_ti","envio_previsto","term_obra","cadastro",
        "sep_equip","emissao_nfe","link","status","cnpj","precos_datahub",
        "preloading","em_loja","observacoes"
    ]

    dados = {c: request.form.get(c, "") for c in campos}
    id = request.form.get("id")

    conn = get_conn()
    cur = conn.cursor()

    try:
        if id:
            dados["id"] = id
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
    except Exception as e:
        print("ERRO AO SALVAR:", e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))

# =========================
# EXCLUIR
# =========================
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

# =========================
# EDITAR
# =========================
@app.route("/editar/<int:id>")
def editar(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM preload WHERE id=%s", (id,))
    registro = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("index.html", editar=registro, registros=[])
