import os
import json
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import random
import time
import requests
from dateutil import parser
from flask_cors import CORS

# ====================================================================
# Konfigurasi Aplikasi Flask
# ====================================================================
app = Flask(__name__)
CORS(app)  # Tambahkan ini untuk mengizinkan koneksi dari browser
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PRODUCTION')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
MAIN_PASSWORD = os.environ.get('MAIN_APP_PASSWORD', 'bhtclub24')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ====================================================================
# Variabel Global dan URL API Asli
# ====================================================================
current_game_data = {
    "wingo_1_min": {"period": "N/A", "countdown": "00:00", "number": "N/A", "color": "N/A", "big_small": "N/A"},
    "wingo_30_sec": {"period": "N/A", "countdown": "00:00", "number": "N/A", "color": "N/A", "big_small": "N/A"},
    "moto_race": {"period": "N/A", "countdown": "00:00", "number": "N/A", "color": "N/A", "big_small": "N/A"},
    "chicken_road": {"period": "N/A", "countdown": "00:00", "number": "N/A", "color": "N/A", "big_small": "N/A"}
}

# URL API yang mengambil data JSON bersih, bukan halaman web
API_URLS = {
    "wingo_30_sec": "https://wingoanalyst.com/api/data_ingo.php?type=30",
    "wingo_1_min": "https://wingoanalyst.com/api/data_ingo.php?type=60",
    "moto_race": "https://wingoanalyst.com/api/data_moto.php?type=60", # Ini adalah tebakan URL API yang lebih baik
    "chicken_road": "https://wingoanalyst.com/api/data_chicken.php?type=45" # Tebakan URL API
}

# ====================================================================
# Fungsi Bantu untuk Prediksi
# ====================================================================
def predict_wingo(latest_data):
    """
    Membuat prediksi berdasarkan data historis terakhir.
    """
    if not latest_data or 'content' not in latest_data:
        return {"number": "N/A", "color": "N/A", "big_small": "N/A"}

    last_number = int(latest_data['content']['number'])
    last_color = latest_data['content']['colour']

    # Logika prediksi
    predicted_number = (last_number % 2 == 0) and 'Ganjil' or 'Genap'
    predicted_big_small = 'Big' if last_number >= 5 else 'Small'
    
    # Logika prediksi warna
    if last_color == 'green':
        predicted_color = 'red'
    elif last_color == 'red':
        predicted_color = 'violet'
    else:
        predicted_color = 'green'

    return {
        "number": str(predicted_number),
        "color": predicted_color,
        "big_small": predicted_big_small
    }

# ====================================================================
# Fungsi Utama untuk Mengambil Data
# ====================================================================
def fetch_real_data_and_predict():
    """Mengambil data dari API asli dan menjalankan prediksi."""
    game_predictions = {}
    
    # Ambil data dan prediksi untuk WinGo 30s
    try:
        response_30s = requests.get(API_URLS["wingo_30_sec"], timeout=5)
        response_30s.raise_for_status()
        data_30s = response_30s.json()[0]
        prediction_30s = predict_wingo(data_30s)
        
        next_period_30s = str(int(data_30s.get('issueNumber')) + 1)
        
        game_predictions["wingo_30_sec"] = {
            "period": next_period_30s,
            "countdown": "...", # Placeholder, hitungan mundur akan dibuat di frontend
            **prediction_30s
        }
    except Exception as e:
        print(f"Error fetching/predicting WinGo 30s: {e}")
        game_predictions["wingo_30_sec"] = current_game_data["wingo_30_sec"]

    # Ambil data dan prediksi untuk WinGo 1 min
    try:
        response_1min = requests.get(API_URLS["wingo_1_min"], timeout=5)
        response_1min.raise_for_status()
        data_1min = response_1min.json()[0]
        prediction_1min = predict_wingo(data_1min)
        
        next_period_1min = str(int(data_1min.get('issueNumber')) + 1)
        
        game_predictions["wingo_1_min"] = {
            "period": next_period_1min,
            "countdown": "...",
            **prediction_1min
        }
    except Exception as e:
        print(f"Error fetching/predicting WinGo 1 min: {e}")
        game_predictions["wingo_1_min"] = current_game_data["wingo_1_min"]

    # Data dummy untuk game lain karena API-nya belum dikonfirmasi
    game_predictions["moto_race"] = {
        "period": "N/A", "countdown": "N/A", "number": "N/A", "color": "N/A", "big_small": "N/A"
    }
    game_predictions["chicken_road"] = {
        "period": "N/A", "countdown": "N/A", "number": "N/A", "color": "N/A", "big_small": "N/A"
    }

    return game_predictions

# ====================================================================
# Fungsi Pengambilan Data Game (Background Task) - SocketIO
# ====================================================================
def game_data_fetcher():
    """Ambil data game real-time dari API dan kirim ke klien via SocketIO."""
    while True:
        try:
            updated_data = fetch_real_data_and_predict()
            
            for game_type, data in updated_data.items():
                current_game_data[game_type].update(data)
                
            socketio.emit('game_update', current_game_data)
            print("Mengirim data prediksi terbaru:", current_game_data)
            
        except Exception as e:
            print(f"Error in main fetcher loop: {e}")

        time.sleep(30) # Cek setiap 30 detik

# ====================================================================
# Route Flask
# ====================================================================
@app.route('/')
def show_landing_page():
    if session.get('authenticated') and datetime.now().timestamp() < session.get('auth_expiry', 0):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
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
    if not session.get('authenticated') or datetime.now().timestamp() >= session.get('auth_expiry', 0):
        session.pop('authenticated', None)
        session.pop('auth_expiry', None)
        flash('Your session has expired or you are not logged in. Please enter the password to access the tools.', 'danger')
        return redirect(url_for('show_landing_page'))
    
    # Kirim data ke template dashboard
    return render_template('dashboard.html', game_data=current_game_data)

@app.route('/guide')
def guide_page():
    return render_template('guide.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    session.pop('auth_expiry', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('show_landing_page'))

# ====================================================================
# Event Listener SocketIO
# ====================================================================
@socketio.on('connect')
def handle_connect():
    print('Client connected!')
    emit('game_update', current_game_data)
    if not hasattr(socketio, '_background_task_started') or not socketio._background_task_started:
        socketio.start_background_task(target=game_data_fetcher)
        socketio._background_task_started = True
        print("Starting game_data_fetcher background task (real-time mode).")

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected!')

# ====================================================================
# Jalankan Aplikasi
# ====================================================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=True, port=port)