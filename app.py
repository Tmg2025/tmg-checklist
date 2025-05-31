from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ───── CRIAR BANCO DE DADOS ─────
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ortomosaicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cultura TEXT,
            quadra TEXT,
            regiao TEXT,
            imagem TEXT,
            observacoes TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ───── ROTA INICIAL ─────
@app.route('/')
def index():
    return redirect(url_for('login'))

# ───── LOGIN ─────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos')
    return render_template('login.html')

# ───── DASHBOARD ─────
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ortomosaicos")
    ortos = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', ortos=ortos)

# ───── VISUALIZAR QUADRA ─────
@app.route('/quadra/<int:id>')
def ver_quadra(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ortomosaicos WHERE id=?", (id,))
    quadra = cursor.fetchone()
    conn.close()
    if not quadra:
        return "Quadra não encontrada", 404
    return render_template('quadra.html', quadra=quadra)

# ───── LOGOUT ─────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ───── CRIAR USUÁRIO PADRÃO ─────
@app.route('/criar_usuario')
def criar_usuario():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'supervisor')")
        conn.commit()
        flash('Usuário admin criado.')
    except:
        flash('Usuário já existe.')
    conn.close()
    return redirect(url_for('login'))

# ───── MAIN ─────
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
