from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import psycopg
import psycopg.rows
import os

app = Flask(__name__)
app.secret_key = "preload-secret-key"

# ================= LOGIN =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ================= DATABASE =================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

def criar_tabela():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS preload (
                    id SERIAL PRIMARY KEY,
                    loja TEXT,
                    entrada_ti TEXT,
                    term_obra TEXT,
                    link TEXT,
                    servidor TEXT,
                    pdvs TEXT,
                    balcoes TEXT,
                    hibrido TEXT,
                    treinamento TEXT,
                    venda_dinheiro TEXT,
                    venda_cartao TEXT,
                    pix TEXT,
                    observacoes TEXT
                )
            """)
            conn.commit()

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            login_user(User("admin"))
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ================= INDEX =================
@app.route("/")
@login_required
def index():
    criar_tabela()

    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM preload ORDER BY id DESC LIMIT 1")
            registro = cur.fetchone()

    return render_template("index.html", registro=registro)

# ================= SALVAR =================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = request.form

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO preload (
                    loja, entrada_ti, term_obra, link,
                    servidor, pdvs, balcoes, hibrido, treinamento,
                    venda_dinheiro, venda_cartao, pix, observacoes
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                dados.get("loja"),
                dados.get("entrada_ti"),
                dados.get("term_obra"),
                dados.get("link"),
                dados.get("servidor"),
                dados.get("pdvs"),
                dados.get("balcoes"),
                dados.get("hibrido"),
                dados.get("treinamento"),
                dados.get("venda_dinheiro"),
                dados.get("venda_cartao"),
                dados.get("pix"),
                dados.get("observacoes"),
            ))
            conn.commit()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
