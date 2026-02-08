from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "preload_secret_key_2026"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

DB_PATH = "database.db"

# =========================
# BANCO DE DADOS
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Usuários
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Preloads
    cur.execute("""
    CREATE TABLE IF NOT EXISTS preloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loja TEXT,
        uf TEXT,
        municipio TEXT,
        status TEXT
    )
    """)

    # Usuário admin padrão
    cur.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("1234"))
        )
        print("✔ Usuário admin criado (senha: 1234)")

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
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()

    if user:
        return User(user["id"], user["username"], user["password"])
    return None

# =========================
# ROTAS
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"], user["password"]))
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        loja = request.form.get("loja")
        uf = request.form.get("uf")
        municipio = request.form.get("municipio")
        status = request.form.get("status")

        cur.execute(
            "INSERT INTO preloads (loja, uf, municipio, status) VALUES (?, ?, ?, ?)",
            (loja, uf, municipio, status)
        )
        conn.commit()

    cur.execute("SELECT * FROM preloads")
    preloads = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", preloads=preloads)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# START
# =========================
if __name__ == "__main__":
    app.run()
