from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
import psycopg.rows
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-123456")

DATABASE_URL = os.environ.get("DATABASE_URL")

# =========================
# LOGIN CONFIG
# =========================
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

# =========================
# DATABASE
# =========================
def get_conn():
    return psycopg.connect(DATABASE_URL, sslmode="require")

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
                CREATE TABLE IF NOT EXISTS filiais (
                    id SERIAL PRIMARY KEY,
                    loja TEXT,
                    data_inicio TEXT,
                    data_termino TEXT,
                    ip TEXT,
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
                    funcional_card TEXT
                )
            """)

            conn.commit()

# =========================
# LOGIN
# =========================
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

                if not user:
                    hashed = generate_password_hash(password)
                    cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)", (username,hashed))
                    conn.commit()
                    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                    user = cur.fetchone()

                if check_password_hash(user["password"], password):
                    login_user(User(user["id"], user["username"]))
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("login.html", erro="Senha incorreta")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# DASHBOARD
# =========================
@app.route("/")
@login_required
def dashboard():
    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM filiais ORDER BY id DESC")
            filiais = cur.fetchall()

    return render_template("dashboard.html", filiais=filiais)

# =========================
# SALVAR
# =========================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = request.form.to_dict()

    with get_conn() as conn:
        with conn.cursor() as cur:

            if dados.get("id"):  # EDITAR
                cur.execute("""
                    UPDATE filiais SET
                        loja=%s,
                        data_inicio=%s,
                        data_termino=%s,
                        ip=%s,
                        venda_dinheiro=%s,
                        venda_cartao=%s,
                        pix=%s,
                        ddg=%s,
                        recarga=%s,
                        fidelize=%s,
                        parcelamento=%s,
                        logix=%s,
                        vida_link=%s,
                        epharma=%s,
                        funcional_card=%s
                    WHERE id=%s
                """, (
                    dados["loja"], dados["data_inicio"], dados["data_termino"], dados["ip"],
                    dados["venda_dinheiro"], dados["venda_cartao"], dados["pix"], dados["ddg"],
                    dados["recarga"], dados["fidelize"], dados["parcelamento"], dados["logix"],
                    dados["vida_link"], dados["epharma"], dados["funcional_card"],
                    dados["id"]
                ))
            else:  # NOVO
                cur.execute("""
                    INSERT INTO filiais (
                        loja,data_inicio,data_termino,ip,
                        venda_dinheiro,venda_cartao,pix,ddg,recarga,
                        fidelize,parcelamento,logix,vida_link,
                        epharma,funcional_card
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    dados["loja"], dados["data_inicio"], dados["data_termino"], dados["ip"],
                    dados["venda_dinheiro"], dados["venda_cartao"], dados["pix"], dados["ddg"],
                    dados["recarga"], dados["fidelize"], dados["parcelamento"], dados["logix"],
                    dados["vida_link"], dados["epharma"], dados["funcional_card"]
                ))

            conn.commit()

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
