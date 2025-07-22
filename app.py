import eventlet # BARIS BARU: Tambahkan ini
eventlet.monkey_patch() # BARIS BARU: Tambahkan ini setelah import eventlet

import os
# import time # Hapus baris ini jika ada, karena kita akan menggunakan eventlet.sleep
import json
# import threading # Biarkan ini untuk saat ini, tetapi mungkin tidak diperlukan nanti
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' # Ganti dengan kunci rahasia yang kuat
socketio = SocketIO(app, cors_allowed_origins="*") # Mengizinkan CORS untuk SocketIO

current_game_data = {
    "WinGo_1Min": {"period": "N/A", "countdown": "00:00"},
    "WinGo_30S": {"period": "N/A", "countdown": "00:00"},
    "Moto_Race": {"period": "N/A", "countdown": "00:00"}
}

# Fungsi untuk menghitung mundur (TETAP SAMA)
def calculate_countdown(end_time_ms):
    end_time_s = end_time_ms / 1000
    current_time_s = datetime.now().timestamp()
    countdown_s = max(0, int(end_time_s - current_time_s))

    minutes = countdown_s // 60
    seconds = countdown_s % 60
    return f"{minutes:02d}:{seconds:02d}"

# Fungsi untuk mengambil data game secara real-time
# UBAH: Hapus 'async' dari sini
def game_data_fetcher(): # Nama fungsi tetap sama
    base_url_30s = "https://draw.ar-lottery01.com/WinGo/WinGo_30S.json"
    base_url_1m = "https://draw.ar-lottery01.com/WinGo/WinGo_1M.json"
    base_url_moto = "https://draw.ar-lottery01.com/WinGo/Moto_Race.json" # Tambahkan URL untuk Moto Race

    headers = {
        "Referer": "https://bharatclub.net/",
        "Sec-Ch-Ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"130\"",
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
    }

    while True:
        try:
            # --- Ambil data WinGo 30 Seconds ---
            timestamp_30s = int(datetime.now().timestamp() * 1000)
            full_url_30s = f"{base_url_30s}?ts={timestamp_30s}"
            print(f"Mengambil data WinGo 30S dari: {full_url_30s}")
            response_30s = requests.get(full_url_30s, headers=headers, timeout=5)
            response_30s.raise_for_status()
            data_30s = response_30s.json()
            print(f"DEBUG: Full JSON response for WinGo 30S: {json.dumps(data_30s, indent=2)}")

            current_data_30s = data_30s.get("current")
            if current_data_30s:
                issue_number_30s = current_data_30s.get("issueNumber")
                end_time_ms_30s = current_data_30s.get("endTime")
                countdown_30s = calculate_countdown(end_time_ms_30s)

                print(f"WinGo 30S - IssueNumber: {issue_number_30s}, endTime: {end_time_ms_30s}, countdown: {countdown_30s}")
                current_game_data["WinGo_30S"]["period"] = issue_number_30s
                current_game_data["WinGo_30S"]["countdown"] = countdown_30s
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response WinGo 30S.")

            # --- Ambil data WinGo 1 Minute ---
            timestamp_1m = int(datetime.now().timestamp() * 1000)
            full_url_1m = f"{base_url_1m}?ts={timestamp_1m}"
            print(f"Mengambil data WinGo 1M dari: {full_url_1m}")
            response_1m = requests.get(full_url_1m, headers=headers, timeout=5)
            response_1m.raise_for_status()
            data_1m = response_1m.json()
            print(f"DEBUG: Full JSON response for WinGo 1M: {json.dumps(data_1m, indent=2)}")

            current_data_1m = data_1m.get("current")
            if current_data_1m:
                issue_number_1m = current_data_1m.get("issueNumber")
                end_time_ms_1m = current_data_1m.get("endTime")
                countdown_1m = calculate_countdown(end_time_ms_1m)

                print(f"WinGo 1M - IssueNumber: {issue_number_1m}, endTime: {end_time_ms_1m}, countdown: {countdown_1m}")
                current_game_data["WinGo_1Min"]["period"] = issue_number_1m
                current_game_data["WinGo_1Min"]["countdown"] = countdown_1m
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response WinGo 1M.")

            # --- Ambil data Moto Race ---
            timestamp_moto = int(datetime.now().timestamp() * 1000)
            full_url_moto = f"{base_url_moto}?ts={timestamp_moto}"
            print(f"Mengambil data Moto Race dari: {full_url_moto}")
            response_moto = requests.get(full_url_moto, headers=headers, timeout=5)
            response_moto.raise_for_status()
            data_moto = response_moto.json()
            print(f"DEBUG: Full JSON response for Moto Race: {json.dumps(data_moto, indent=2)}")

            current_data_moto = data_moto.get("current")
            if current_data_moto:
                issue_number_moto = current_data_moto.get("issueNumber")
                end_time_ms_moto = current_data_moto.get("endTime")
                countdown_moto = calculate_countdown(end_time_ms_moto)

                print(f"Moto Race - IssueNumber: {issue_number_moto}, endTime: {end_time_ms_moto}, countdown: {countdown_moto}")
                current_game_data["Moto_Race"]["period"] = issue_number_moto
                current_game_data["Moto_Race"]["countdown"] = countdown_moto
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response Moto Race.")

            # Kirim update ke semua client yang terhubung
            socketio.emit('game_update', current_game_data)
            print(f"Data game terbaru dikirim: {current_game_data}")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengambil data via HTTP: {e}")
        except json.JSONDecodeError:
            print("Menerima response non-JSON atau JSON tidak valid.")
        except Exception as e:
            print(f"Terjadi error tak terduga di game data fetcher: {e}")

        # UBAH: Tunggu sebentar sebelum request berikutnya
        eventlet.sleep(1) # Ganti dari asyncio.sleep(1) ke eventlet.sleep(1)

# Fungsi untuk menjalankan game data fetcher di greenlet terpisah
def run_game_data_fetcher():
    # UBAH: Ganti dari asyncio.run(websocket_client()) ke eventlet.spawn
    eventlet.spawn(game_data_fetcher) # Jalankan game_data_fetcher sebagai greenlet

@app.route('/')
def index():
    return render_template('prediction_tool.html', game_data=current_game_data)

@socketio.on('connect')
def test_connect():
    print('Client terhubung!')
    # Kirim data saat ini ke client yang baru terhubung
    emit('game_update', current_game_data)

@socketio.on('disconnect')
def test_disconnect():
    print('Client terputus!')

if __name__ == '__main__':
    # Jalankan fungsi fetcher data di awal
    run_game_data_fetcher()
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) # Tambahkan int() untuk port