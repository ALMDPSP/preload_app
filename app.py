from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
import psycopg.rows
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

DATABASE_URL = os.environ.get("DATABASE_URL")

# =========================
# LOGIN CONFIG
# =========================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

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
                    # cria usuário automaticamente na primeira vez
                    hashed = generate_password_hash(password)
                    cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)",
                                (username, hashed))
                    conn.commit()
                    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                    user = cur.fetchone()

                if check_password_hash(user["password"], password):
                    login_user(User(user["id"], user["username"]), remember=True)
                    return redirect(url_for("dashboard"))
                else:
                    flash("Senha incorreta")

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
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run()
