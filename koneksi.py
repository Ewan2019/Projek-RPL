from flask import Flask, render_template, request, url_for, flash, session, redirect
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'kuatkuat'  # Ganti dengan kunci rahasia yang SANGAT kuat dan acak!

# Konfigurasi database untuk users
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'kereta'
mysql_user = MySQL(app)

# Konfigurasi database untuk admin
app.config['MYSQL_ADMIN_DB'] = 'admin'  # Tentukan database admin
mysql_admin = MySQL(app)  # Buat koneksi MySQL baru untuk admin

@app.route('/')
def indeks():
    return render_template('home.html')


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/choice_regis')
def choice_regis():
    return render_template('choice-regis.html')


# Registrasi pengguna
@app.route('/regis_user', methods=('GET', 'POST'))
def regis_user():
    if request.method == 'POST':  # Memeriksa apakah metode request adalah POST
        username = request.form['username']  # Mengambil username dari form
        email = request.form['email']  # Mengambil email dari form
        password = request.form['password']  # Mengambil password dari form

        # Cek username atau email
        cursor = mysql_user.connection.cursor()  # Membuat objek cursor untuk menjalankan query
        cursor.execute('SELECT * FROM users WHERE username=%s OR email=%s', (username, email))  # Menjalankan query untuk mencari username atau email
        akun = cursor.fetchone()  # Mengambil data akun yang ditemukan
        if akun is None:  # Jika akun tidak ditemukan
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (username, email, generate_password_hash(password)))  # Menjalankan query untuk memasukkan data akun baru
            mysql_user.connection.commit()  # Melakukan commit perubahan ke database
            flash('Registrasi Berhasil', 'success')  # Menampilkan pesan flash 'Registrasi Berhasil' dengan kategori 'success'
        else:  # Jika akun ditemukan
            flash('Username atau email sudah ada', 'danger')  # Menampilkan pesan flash 'Username atau email sudah ada' dengan kategori 'danger'
    return render_template('regis-user.html')  # Merender template 'registrasi.html'


# Registrasi admin
@app.route('/regis_admin', methods=['GET', 'POST'])
def regis_admin():
    if request.method == 'POST':
        # Periksa apakah semua field yang diperlukan ada
        if 'username' not in request.form or 'email' not in request.form or 'password' not in request.form or 'admin_key' not in request.form:
            flash('Semua field harus diisi', 'danger')
            return render_template('regis-admin.html')
            
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        admin_key = request.form['admin_key']
        
        # Validasi input tidak boleh kosong
        if not username or not email or not password or not admin_key:
            flash('Semua field harus diisi', 'danger')
            return render_template('regis-admin.html')

        cursor = mysql_admin.connection.cursor()
        try:
            # Cek username atau email
            cursor.execute('SELECT * FROM admin WHERE username=%s OR email=%s', (username, email))
            akun = cursor.fetchone()
            
            if akun is None:
                cursor.execute('INSERT INTO admin VALUES (NULL, %s, %s, %s, %s)', 
                             (username, email, generate_password_hash(password), admin_key))
                mysql_admin.connection.commit()
                flash('Registrasi Berhasil', 'success')
                return redirect(url_for('login'))  # Redirect ke halaman login setelah berhasil
            else:
                flash('Username atau email sudah ada', 'danger')
                
        except Exception as e:
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        finally:
            cursor.close()
            
    return render_template('regis-admin.html')


# Login pengguna atau admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor_user = mysql_user.connection.cursor()
        cursor_admin = mysql_admin.connection.cursor()

        try:
            # Cek di tabel users
            cursor_user.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cursor_user.fetchone()

            # Cek di tabel admin
            cursor_admin.execute("SELECT * FROM admin WHERE username = %s", [username])
            admin = cursor_admin.fetchone()

            # Periksa login user
            if user and check_password_hash(user[3], password):  # asumsikan password ada di kolom ke-4
                session['loggedin'] = True
                session['id'] = user[0]  # id_user
                session['username'] = user[1]  # username
                return redirect(url_for('user_view'))  # Arahkan ke halaman pengguna

            # Periksa login admin
            elif admin and check_password_hash(admin[3], password):  # asumsikan password ada di kolom ke-4
                session['loggedin'] = True
                session['id'] = admin[0]  # id_admin
                session['username'] = admin[1]  # username
                return redirect(url_for('admin_view'))  # Arahkan ke halaman admin

            flash('Username atau password salah', 'danger')

        except Exception as e:
            flash(f'Error database: {str(e)}', 'danger')
        finally:
            cursor_user.close()
            cursor_admin.close()

    return render_template('login.html')


@app.route('/user_view')
def user_view():
    if 'loggedin' in session:
        return render_template('user-view.html')
    else:
        flash('Silakan login terlebih dahulu', 'danger')
        return redirect(url_for('login'))  # Jika pengguna tidak login, arahkan ke halaman login

@app.route('/admin_view')
def admin_view():
    if 'loggedin' in session:
        return render_template('admin-view.html')
    else:
        flash('Silakan login terlebih dahulu', 'danger')
        return redirect(url_for('login'))  # Jika admin tidak login, arahkan ke halaman login


if __name__ == '__main__':
    app.run(debug=True)
