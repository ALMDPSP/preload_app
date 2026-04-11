from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import psycopg
import psycopg.rows
import os

app = Flask(__name__)
app.secret_key = "preload-secret-key"

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

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

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            login_user(User("admin"))
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# DASHBOARD
@app.route("/")
@login_required
def dashboard():
    criar_tabela()
    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM preload ORDER BY id DESC")
            filiais = cur.fetchall()
    return render_template("dashboard.html", filiais=filiais)

# SALVAR / EDITAR
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    dados = request.form
    id_registro = dados.get("id")

    with get_conn() as conn:
        with conn.cursor() as cur:

            if id_registro:  # EDITAR
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

            else:  # NOVO
                cur.execute("""
                INSERT INTO preload (
                    loja, data_inicio, data_termino, ip,
                    servidor, pdvs, balcoes, hibrido, treinamento,
                    venda_dinheiro, venda_cartao, pix, ddg,
                    recarga, fidelize, parcelamento, logix,
                    vida_link, epharma, funcional_card, obs
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
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
