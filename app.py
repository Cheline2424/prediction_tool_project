import os
import time
import json
import threading
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

current_game_data = {
    "WinGo_1Min": {"period": "N/A", "countdown": "00:00"},
    "WinGo_30S": {"period": "N/A", "countdown": "00:00"}
}

def calculate_countdown(end_time_ms):
    """
    Menghitung waktu mundur dari timestamp akhir dalam milidetik.
    Mengembalikan format MM:SS.
    """
    if not end_time_ms:
        return "00:00"

    current_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    remaining_ms = end_time_ms - current_time_ms

    if remaining_ms <= 0:
        return "00:00"

    remaining_seconds = remaining_ms // 1000
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def game_data_fetcher():
    # Pastikan URL ini benar-benar untuk game WinGo_30S dan WinGo_1M
    base_url_30s = "https://draw.ar-lottery01.com/WinGo/WinGo_30S.json"
    base_url_1m = "https://draw.ar-lottery01.com/WinGo/WinGo_1M.json"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Origin": "https://bharatclub.net",
        "Referer": "https://bharatclub.net/",
        "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
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
            # Ini adalah baris print yang penting untuk debugging
            print(f"DEBUG: Full JSON response for WinGo 30S: {json.dumps(data_30s, indent=2)}")

            # Pastikan mengambil dari objek 'current' yang berisi data terkini
            current_data_30s = data_30s.get("current")
            if current_data_30s:
                issue_number_30s = current_data_30s.get("issueNumber")
                end_time_ms_30s = current_data_30s.get("endTime")
                countdown_30s = calculate_countdown(end_time_ms_30s)

                # Tambahkan print di sini untuk melihat nilai yang diekstrak
                print(f"WinGo 30S - issueNumber: {issue_number_30s}, endTime: {end_time_ms_30s}, countdown: {countdown_30s}")

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
            # Ini adalah baris print yang penting untuk debugging
            print(f"DEBUG: Full JSON response for WinGo 1M: {json.dumps(data_1m, indent=2)}")

            # Pastikan mengambil dari objek 'current' yang berisi data terkini
            current_data_1m = data_1m.get("current")
            if current_data_1m:
                issue_number_1m = current_data_1m.get("issueNumber")
                end_time_ms_1m = current_data_1m.get("endTime")
                countdown_1m = calculate_countdown(end_time_ms_1m)
                
                # Tambahkan print di sini untuk melihat nilai yang diekstrak
                print(f"WinGo 1Min - issueNumber: {issue_number_1m}, endTime: {end_time_ms_1m}, countdown: {countdown_1m}")

                current_game_data["WinGo_1Min"]["period"] = issue_number_1m
                current_game_data["WinGo_1Min"]["countdown"] = countdown_1m
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response WinGo 1M.")


            socketio.emit('game_update', current_game_data)
            print(f"Mengirim update: {current_game_data}")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengambil data via HTTP: {e}")
            current_game_data["WinGo_1Min"] = {"period": "Error", "countdown": "Error"}
            current_game_data["WinGo_30S"] = {"period": "Error", "countdown": "Error"}
            socketio.emit('game_update', current_game_data) # Kirim error ke frontend
        except json.JSONDecodeError:
            print(f"Menerima response non-JSON atau JSON tidak valid.")
            current_game_data["WinGo_1Min"] = {"period": "JSON Error", "countdown": "JSON Error"}
            current_game_data["WinGo_30S"] = {"period": "JSON Error", "countdown": "JSON Error"}
            socketio.emit('game_update', current_game_data) # Kirim error ke frontend
        except Exception as e:
            print(f"Terjadi error tak terduga di game data fetcher: {e}")
            current_game_data["WinGo_1Min"] = {"period": "Unknown Error", "countdown": "Unknown Error"}
            current_game_data["WinGo_30S"] = {"period": "Unknown Error", "countdown": "Unknown Error"}
            socketio.emit('game_update', current_game_data) # Kirim error ke frontend
        
        time.sleep(3) # Tunggu 3 detik

@app.route('/')
def index():
    return render_template('prediction_tool.html', game_data=current_game_data)

@socketio.on('connect')
def test_connect():
    print('Client terhubung!')
    emit('game_update', current_game_data)

@socketio.on('disconnect')
def test_disconnect():
    print('Client terputus!')

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('WERKZEUG_RUN_MAIN'):
        socketio.start_background_task(target=game_data_fetcher)
    
    socketio.run(app, host='0.0.0.0', port=os.environ.get('PORT', 5000), allow_unsafe_werkzeug=True)