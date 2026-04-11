from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

# ================= LOGIN =================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()
            if user:
                return User(user["id"], user["username"])
    return None

# ================= DATABASE =================

def create_tables():
    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS preload (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                loja TEXT,
                entrada TEXT,
                termino TEXT,
                ip TEXT,

                servidor TEXT,
                pdvs TEXT,
                balcoes TEXT,
                hibrido TEXT,
                treinamento TEXT,

                venda_dinheiro TEXT,
                venda_cartao TEXT,
                pix TEXT,
                ddg TEXT,
                recarga TEXT,
                fidelize TEXT,
                parcelamento TEXT,
                logix TEXT,
                vida_link TEXT,
                epharma TEXT,
                funcional TEXT
            )
            """)
            conn.commit()

# ================= LOGIN ROUTES =================

@app.route("/login", methods=["GET","POST"])
def login():
    create_tables()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with get_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:

                cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                user = cur.fetchone()

                if user:
                    if check_password_hash(user["password"], password):
                        login_user(User(user["id"], user["username"]))
                        return redirect(url_for("dashboard"))
                    else:
                        return "Senha incorreta"
                else:
                    senha_hash = generate_password_hash(password)
                    cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)",
                                (username, senha_hash))
                    conn.commit()
                    return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ================= DASHBOARD =================

@app.route("/")
@login_required
def dashboard():

    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM preload WHERE user_id=%s ORDER BY id DESC",
                        (current_user.id,))
            filiais = cur.fetchall()

    total = len(filiais)
    concluidas = sum(1 for f in filiais if f["servidor"] == "🟢")
    percentual = int((concluidas / total)*100) if total > 0 else 0

    return render_template("dashboard.html",
                           filiais=filiais,
                           total=total,
                           concluidas=concluidas,
                           percentual=percentual,
                           user=current_user)

# ================= SALVAR =================

@app.route("/salvar", methods=["POST"])
@login_required
def salvar():

    dados = request.form.to_dict()
    id_reg = dados.get("id")

    with get_conn() as conn:
        with conn.cursor() as cur:

            if id_reg:
                cur.execute("""
                UPDATE preload SET
                    loja=%(loja)s,
                    entrada=%(entrada)s,
                    termino=%(termino)s,
                    ip=%(ip)s,
                    servidor=%(servidor)s,
                    pdvs=%(pdvs)s,
                    balcoes=%(balcoes)s,
                    hibrido=%(hibrido)s,
                    treinamento=%(treinamento)s
                WHERE id=%(id)s
                """, dados)
            else:
                cur.execute("""
                INSERT INTO preload (
                    user_id, loja, entrada, termino, ip,
                    servidor, pdvs, balcoes, hibrido, treinamento
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    current_user.id,
                    dados.get("loja"),
                    dados.get("entrada"),
                    dados.get("termino"),
                    dados.get("ip"),
                    dados.get("servidor"),
                    dados.get("pdvs"),
                    dados.get("balcoes"),
                    dados.get("hibrido"),
                    dados.get("treinamento")
                ))

            conn.commit()

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
