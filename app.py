from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "preload_secret_key"

# =========================
# CONEXÃO COM BANCO (Render)
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        if user == "admin" and password == "admin":
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

# =========================
# INDEX (FORM + GRID)
# =========================
@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, vd, loja, uf, status, projeto FROM preload ORDER BY id DESC")
    registros = cur.fetchall()
    conn.close()

    return render_template("index.html", registros=registros)

# =========================
# SALVAR
# =========================
@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect(url_for("login"))

    dados = request.form

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
    cur.execute("DELETE FROM preload WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT status, COUNT(*) FROM preload GROUP BY status")
    status = cur.fetchall()

    cur.execute("SELECT uf, COUNT(*) FROM preload GROUP BY uf")
    ufs = cur.fetchall()

    conn.close()

    return render_template("dashboard.html", status=status, ufs=ufs)

if __name__ == "__main__":
    app.run(debug=True)
