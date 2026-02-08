from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "preload_secret_key"

login_manager = LoginManager(app)
login_manager.login_view = "login"


def get_db():
    return sqlite3.connect("database.db")


with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS preload (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vd TEXT, bandeira TEXT, loja TEXT, uf TEXT, municipio TEXT,
            cd_supridor TEXT, montador TEXT, projeto TEXT, entrada_ti TEXT,
            envio_previsto TEXT, term_obra TEXT, cadastro TEXT,
            sep_equipamentos TEXT, emissao_nfe TEXT, link TEXT,
            preloading TEXT, em_loja TEXT, status TEXT, cnpj TEXT,
            precos_datahub TEXT, obs TEXT
        )
    """)


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    u = db.execute(
        "SELECT id, username, password FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    return User(*u) if u else None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT id, username, password FROM users WHERE username=?",
            (u,)
        ).fetchone()

        if user and check_password_hash(user[2], p):
            login_user(User(*user))
            return redirect("/")
        return render_template("login.html", erro="Usuário ou senha inválidos")

    return render_template("login.html")


@app.route("/")
@login_required
def index():
    db = get_db()
    dados = db.execute("SELECT * FROM preload").fetchall()
    return render_template("index.html", dados=dados)


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM preload").fetchone()[0]

    por_status = db.execute("""
        SELECT status, COUNT(*) 
        FROM preload
        GROUP BY status
    """).fetchall()

    por_uf = db.execute("""
        SELECT uf, COUNT(*) 
        FROM preload
        GROUP BY uf
    """).fetchall()

    return render_template(
        "dashboard.html",
        total=total,
        por_status=por_status,
        por_uf=por_uf
    )


@app.route("/novo", methods=["POST"])
@login_required
def novo():
    campos = [
        "vd","bandeira","loja","uf","municipio","cd_supridor","montador","projeto",
        "entrada_ti","envio_previsto","term_obra","cadastro","sep_equipamentos",
        "emissao_nfe","link","preloading","em_loja","status","cnpj",
        "precos_datahub","obs"
    ]
    valores = tuple(request.form.get(c) for c in campos)

    db = get_db()
    db.execute("""
        INSERT INTO preload (
            vd,bandeira,loja,uf,municipio,cd_supridor,montador,projeto,
            entrada_ti,envio_previsto,term_obra,cadastro,sep_equipamentos,
            emissao_nfe,link,preloading,em_loja,status,cnpj,precos_datahub,obs
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, valores)

    db.commit()
    return redirect("/")


@app.route("/editar/<int:id>")
@login_required
def editar(id):
    db = get_db()
    registro = db.execute("SELECT * FROM preload WHERE id=?", (id,)).fetchone()
    dados = db.execute("SELECT * FROM preload").fetchall()
    return render_template("index.html", dados=dados, editar=registro)


@app.route("/atualizar/<int:id>", methods=["POST"])
@login_required
def atualizar(id):
    campos = [
        "vd","bandeira","loja","uf","municipio","cd_supridor","montador","projeto",
        "entrada_ti","envio_previsto","term_obra","cadastro","sep_equipamentos",
        "emissao_nfe","link","preloading","em_loja","status","cnpj",
        "precos_datahub","obs"
    ]

    valores = [request.form.get(c) for c in campos]
    valores.append(id)

    db = get_db()
    db.execute("""
        UPDATE preload SET
            vd=?, bandeira=?, loja=?, uf=?, municipio=?, cd_supridor=?,
            montador=?, projeto=?, entrada_ti=?, envio_previsto=?,
            term_obra=?, cadastro=?, sep_equipamentos=?, emissao_nfe=?,
            link=?, preloading=?, em_loja=?, status=?, cnpj=?,
            precos_datahub=?, obs=?
        WHERE id=?
    """, valores)

    db.commit()
    return redirect("/")


@app.route("/excluir/<int:id>")
@login_required
def excluir(id):
    db = get_db()
    db.execute("DELETE FROM preload WHERE id=?", (id,))
    db.commit()
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
