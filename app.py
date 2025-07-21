# app.py

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import random
import time
from datetime import datetime, timedelta # Import ini untuk menghitung waktu

app = Flask(__name__)
app.secret_key = 'a1b2c3d4e5f67890abcdef1234567890abcdef1234567890' # GANTI INI DENGAN SECRET KEY YANG SANGAT PANJANG DAN UNIK UNTUK SETUP DEPLOYMENT!

# KONFIGURASI PENTING
ACCESS_PASSWORD = "bhtclub24"
HASHEd_ACCESS_PASSWORD = hashlib.sha256(ACCESS_PASSWORD.encode('utf-8')).hexdigest()

# Variabel global untuk menyimpan status periode terakhir di server
# Ini akan menjadi dictionary untuk menyimpan status per jenis game
# Inisialisasi awal (bisa diatur manual sebagai starting point)
# Untuk produksi, Anda mungkin ingin ini disimpan di database
game_states = {
    'wingo-1-min': {
        'last_period_number': 760, # Contoh: mulai dari periode 566
        'last_update_time': datetime.now(), # Waktu terakhir periode ini diupdate
        'duration_seconds': 60 # Durasi per periode dalam detik
    },
    'wingo-30-sec': {
        'last_period_number': 515, # Contoh: mulai dari periode 345
        'last_update_time': datetime.now(),
        'duration_seconds': 30
    },
    'moto-race': {
        'last_period_number': 745, # Contoh
        'last_update_time': datetime.now(),
        'duration_seconds': 15
    }
}

# Fungsi pembantu untuk menghitung periode dan waktu sisa
def calculate_simulated_period_data(game_type):
    state = game_states.get(game_type)
    if not state:
        return "N/A", 0, "Game type not configured."

    now = datetime.now()
    time_since_last_update = (now - state['last_update_time']).total_seconds()
    
    # Hitung berapa banyak periode yang sudah berlalu sejak update terakhir
    periods_passed = int(time_since_last_update // state['duration_seconds'])
    
    # Update nomor periode
    current_period_number = state['last_period_number'] + periods_passed
    
    # Tangani siklus 1000 ke 001
    if current_period_number > 1000:
        current_period_number = (current_period_number - 1) % 1000 + 1 # (N-1)%1000 + 1 untuk siklus 1-1000

    # Hitung waktu sisa dalam periode saat ini
    remaining_time_in_period = state['duration_seconds'] - (time_since_last_update % state['duration_seconds'])
    remaining_time_seconds = max(0, int(remaining_time_in_period)) # Pastikan tidak negatif

    # Update state untuk request berikutnya
    state['last_period_number'] = current_period_number
    # Update waktu terakhir berdasarkan siklus periode yang penuh
    state['last_update_time'] = state['last_update_time'] + timedelta(seconds=periods_passed * state['duration_seconds'])
    
    return str(current_period_number).zfill(3), remaining_time_seconds, None # Format jadi 001, 010, dll.


@app.route('/')
def index():
    if not session.get('authenticated'):
        return render_template('password_input.html')
    return redirect(url_for('prediction_tool'))

@app.route('/authenticate', methods=['POST'])
def authenticate():
    input_password = request.form['password']
    hashed_input_password = hashlib.sha256(input_password.encode('utf-8')).hexdigest()

    if hashed_input_password == HASHEd_ACCESS_PASSWORD:
        session['authenticated'] = True
        return redirect(url_for('prediction_tool'))
    else:
        return render_template('password_input.html', error="Kata sandi salah. Silakan coba lagi.")

@app.route('/prediction_tool')
def prediction_tool():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('prediction_tool.html')

@app.route('/get_prediction_data/<game_type>', methods=['GET'])
def get_prediction_data(game_type):
    current_period_number, remaining_time, error_message = calculate_simulated_period_data(game_type)
    
    if error_message:
        return jsonify({
            'game_type': game_type,
            'period_number': "Error",
            'remaining_time': 0,
            'prediction': f"Error: {error_message}",
            'error': error_message
        })

    # --- LOGIKA PREDIKSI ASLI ANDA DI SINI ---
    # GANTI INI DENGAN LOGIKA PREDISKSI ANDA YANG SEBENARNYA BERDASARKAN current_period_number
    # Contoh:
    prediction_result = ""
    if game_type == 'wingo-1-min':
        # Contoh prediksi: ganjil/genap
        if int(current_period_number) % 2 == 0:
            prediction_result = "Green"
        else:
            prediction_result = "Red"
    elif game_type == 'wingo-30-sec':
        if int(current_period_number) % 5 == 0:
            prediction_result = "Big"
        else:
            prediction_result = "Small"
    elif game_type == 'moto-race':
        if int(current_period_number) % 3 == 0:
            prediction_result = "Motor A"
        else:
            prediction_result = "Motor B"
    # --- AKHIR LOGIKA PREDIKSI ASLI ANDA ---

    return jsonify({
        'game_type': game_type,
        'period_number': current_period_number, # Sudah diformat "001"
        'remaining_time': remaining_time,
        'prediction': prediction_result,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    app.run(debug=False) # Pastikan ini False untuk deployment!