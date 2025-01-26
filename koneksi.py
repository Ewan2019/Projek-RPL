import os
from flask import Flask, render_template, request, url_for, flash, session, redirect
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY environment variable is not set!")

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' # Ganti dengan password database Anda
app.config['MYSQL_DB'] = 'kereta'
mysql = MySQL(app)

@app.route('/', methods=['GET'])
def index():
    if 'loggedin' in session:
        if session['user_type'] == 'admin':
            return redirect(url_for('admin_view'))
        else:
            return redirect(url_for('user_view'))
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username dan password harus diisi', 'danger')
            return render_template('login.html')

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user[3], password):
                session['loggedin'] = True
                session['id'] = user[0]
                session['username'] = user[1]
                session['user_type'] = user[4]
                return redirect(url_for('index'))
            else:
                flash('Username atau password salah', 'danger')
        except Exception as e:
            flash(f'Error database: {str(e)}', 'danger')
        finally:
            cur.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))

@app.route('/regis_user', methods=['GET', 'POST'])
def regis_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('Semua field harus diisi', 'danger')
            return render_template('regis-user.html')

        if password != confirm_password:
            flash('Password tidak cocok', 'danger')
            return render_template('regis-user.html')

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            user = cur.fetchone()
            if user is None:
                cur.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
                            (username, email, generate_password_hash(password), 'user'))
                mysql.connection.commit()
                flash('Registrasi Berhasil', 'success')
            else:
                flash('Username atau email sudah ada', 'danger')
        except Exception as e:
            flash(f'Error database: {str(e)}', 'danger')
        finally:
            cur.close()
    return render_template('regis-user.html')

@app.route('/regis_admin', methods=['GET', 'POST'])
def regis_admin():
    if request.method == 'POST':
        admin_key = request.form.get('admin_key')
        if admin_key != os.environ.get('ADMIN_REGISTRATION_KEY'):
            flash('Kunci admin salah!', 'danger')
            return render_template('regis-admin.html')

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('Semua field harus diisi', 'danger')
            return render_template('regis-admin.html')

        if password != confirm_password:
            flash('Password tidak cocok', 'danger')
            return render_template('regis-admin.html')

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            user = cur.fetchone()
            if user is None:
                cur.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
                            (username, email, generate_password_hash(password), 'admin'))
                mysql.connection.commit()
                flash('Registrasi Admin Berhasil', 'success')
            else:
                flash('Username atau email sudah ada', 'danger')
        except Exception as e:
            flash(f'Error database: {str(e)}', 'danger')
        finally:
            cur.close()
    return render_template('regis-admin.html')

@app.route('/user_view', methods=['GET'])
def user_view():
    if 'loggedin' in session and session['user_type'] == 'user':
        return render_template('user-view.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/admin_view', methods=['GET'])
def admin_view():
    if 'loggedin' in session and session['user_type'] == 'admin':
        return render_template('admin-view.html', username=session['username'])
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)