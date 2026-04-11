from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import psycopg
import os

app = Flask(__name__)
app.secret_key = "preload-secret-key"

# =========================
# LOGIN CONFIG
# =========================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# =========================
# DATABASE
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

# =========================
# CRIAR TABELA AUTOMATICAMENTE
# =========================
def criar_tabela():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS preload (
                    id SERIAL PRIMARY KEY,
                    vd TEXT,
                    loja TEXT,
                    entrada_ti TEXT,
                    term_obra TEXT,
                    link TEXT,
                    servidor_status TEXT,
                    pdv_status TEXT,
                    venda_dinheiro TEXT,
                    venda_cartao TEXT,
                    observacoes TEXT
                )
            """)
            conn.commit()

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        if user == "admin" and password == "1234":
            login_user(User(user))
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# INDEX
# =========================
@app.route("/")
@login_required
def index():
    criar_tabela()

    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM preload ORDER BY id DESC")
            registros = cur.fetchall()

    return render_template("index.html", registros=registros)

# =========================
# SALVAR (UPDATE)
# =========================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = request.form.to_dict()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE preload SET
                    servidor_status = %(servidor_status)s,
                    pdv_status = %(pdv_status)s,
                    venda_dinheiro = %(venda_dinheiro)s,
                    venda_cartao = %(venda_cartao)s,
                    observacoes = %(observacoes)s
                WHERE vd = %(vd)s
            """, dados)
            conn.commit()

    return redirect(url_for("index"))

# =========================
# RODAR
# =========================
if __name__ == "__main__":
    app.run(debug=True)
