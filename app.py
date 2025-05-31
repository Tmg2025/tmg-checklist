from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_super_segura'

UPLOAD_FOLDER = 'static/uploads'
FOTOS_FOLDER = 'static/fotos_apoiadoras'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FOTOS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FOTOS_FOLDER'] = FOTOS_FOLDER

# ───── CONEXÃO COM BANCO ─────
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ortomosaicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        quadra_nome TEXT,
        descricao TEXT,
        projeto TEXT,
        cliente TEXT,
        data_registro TEXT,
        cultura TEXT,
        regiao TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS anotacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orto_id INTEGER,
        x FLOAT,
        y FLOAT,
        texto TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fotos_apoiadoras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orto_id INTEGER,
        filename TEXT,
        legenda TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ───── ROTA: LOGIN ─────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (user, pwd))
        result = cursor.fetchone()
        conn.close()
        if result:
            session['user'] = user
            session['role'] = result[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Login inválido.')
    return render_template('login.html')

# ───── ROTA: DASHBOARD ─────
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    filtro_projeto = request.args.get('projeto')
    filtro_cultura = request.args.get('cultura')
    filtro_regiao = request.args.get('regiao')
    filtro_quadra = request.args.get('quadra')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = 'SELECT * FROM ortomosaicos WHERE 1=1'
    params = []

    if filtro_projeto:
        query += ' AND projeto=?'
        params.append(filtro_projeto)
    if filtro_cultura:
        query += ' AND cultura=?'
        params.append(filtro_cultura)
    if filtro_regiao:
        query += ' AND regiao=?'
        params.append(filtro_regiao)
    if filtro_quadra:
        query += ' AND quadra_nome LIKE ?'
        params.append(f'%{filtro_quadra}%')

    cursor.execute(query, params)
    dados = cursor.fetchall()

    cursor.execute('SELECT DISTINCT projeto FROM ortomosaicos')
    projetos = [row[0] for row in cursor.fetchall()]
    cursor.execute('SELECT DISTINCT cultura FROM ortomosaicos')
    culturas = [row[0] for row in cursor.fetchall()]
    cursor.execute('SELECT DISTINCT regiao FROM ortomosaicos')
    regioes = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template('dashboard.html', dados=dados, projetos=projetos, culturas=culturas, regioes=regioes)

# ───── ROTA: UPLOAD DE ORTOMOSAICO ─────
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['arquivo']
        quadra_nome = request.form['quadra']
        descricao = request.form['descricao']
        projeto = request.form['projeto']
        cliente = request.form['cliente']
        cultura = request.form['cultura']
        regiao = request.form['regiao']
        data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO ortomosaicos 
                (filename, quadra_nome, descricao, projeto, cliente, data_registro, cultura, regiao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (filename, quadra_nome, descricao, projeto, cliente, data_registro, cultura, regiao))
            conn.commit()
            conn.close()

            flash('Ortomosaico enviado com sucesso!')
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

# ───── ROTA: VISUALIZAR QUADRA ─────
@app.route('/quadra/<int:quadra_id>')
def quadra(quadra_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ortomosaicos WHERE id=?', (quadra_id,))
    item = cursor.fetchone()
    conn.close()
    return render_template('quadra.html', item=item)

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

if __name__ == '__main__':
    app.run(debug=True)
