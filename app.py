from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import psycopg
import os

app = Flask(__name__)
app.secret_key = "preload-secret-key"

# =========================
# LOGIN
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
def criar_tabela_se_nao_existir():
    with get_conn() as conn:
        with conn.cursor() as cur:
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
                    status TEXT,
                    cnpj TEXT,
                    precos_datahub TEXT,
                    preloading TEXT,
                    em_loja TEXT,
                    observacoes TEXT,

                    servidor_status TEXT,
                    pdv_status TEXT,
                    balcao_status TEXT,
                    hibrido_status TEXT,
                    treinamento_status TEXT,

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
# LOGIN ROUTES
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
    criar_tabela_se_nao_existir()  # 🔥 cria tabela automaticamente

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM preload ORDER BY id DESC")
            registros = cur.fetchall()

    return render_template("index.html", registros=registros)

# =========================
# SALVAR
# =========================
@app.route("/salvar", methods=["POST"])
@login_required
def salvar():
    criar_tabela_se_nao_existir()

    dados = request.form.to_dict()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO preload (
                    vd, bandeira, loja, uf, municipio, cd_supridor, montador,
                    projeto, entrada_ti, envio_previsto, term_obra, cadastro,
                    sep_equip, emissao_nfe, link, status, cnpj, precos_datahub,
                    preloading, em_loja, observacoes,

                    servidor_status,
                    pdv_status,
                    balcao_status,
                    hibrido_status,
                    treinamento_status,

                    venda_dinheiro,
                    venda_cartao,
                    pix,
                    ddg,
                    recarga,
                    fidelize,
                    parcelamento,
                    logix,
                    vida_link,
                    epharma,
                    funcional_card
                ) VALUES (
                    %(vd)s, %(bandeira)s, %(loja)s, %(uf)s, %(municipio)s, %(cd_supridor)s, %(montador)s,
                    %(projeto)s, %(entrada_ti)s, %(envio_previsto)s, %(term_obra)s, %(cadastro)s,
                    %(sep_equip)s, %(emissao_nfe)s, %(link)s, %(status)s, %(cnpj)s, %(precos_datahub)s,
                    %(preloading)s, %(em_loja)s, %(observacoes)s,

                    %(servidor_status)s,
                    %(pdv_status)s,
                    %(balcao_status)s,
                    %(hibrido_status)s,
                    %(treinamento_status)s,

                    %(venda_dinheiro)s,
                    %(venda_cartao)s,
                    %(pix)s,
                    %(ddg)s,
                    %(recarga)s,
                    %(fidelize)s,
                    %(parcelamento)s,
                    %(logix)s,
                    %(vida_link)s,
                    %(epharma)s,
                    %(funcional_card)s
                )
            """, dados)
            conn.commit()

    return redirect(url_for("index"))

# =========================
# EXCLUIR
# =========================
@app.route("/excluir/<vd>")
@login_required
def excluir(vd):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM preload WHERE vd = %s", (vd,))
            conn.commit()
    return redirect(url_for("index"))

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
