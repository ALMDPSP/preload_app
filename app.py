from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "preload-secret-2026")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

# ================= LOGIN =================
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        if user == "admin" and password == "admin":
            session.clear()
            session["user"] = user
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha inválidos")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= INDEX / DASHBOARD =================
@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, vd, loja, uf, status, projeto
                FROM preload
                ORDER BY id DESC
            """)
            registros = cur.fetchall()

    return render_template("index.html", registros=registros)

# ================= SALVAR =================
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

    with get_conn() as conn:
        with conn.cursor() as cur:
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

    return redirect(url_for("index"))

# ================= EXCLUIR =================
@app.route("/excluir/<int:id>")
def excluir(id):
    if "user" not in session:
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM preload WHERE id = %s", (id,))

    return redirect(url_for("index"))

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, COUNT(*) FROM preload GROUP BY status")
            status = cur.fetchall()

    return render_template("dashboard.html", status=status)

if __name__ == "__main__":
    app.run()
