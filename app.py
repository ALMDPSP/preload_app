from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = "preload_secret_key_2026"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# BANCO
# =========================
def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # PRELOADS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS preloads (
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

    # ADMIN
    cur.execute("SELECT * FROM users WHERE username = %s", ("admin",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", generate_password_hash("1234"))
        )

    conn.commit()
    conn.close()

init_db()

# =========================
# LOGIN
# =========================
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    u = cur.fetchone()
    conn.close()
    return User(u["id"], u["username"], u["password"]) if u else None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (request.form["username"],))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            login_user(User(user["id"], user["username"], user["password"]))
            return redirect(url_for("preload"))
        flash("Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# PRELOAD (CRUD)
# =========================
@app.route("/")
@login_required
def preload():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM preloads ORDER BY id DESC")
    dados = cur.fetchall()
    conn.close()
    return render_template("index.html", dados=dados)

@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    conn = get_db()
    cur = conn.cursor()

    campos = (
        "vd","bandeira","loja","uf","municipio","cd_supridor","montador","projeto",
        "entrada_ti","envio_previsto","term_obra","cadastro","sep_equip","emissao_nfe",
        "link","preloading","em_loja","status","cnpj","precos_datahub","obs"
    )

    valores = [request.form.get(c) for c in campos]

    cur.execute(f"""
        INSERT INTO preloads ({",".join(campos)})
        VALUES ({",".join(["%s"]*len(campos))})
    """, valores)

    conn.commit()
    conn.close()
    return redirect(url_for("preload"))

@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM preloads WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("preload"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        campos = (
            "vd","bandeira","loja","uf","municipio","cd_supridor","montador","projeto",
            "entrada_ti","envio_previsto","term_obra","cadastro","sep_equip","emissao_nfe",
            "link","preloading","em_loja","status","cnpj","precos_datahub","obs"
        )
        valores = [request.form.get(c) for c in campos]
        valores.append(id)

        cur.execute(f"""
            UPDATE preloads SET
            {",".join([f"{c}=%s" for c in campos])}
            WHERE id=%s
        """, valores)

        conn.commit()
        conn.close()
        return redirect(url_for("preload"))

    cur.execute("SELECT * FROM preloads WHERE id=%s", (id,))
    dado = cur.fetchone()
    conn.close()
    return render_template("editar.html", dado=dado)
