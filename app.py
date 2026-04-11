from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg
import psycopg.rows
import os

app = Flask(__name__)
app.secret_key = "preload-super-system"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

# ------------------ USER ------------------

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

# ------------------ CREATE TABLES ------------------

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
                data_inicio TEXT,
                data_termino TEXT,
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
                funcional_card TEXT,
                obs TEXT
            )
            """)
            conn.commit()

# ------------------ LOGIN ------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    create_tables()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with get_conn() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                            (username, password))
                user = cur.fetchone()

                if user:
                    login_user(User(user["id"], user["username"]))
                    return redirect(url_for("dashboard"))
                else:
                    # cria usuário automaticamente se não existir
                    cur.execute("INSERT INTO users (username, password) VALUES (%s,%s)",
                                (username, password))
                    conn.commit()
                    return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ------------------ DASHBOARD ------------------

@app.route("/")
@login_required
def dashboard():
    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM preload WHERE user_id=%s ORDER BY id DESC",
                        (current_user.id,))
            filiais = cur.fetchall()

    return render_template("dashboard.html", filiais=filiais, user=current_user)

# ------------------ SAVE ------------------

@app.route("/salvar", methods=["POST"])
@login_required
def salvar():

    dados = request.form
    id_registro = dados.get("id")

    with get_conn() as conn:
        with conn.cursor() as cur:

            if id_registro:
                cur.execute("""
                UPDATE preload SET
                    loja=%s, data_inicio=%s, data_termino=%s, ip=%s,
                    servidor=%s, pdvs=%s, balcoes=%s, hibrido=%s, treinamento=%s,
                    venda_dinheiro=%s, venda_cartao=%s, pix=%s, ddg=%s,
                    recarga=%s, fidelize=%s, parcelamento=%s, logix=%s,
                    vida_link=%s, epharma=%s, funcional_card=%s, obs=%s
                WHERE id=%s
                """, (
                    dados["loja"], dados["data_inicio"], dados["data_termino"], dados["ip"],
                    dados["servidor"], dados["pdvs"], dados["balcoes"], dados["hibrido"], dados["treinamento"],
                    dados["venda_dinheiro"], dados["venda_cartao"], dados["pix"], dados["ddg"],
                    dados["recarga"], dados["fidelize"], dados["parcelamento"], dados["logix"],
                    dados["vida_link"], dados["epharma"], dados["funcional_card"], dados["obs"],
                    id_registro
                ))
            else:
                cur.execute("""
                INSERT INTO preload (
                    user_id, loja, data_inicio, data_termino, ip,
                    servidor, pdvs, balcoes, hibrido, treinamento,
                    venda_dinheiro, venda_cartao, pix, ddg,
                    recarga, fidelize, parcelamento, logix,
                    vida_link, epharma, funcional_card, obs
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    current_user.id,
                    dados["loja"], dados["data_inicio"], dados["data_termino"], dados["ip"],
                    dados["servidor"], dados["pdvs"], dados["balcoes"], dados["hibrido"], dados["treinamento"],
                    dados["venda_dinheiro"], dados["venda_cartao"], dados["pix"], dados["ddg"],
                    dados["recarga"], dados["fidelize"], dados["parcelamento"], dados["logix"],
                    dados["vida_link"], dados["epharma"], dados["funcional_card"], dados["obs"]
                ))

            conn.commit()

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
