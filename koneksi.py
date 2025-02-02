import os
from flask import Flask, render_template, request, url_for, flash, session, redirect, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import datetime
from flask_cors import CORS
import logging

# Configure logging to write to a file
log_file = os.path.join(os.getcwd(), 'app.log')
logging.basicConfig(filename=log_file, level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# Memuat variabel lingkungan dari file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY environment variable is not set!")

# Mengatur konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Ganti dengan password database Anda
app.config['MYSQL_DB'] = 'kereta'

# Inisialisasi MySQL dan CORS
mysql = MySQL(app)
CORS(app)

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
        try:
            # Menjalankan query untuk mengambil data kereta dari database
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM jadwal")  # Pastikan nama tabel dan kolom sesuai
            trains = cur.fetchall()
            
            # Jika data ada, kirim ke template
            if trains:
                return render_template('user-view.html', trains=trains)
            else:
                flash("Tidak ada data kereta ditemukan", "warning")
                return render_template('user-view.html', trains=[])
        except Exception as e:
            flash(f"Error database: {str(e)}", "danger")
            return render_template('user-view.html', trains=[])
        finally:
            cur.close()
    else:
        return redirect(url_for('login'))


@app.route('/admin_view', methods=['GET'])
def admin_view():
    if 'loggedin' in session and session['user_type'] == 'admin':
        try:
            # Ambil data kereta dari database
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM jadwal")  # Mengambil semua jadwal kereta
            trains = cur.fetchall()

            # Kirim data ke template jika data kereta ada
            if trains:
                return render_template('admin-view.html', trains=trains)
            else:
                flash('Tidak ada data kereta ditemukan', 'warning')
                return render_template('admin-view.html', trains=[])
        except Exception as e:
            flash(f"Error database: {str(e)}", 'danger')
            return render_template('admin-view.html', trains=[])
        finally:
            cur.close()
    else:
        # Jika tidak ada sesi atau tipe user bukan admin, arahkan ke login
        return redirect(url_for('login'))

@app.route('/admin_dashbord', methods=['GET'])
def admin_dashbord():
    return render_template('admin-dashbord.html')

@app.route('/api/trains', methods=['GET'])
def get_trains():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM jadwal")  # Mengambil data jadwal kereta dari tabel 'jadwal'
        trains = cur.fetchall()

        # Jika tidak ada data kereta dalam database
        if not trains:
            return jsonify({'error': 'Tidak ada kereta dalam database'}), 404

        # Menyiapkan data kereta dalam format JSON untuk dikirim ke frontend
        train_data = []
        for train in trains:
            train_data.append({
                'id': train[0],  # Pastikan untuk mengirimkan ID kereta untuk keperluan penghapusan
                'nama_kereta': train[1],
                'tanggal': train[2].strftime('%Y-%m-%d'),  # Mengubah format tanggal menjadi 'YYYY-MM-DD'
                'waktu': train[3].strftime('%H:%M:%S'),  # Mengubah format waktu menjadi 'HH:MM:SS'
                'hari': train[4],
                'prediksi_waktu': train[5].strftime('%H:%M:%S'),  # Format waktu prediksi
                'status': train[6],
                'kecepatan': train[7],
                'jarak': train[8]
            })
        
        # Mengirimkan data kereta dalam format JSON ke frontend
        return jsonify({'trains': train_data}), 200
    except Exception as e:
        # Menangani error dan mengirimkan pesan error
        return jsonify({'error': f'Error: {str(e)}'}), 500
    finally:
        cur.close()


@app.route('/api/trains', methods=['POST'])
def add_train():
    data = request.get_json()
    nama_kereta = data.get('nama_kereta')
    tanggal_str = data.get('tanggal')
    waktu_str = data.get('waktu')
    hari = data.get('hari')
    prediksi_waktu_str = data.get('prediksi_waktu')
    status = data.get('status')
    kecepatan = data.get('kecepatan')
    jarak = data.get('jarak')

    # Input validation: Check for missing fields
    required_fields = ['nama_kereta', 'tanggal', 'waktu', 'hari', 'prediksi_waktu', 'status', 'kecepatan', 'jarak']
    missing_fields = [field for field in required_fields if data.get(field) is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    try:
        tanggal = datetime.datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        waktu_str = waktu_str + ":00" if len(waktu_str) == 5 else waktu_str
        waktu = datetime.datetime.strptime(waktu_str, '%H:%M:%S').time()
        prediksi_waktu_str = prediksi_waktu_str + ":00" if len(prediksi_waktu_str) == 5 else prediksi_waktu_str
        prediksi_waktu = datetime.datetime.strptime(prediksi_waktu_str, '%H:%M:%S').time()

    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {e}'}), 400

    cur = mysql.connection.cursor()
    try:
        # Check for existing train schedule
        cur.execute("SELECT 1 FROM jadwal WHERE nama_kereta = %s AND tanggal = %s AND waktu = %s", (nama_kereta, tanggal, waktu))
        existing_entry = cur.fetchone()

        if existing_entry:
            return jsonify({'error': 'Train schedule already exists'}), 409  # Conflict status code

        # Insert new train schedule
        cur.execute("INSERT INTO jadwal (nama_kereta, tanggal, waktu, hari, prediksi_waktu, status, kecepatan, jarak) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (nama_kereta, tanggal, waktu, hari, prediksi_waktu, status, kecepatan, jarak))
        mysql.connection.commit()
        train_id = cur.lastrowid
        return jsonify({'message': 'Train added successfully', 'id': train_id}), 201

    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500
    finally:
        cur.close()

@app.route('/delete_train/<int:train_id>', methods=['POST'])
def delete_train(train_id):
    print(f"Attempting to delete train with ID: {train_id}")
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM jadwal WHERE id = %s", (train_id,))
        affected_rows = cur.rowcount
        mysql.connection.commit()

        if affected_rows > 0:
            flash('Jadwal berhasil dihapus', 'success')
        else:
            flash('Jadwal dengan ID tersebut tidak ditemukan.', 'warning')
        return redirect(url_for('admin_view'))
    except Exception as e:
        logging.exception(f"Error deleting train with ID {train_id}: {e}")
        flash(f"Terjadi kesalahan saat menghapus jadwal. Silakan coba lagi. Check the application log for details.", "danger")
        return redirect(url_for('admin_view'))
    finally:
        cur.close()



@app.route('/api/trains/<int:train_id>', methods=['PUT'])
def update_train(train_id):
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    if not key or not value:
        return jsonify({'error': 'Key dan value harus diisi'}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(f"UPDATE jadwal SET {key} = %s WHERE id = %s", (value, train_id))
        mysql.connection.commit()
        return jsonify({'message': 'Kereta berhasil diperbarui'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

if __name__ == '__main__':
    app.run(debug=True)
