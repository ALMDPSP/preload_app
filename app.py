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
                    link TEXT
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

    # Dados fixos por enquanto (layout visual)
    filial = {
        "loja": "Filial Exemplo",
        "entrada_ti": "01/04/2026",
        "term_obra": "05/04/2026",
        "link": "192.168.0.10"
    }

    return render_template("index.html", filial=filial)

if __name__ == "__main__":
    app.run(debug=True)
