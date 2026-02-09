from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "preload-secret")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        if user == "admin" and password == "1234":
            session["user"] = user
            return redirect("/index")

        return render_template("login.html", error="Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= DASHBOARD =================

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return redirect("/index")

@app.route("/index")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, vd, loja, uf, status, projeto FROM preload ORDER BY id DESC")
    registros = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", registros=registros)

# ================= SALVAR =================

@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect("/login")

    dados = dict(request.form)

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

    return redirect("/index")

# ================= EDITAR =================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        dados = dict(request.form)
        dados["id"] = id

        cur.execute("""
            UPDATE preload SET
                vd=%(vd)s, loja=%(loja)s, uf=%(uf)s,
                status=%(status)s, projeto=%(projeto)s,
                observacoes=%(observacoes)s
            WHERE id=%(id)s
        """, dados)

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/index")

    cur.execute("SELECT * FROM preload WHERE id=%s", (id,))
    registro = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("editar.html", r=registro)

# ================= EXCLUIR =================

@app.route("/excluir/<int:id>")
def excluir(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM preload WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/index")

if __name__ == "__main__":
    app.run()
