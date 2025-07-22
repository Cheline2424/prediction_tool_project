import os
import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import websockets

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' # Ganti dengan kunci rahasia yang kuat!
socketio = SocketIO(app, cors_allowed_origins="*") # Mengizinkan CORS untuk SocketIO

# Variabel global untuk menyimpan data game terbaru
# Kita akan menyimpan data untuk WinGo 1 Min dan WinGo 30 Sec
current_game_data = {
    "WinGo_1Min": {"period": "N/A", "countdown": "00:00"},
    "WinGo_30S": {"period": "N/A", "countdown": "00:00"}
}

# Fungsi untuk menghitung countdown
def calculate_countdown(end_time_ms):
    """
    Menghitung waktu mundur dari timestamp akhir dalam milidetik.
    Mengembalikan format MM:SS.
    """
    if not end_time_ms:
        return "00:00"

    # Waktu saat ini dalam milidetik
    current_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Selisih waktu dalam milidetik
    remaining_ms = end_time_ms - current_time_ms

    if remaining_ms <= 0:
        return "00:00"

    # Konversi ke detik
    remaining_seconds = remaining_ms // 1000

    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    return f"{minutes:02d}:{seconds:02d}"

# Fungsi async untuk terhubung dan mendengarkan WebSocket
async def websocket_client():
    # URL WebSocket dari JSON response Anda. Ini yang kita temukan: wss://ws-pro.ar-lottery01.com
    # TAPI, berdasarkan JSON terakhir yang Anda berikan dari WinGo_30S.json,
    # data periode dan waktu datang dari HTTP GET requests reguler, bukan langsung dari WebSocket umum.
    # WebSocket di JSON yang Anda berikan adalah "webSocketUrl": "wss://ws-pro.ar-lottery01.com"
    # Ini kemungkinan untuk notifikasi umum, bukan update game spesifik.

    # Karena itu, kita akan menggunakan metode HTTP GET untuk mengambil data WinGo_30S.json
    # secara berkala, seperti yang Anda tunjukkan di tab Network (WinGo_30S.json?ts=...)
    # Ini lebih pasti daripada menebak format WebSocket yang belum kita lihat.

    # Menggunakan requests untuk HTTP GET
    import requests

    # Base URL untuk mengambil data game WinGo_30S.json
    base_url_30s = "https://draw.ar-lottery01.com/WinGo/WinGo_30S.json"

    # Base URL untuk mengambil data game WinGo_1M.json (kita asumsikan mirip)
    base_url_1m = "https://draw.ar-lottery01.com/WinGo/WinGo_1M.json"

    # Headers yang Anda berikan sebelumnya. Cookie tidak ada, jadi kita abaikan untuk sementara.
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
            response_30s.raise_for_status() # Akan memunculkan error jika status bukan 2xx
            data_30s = response_30s.json()

            if data_30s.get("gameCode") == "WinGo_30S":
                issue_number_30s = data_30s.get("issueNumber")
                end_time_ms_30s = data_30s.get("endTime")
                countdown_30s = calculate_countdown(end_time_ms_30s)

                current_game_data["WinGo_30S"]["period"] = issue_number_30s
                current_game_data["WinGo_30S"]["countdown"] = countdown_30s

            # --- Ambil data WinGo 1 Minute ---
            # Asumsi URL dan formatnya mirip dengan WinGo 30S
            timestamp_1m = int(datetime.now().timestamp() * 1000)
            full_url_1m = f"{base_url_1m}?ts={timestamp_1m}"
            print(f"Mengambil data WinGo 1M dari: {full_url_1m}")
            response_1m = requests.get(full_url_1m, headers=headers, timeout=5)
            response_1m.raise_for_status()
            data_1m = response_1m.json()

            if data_1m.get("gameCode") == "WinGo_1M": # Asumsi gameCode untuk 1 Menit adalah WinGo_1M
                issue_number_1m = data_1m.get("issueNumber")
                end_time_ms_1m = data_1m.get("endTime")
                countdown_1m = calculate_countdown(end_time_ms_1m)

                current_game_data["WinGo_1Min"]["period"] = issue_number_1m
                current_game_data["WinGo_1Min"]["countdown"] = countdown_1m

            # Kirim update ke semua klien web melalui SocketIO
            socketio.emit('game_update', current_game_data)
            print(f"Mengirim update: {current_game_data}")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengambil data via HTTP: {e}")
        except json.JSONDecodeError:
            print(f"Menerima response non-JSON atau JSON tidak valid.")
        except Exception as e:
            print(f"Terjadi error tak terduga di game data fetcher: {e}")

        # Tunggu sebentar sebelum request berikutnya
        await asyncio.sleep(1) # Ambil data setiap 1 detik

# Fungsi untuk menjalankan game data fetcher di thread terpisah
def run_game_data_fetcher():
    asyncio.run(websocket_client()) # Nama fungsinya tetap websocket_client, tapi isinya sudah HTTP GET

# Rute utama untuk menampilkan halaman
@app.route('/')
def index():
    return render_template('index.html', game_data=current_game_data)

# SocketIO event handler ketika client terhubung
@socketio.on('connect')
def test_connect():
    print('Client terhubung!')
    # Kirim data saat ini ke client yang baru terhubung
    emit('game_update', current_game_data)

@socketio.on('disconnect')
def test_disconnect():
    print('Client terputus!')

# Jalankan game data fetcher di thread terpisah saat aplikasi Flask dimulai
if __name__ == '__main__':
    # Pastikan ini hanya berjalan sekali saat debug reloader aktif
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('WERKZEUG_RUN_MAIN'):
        game_data_thread = threading.Thread(target=run_game_data_fetcher, daemon=True)
        game_data_thread.start()

    # Jalankan aplikasi Flask dengan SocketIO
    socketio.run(app, host='0.0.0.0', port=os.environ.get('PORT', 5000), allow_unsafe_werkzeug=True)