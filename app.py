import os
import json
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit # Mengembalikan Flask-SocketIO
import random
import time

# ====================================================================
# Konfigurasi Aplikasi Flask
# ====================================================================
app = Flask(__name__)

# Konfigurasi SECRET_KEY untuk Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PRODUCTION')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1) # Sesi bertahan 1 jam

# Password utama untuk akses awal aplikasi
# AMBIL DARI ENVIRONMENT VARIABLE DI RENDER ATAU GANTI DENGAN PASSWORD ASLI ANDA
MAIN_PASSWORD = os.environ.get('MAIN_APP_PASSWORD', 'bhtclub24') # Menggunakan bhtclub24 sebagai default

# Inisialisasi SocketIO dengan mode threading untuk menghindari masalah kompilasi gevent
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ====================================================================
# Variabel Global untuk Data Game
# ====================================================================
current_game_data = {
    "wingo_1_min": {"period": "N/A", "countdown": "00:00", "result_number": "N/A", "result_color": "N/A", "end_time": 0, "big_small": "N/A"},
    "wingo_30_sec": {"period": "N/A", "countdown": "00:00", "result_number": "N/A", "result_color": "N/A", "end_time": 0, "big_small": "N/A"},
    "moto_race": {"period": "N/A", "countdown": "00:00", "results": [], "end_time": 0}
}

# Define game intervals in seconds
GAME_INTERVALS = {
    "wingo_1_min": 60,
    "wingo_30_sec": 30,
    "moto_race": 60 
}

# ====================================================================
# Fungsi Bantu
# ====================================================================
def generate_random_wingo_result():
    """Menghasilkan nomor, warna, dan ukuran (besar/kecil) random untuk WinGo."""
    number = random.randint(0, 9)
    
    if number == 0:
        color = "violet-red"
    elif number == 5:
        color = "violet-green"
    elif number in [1, 3, 7, 9]:
        color = "green"
    else: # 2, 4, 6, 8
        color = "red"
    
    big_small = "Big" if number >= 5 else "Small"
    if number == 0 or number == 5:
        pass

    return {"number": number, "color": color, "big_small": big_small}

def generate_random_moto_race_results():
    """Menghasilkan hasil random untuk Moto Race."""
    results = []
    available_numbers = list(range(1, 10))
    random.shuffle(available_numbers)

    for i in range(1, 4):
        if not available_numbers: 
            break
        num = available_numbers.pop(0)
        odd_even = "Odd" if num % 2 != 0 else "Even"
        big_small = "Big" if num >= 5 else "Small"
        results.append({
            "position": f"Rank {i}",
            "number": num,
            "odd_even": odd_even,
            "big_small": big_small
        })
    return results

def calculate_countdown(end_time_ms):
    """Menghitung hitungan mundur dari waktu berakhir dalam milidetik."""
    end_time_s = end_time_ms / 1000
    current_time_s = datetime.now().timestamp()
    countdown_s = max(0, int(end_time_s - current_time_s))

    minutes = countdown_s // 60
    seconds = countdown_s % 60
    return f"{minutes:02d}:{seconds:02d}"

# ====================================================================
# Fungsi Pengambilan Data Game (Background Task) - SocketIO
# ====================================================================
def game_data_fetcher():
    """Menghasilkan data game random secara periodik dan mengirimkannya ke klien via SocketIO."""
    
    # Inisialisasi waktu berakhir untuk putaran pertama jika aplikasi baru dimulai
    for game_type, interval in GAME_INTERVALS.items():
        if current_game_data[game_type]["end_time"] == 0:
            current_game_data[game_type]["end_time"] = (datetime.now().timestamp() + interval) * 1000
            current_game_data[game_type]["period"] = random.randint(1000000, 9999999)
            
            if game_type.startswith("wingo"):
                result = generate_random_wingo_result()
                current_game_data[game_type]["result_number"] = result["number"]
                current_game_data[game_type]["result_color"] = result["color"]
                current_game_data[game_type]["big_small"] = result["big_small"]
            elif game_type == "moto_race":
                current_game_data[game_type]["results"] = generate_random_moto_race_results()
            
            print(f"Inisialisasi data untuk {game_type}: {current_game_data[game_type]}")

    while True:
        current_time_ms = datetime.now().timestamp() * 1000

        for game_type, interval in GAME_INTERVALS.items():
            # Jika countdown sudah berakhir atau belum diset, generate data baru
            if current_time_ms >= current_game_data[game_type]["end_time"]:
                current_game_data[game_type]["end_time"] = (datetime.now().timestamp() + interval) * 1000
                current_game_data[game_type]["period"] = random.randint(1000000, 9999999)
                
                if game_type.startswith("wingo"):
                    result = generate_random_wingo_result()
                    current_game_data[game_type]["result_number"] = result["number"]
                    current_game_data[game_type]["result_color"] = result["color"]
                    current_game_data[game_type]["big_small"] = result["big_small"]
                elif game_type == "moto_race":
                    current_game_data[game_type]["results"] = generate_random_moto_race_results()
                
                print(f"Menggenerasi data baru untuk {game_type}: {current_game_data[game_type]}")

            current_game_data[game_type]["countdown"] = calculate_countdown(current_game_data[game_type]["end_time"])

        # Kirim data terbaru ke semua klien yang terhubung melalui SocketIO
        socketio.emit('game_update', {
            "wingo_1_min": {
                "period": current_game_data["wingo_1_min"]["period"],
                "countdown": current_game_data["wingo_1_min"]["countdown"],
                "number": current_game_data["wingo_1_min"]["result_number"],
                "color": current_game_data["wingo_1_min"]["result_color"],
                "big_small": current_game_data["wingo_1_min"]["big_small"]
            },
            "wingo_30_sec": {
                "period": current_game_data["wingo_30_sec"]["period"],
                "countdown": current_game_data["wingo_30_sec"]["countdown"],
                "number": current_game_data["wingo_30_sec"]["result_number"],
                "color": current_game_data["wingo_30_sec"]["result_color"],
                "big_small": current_game_data["wingo_30_sec"]["big_small"]
            },
            "moto_race": {
                "period": current_game_data["moto_race"]["period"],
                "countdown": current_game_data["moto_race"]["countdown"],
                "results": current_game_data["moto_race"]["results"]
            }
        })

        time.sleep(1)

# ====================================================================
# Route Flask
# ====================================================================
@app.route('/')
def show_landing_page():
    """Menampilkan halaman landing utama."""
    if session.get('authenticated') and datetime.now().timestamp() < session.get('auth_expiry', 0):
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Memproses autentikasi password."""
    password_attempt = request.form.get('password')
    if password_attempt == MAIN_PASSWORD:
        session['authenticated'] = True
        session['auth_expiry'] = (datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']).timestamp()
        session.permanent = True
        flash('Access granted!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Incorrect password. Please try again.', 'danger')
        return redirect(url_for('show_landing_page'))

@app.route('/dashboard')
def dashboard():
    """Merender halaman utama aplikasi (setelah autentikasi)."""
    if not session.get('authenticated') or datetime.now().timestamp() >= session.get('auth_expiry', 0):
        session.pop('authenticated', None)
        session.pop('auth_expiry', None)
        flash('Your session has expired or you are not logged in. Please enter the password to access the tools.', 'danger')
        return redirect(url_for('show_landing_page'))
    
    return render_template('prediction_tool.html', game_data=current_game_data)

# Route baru untuk halaman guide
@app.route('/guide')
def guide_page():
    """Menampilkan halaman panduan (guide.html)."""
    return render_template('guide.html')

@app.route('/logout')
def logout():
    """Melakukan logout dan kembali ke halaman landing page."""
    session.pop('authenticated', None)
    session.pop('auth_expiry', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('show_landing_page'))

# ====================================================================
# Event Listener SocketIO
# ====================================================================
@socketio.on('connect')
def handle_connect():
    """Menangani koneksi klien SocketIO baru."""
    print('Client connected!')
    # Kirim data game yang terakhir diketahui segera setelah klien terhubung
    emit('game_update', {
        "wingo_1_min": {
            "period": current_game_data["wingo_1_min"]["period"],
            "countdown": current_game_data["wingo_1_min"]["countdown"],
            "number": current_game_data["wingo_1_min"]["result_number"],
            "color": current_game_data["wingo_1_min"]["result_color"],
            "big_small": current_game_data["wingo_1_min"]["big_small"]
        },
        "wingo_30_sec": {
            "period": current_game_data["wingo_30_sec"]["period"],
            "countdown": current_game_data["wingo_30_sec"]["countdown"],
            "number": current_game_data["wingo_30_sec"]["result_number"],
            "color": current_game_data["wingo_30_sec"]["result_color"],
            "big_small": current_game_data["wingo_30_sec"]["big_small"]
        },
        "moto_race": {
            "period": current_game_data["moto_race"]["period"],
            "countdown": current_game_data["moto_race"]["countdown"],
            "results": current_game_data["moto_race"]["results"]
        }
    })

    # Memulai background task untuk mengambil data jika belum berjalan.
    if not hasattr(socketio, '_background_task_started') or not socketio._background_task_started:
        socketio.start_background_task(target=game_data_fetcher)
        socketio._background_task_started = True
        print("Starting game_data_fetcher background task (random data mode).")

@socketio.on('disconnect')
def handle_disconnect():
    """Menangani pemutusan koneksi klien SocketIO."""
    print('Client disconnected!')

# ====================================================================
# Jalankan Aplikasi
# ====================================================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=True, port=port)
