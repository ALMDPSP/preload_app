import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, UserMixin, current_user
)

app = Flask(__name__)

# 🔐 SECRET KEY FIXA (obrigatório em produção)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "preload_super_secret_key_123"
)

# 🔐 CONFIG LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"


# ========= BANCO =========
def get_db_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS preload (
            id SERIAL PRIMARY KEY,
            vd TEXT,
            bandeira TEXT,
            loja TEXT,
            uf TEXT,
            municipio TEXT,
            cd_supridor TEXT,
            montador TEXT,
            projeto TEXT,
            entrada_ti TEXT,
            envio_previsto TEXT,
            term_obra TEXT,
            cadastro TEXT,
            sep_equip TEXT,
            emissao_nfe TEXT,
            link TEXT,
            preloading TEXT,
            em_loja TEXT,
            status TEXT,
            cnpj TEXT,
            precos_datahub TEXT,
            obs TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


init_db()


# ========= USUÁRIO =========
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# ========= LOGIN =========
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # LOGIN FIXO (admin / 1234)
        if username == "admin" and password == "1234":
            user = User(1)
            login_user(user, remember=True)  # 🔥 remember é o ponto-chave
            return redirect(url_for("index"))

        return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ========= ROTAS =========
@app.route("/")
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM preload ORDER BY id DESC")
    registros = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", registros=registros)


@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO preload (
            vd, bandeira, loja, uf, municipio,
            cd_supridor, montador, projeto,
            entrada_ti, envio_previsto, term_obra, cadastro,
            sep_equip, emissao_nfe, link,
            preloading, em_loja, status, cnpj,
            precos_datahub, obs
        ) VALUES (%s,%s,%s,%s,%s,
                  %s,%s,%s,
                  %s,%s,%s,%s,
                  %s,%s,%s,
                  %s,%s,%s,%s,
                  %s,%s)
    """, (
        request.form.get("vd"),
        request.form.get("bandeira"),
        request.form.get("loja"),
        request.form.get("uf"),
        request.form.get("municipio"),
        request.form.get("cd_supridor"),
        request.form.get("montador"),
        request.form.get("projeto"),
        request.form.get("entrada_ti"),
        request.form.get("envio_previsto"),
        request.form.get("term_obra"),
        request.form.get("cadastro"),
        request.form.get("sep_equip"),
        request.form.get("emissao_nfe"),
        request.form.get("link"),
        request.form.get("preloading"),
        request.form.get("em_loja"),
        request.form.get("status"),
        request.form.get("cnpj"),
        request.form.get("precos_datahub"),
        request.form.get("obs")
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))


# 🔒 BLINDAGEM
@app.route("/novo")
@login_required
def novo():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()
