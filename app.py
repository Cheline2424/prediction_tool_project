import eventlet
eventlet.monkey_patch() # Penting: Lakukan monkey patch di awal

import os
import json
from datetime import datetime
# import httpx # TIDAK DIPERLUKAN LAGI KARENA TIDAK AMBIL DATA EKSTERNAL
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import random # Import modul random

# ====================================================================
# Konfigurasi Aplikasi Flask
# ====================================================================
app = Flask(__name__)

# Konfigurasi SECRET_KEY untuk Flask
# Ini SANGAT PENTING untuk keamanan sesi dan Flask-SocketIO.
# Ambil dari Environment Variable di Render atau gunakan nilai fallback yang kuat.
# Anda HARUS menambahkan SECRET_KEY di Environment Variables Render Anda.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PRODUCTION')

# Contoh password (ubah ini di lingkungan produksi atau gunakan hashing yang lebih aman)
# Untuk saat ini, kita akan gunakan password sederhana agar mudah
PASSWORD = os.environ.get('APP_PASSWORD', 'your_secure_password_here') # GANTI DENGAN PASSWORD ASLI ANDA

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ====================================================================
# Variabel Global untuk Data Game
# ====================================================================
current_game_data = {
    "WinGo_1Min": {"period": "N/A", "countdown": "00:00", "result_number": "N/A", "result_color": "N/A", "end_time": 0},
    "WinGo_30S": {"period": "N/A", "countdown": "00:00", "result_number": "N/A", "result_color": "N/A", "end_time": 0},
    "Moto_Race": {"period": "N/A", "countdown": "00:00", "result_number": "N/A", "result_color": "N/A", "end_time": 0}
}

# Define game intervals in seconds
GAME_INTERVALS = {
    "WinGo_1Min": 60,
    "WinGo_30S": 30,
    "Moto_Race": 60 # Asumsi sama dengan 1 menit jika tidak ada data dari API
}

# ====================================================================
# Fungsi Bantu
# ====================================================================
def generate_random_game_result():
    """Menghasilkan nomor dan warna random."""
    number = random.randint(0, 9)
    
    # Warna berdasarkan aturan WinGo (0, 5 = violet+red/green, lainnya single color)
    if number == 0:
        color = "violet-red"
    elif number == 5:
        color = "violet-green"
    elif number in [1, 3, 7, 9]:
        color = "green"
    else: # 2, 4, 6, 8
        color = "red"
    
    return number, color

def calculate_countdown(end_time_ms):
    """Menghitung hitungan mundur dari waktu berakhir dalam milidetik."""
    end_time_s = end_time_ms / 1000
    current_time_s = datetime.now().timestamp()
    countdown_s = max(0, int(end_time_s - current_time_s))

    minutes = countdown_s // 60
    seconds = countdown_s % 60
    return f"{minutes:02d}:{seconds:02d}"

# ====================================================================
# Fungsi Pengambilan Data Game (Background Task) - Sekarang Generate Random
# ====================================================================
def game_data_fetcher():
    """Menghasilkan data game random secara periodik dan mengirimkannya ke klien via SocketIO."""
    
    # URL dan Headers untuk API lama tidak diperlukan lagi
    # base_url_30s = "https://draw.ar-lottery01.com/WinGo/WinGo_30S.json"
    # base_url_1m = "https://draw.ar-lottery01.com/WinGo/WinGo_1M.json"
    # base_url_moto = "https://draw.ar-lottery01.com/WinGo/Moto_Race.json"

    # headers = {
    #     "Referer": "https://bharatclub.net/",
    #     "Sec-Ch-Ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"130\"",
    #     "Sec-Ch-Ua-Mobile": "?1",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "cross-site",
    #     "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
    # }

    # Inisialisasi waktu berakhir untuk putaran pertama jika aplikasi baru dimulai
    for game_type, interval in GAME_INTERVALS.items():
        if current_game_data[game_type]["end_time"] == 0:
            current_game_data[game_type]["end_time"] = (datetime.now().timestamp() + interval) * 1000
            current_game_data[game_type]["period"] = random.randint(1000000, 9999999) # Random Period Awal
            num, col = generate_random_game_result()
            current_game_data[game_type]["result_number"] = num
            current_game_data[game_type]["result_color"] = col

    while True:
        current_time_ms = datetime.now().timestamp() * 1000

        for game_type, interval in GAME_INTERVALS.items():
            # Jika countdown sudah berakhir atau belum diset, generate data baru
            if current_time_ms >= current_game_data[game_type]["end_time"]:
                current_game_data[game_type]["end_time"] = (datetime.now().timestamp() + interval) * 1000
                current_game_data[game_type]["period"] = random.randint(1000000, 9999999) # Random Period Baru
                num, col = generate_random_game_result()
                current_game_data[game_type]["result_number"] = num
                current_game_data[game_type]["result_color"] = col
                print(f"Menggenerasi data baru untuk {game_type}: Period {current_game_data[game_type]['period']}, Number {num}, Color {col}")

            current_game_data[game_type]["countdown"] = calculate_countdown(current_game_data[game_type]["end_time"])

        # Kirim data terbaru ke semua klien yang terhubung melalui SocketIO
        socketio.emit('game_update', {
            "WinGo_1Min": {
                "period": current_game_data["WinGo_1Min"]["period"],
                "countdown": current_game_data["WinGo_1Min"]["countdown"],
                "result_number": current_game_data["WinGo_1Min"]["result_number"],
                "result_color": current_game_data["WinGo_1Min"]["result_color"]
            },
            "WinGo_30S": {
                "period": current_game_data["WinGo_30S"]["period"],
                "countdown": current_game_data["WinGo_30S"]["countdown"],
                "result_number": current_game_data["WinGo_30S"]["result_number"],
                "result_color": current_game_data["WinGo_30S"]["result_color"]
            },
            "Moto_Race": {
                "period": current_game_data["Moto_Race"]["period"],
                "countdown": current_game_data["Moto_Race"]["countdown"],
                "result_number": current_game_data["Moto_Race"]["result_number"],
                "result_color": current_game_data["Moto_Race"]["result_color"]
            }
        })
        print(f"Data game terbaru dikirim: {current_game_data}")

        # Tunggu 1 detik sebelum memperbarui data
        eventlet.sleep(1)

# ====================================================================
# Route Flask
# ====================================================================
@app.route('/')
def login():
    """Menampilkan halaman login."""
    return render_template('login.html') # Kita akan buat file login.html

@app.route('/login', methods=['POST'])
def do_login():
    """Memproses login."""
    password = request.form.get('password')
    if password == PASSWORD:
        session['logged_in'] = True
        flash('Login berhasil!', 'success')
        return redirect(url_for('index'))
    else:
        flash('Password salah. Silakan coba lagi.', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Melakukan logout."""
    session.pop('logged_in', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard') # Ubah route utama menjadi /dashboard
def index():
    """Merender halaman utama aplikasi (setelah login)."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('prediction_tool.html', game_data=current_game_data)

# ====================================================================
# Event Listener SocketIO
# ====================================================================
@socketio.