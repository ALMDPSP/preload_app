from flask import Flask, render_template, request, redirect, url_for, session
import psycopg
import os

app = Flask(__name__)
app.secret_key = "preload_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        # LOGIN SIMPLES (AJUSTE DEPOIS SE QUISER)
        if user == "admin" and password == "admin":
            session["user"] = user
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def login_required():
    return "user" in session


# ================= INDEX =================
@app.route("/")
@app.route("/index")
def index():
    if not login_required():
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, vd, loja, uf, status, projeto FROM preload ORDER BY id DESC")
            registros = cur.fetchall()

    return render_template("index.html", registros=registros)


# ================= SALVAR =================
@app.route("/salvar", methods=["POST"])
def salvar():
    if not login_required():
        return redirect(url_for("login"))

    dados = request.form

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
    if not login_required():
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM preload WHERE id = %s", (id,))

    return redirect(url_for("index"))


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, COUNT(*) FROM preload GROUP BY status")
            status = cur.fetchall()

    return render_template("dashboard.html", status=status)


# ================= START =================
if __name__ == "__main__":
    app.run(debug=True)
