import eventlet
eventlet.monkey_patch() # Penting: Lakukan monkey patch di awal

import os
import json
from datetime import datetime
import httpx # Menggunakan httpx
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ====================================================================
# Konfigurasi Aplikasi Flask
# ====================================================================
app = Flask(__name__)

# Konfigurasi SECRET_KEY untuk Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PRODUCTION')

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ====================================================================
# Variabel Global untuk Data Game
# ====================================================================
current_game_data = {
    "WinGo_1Min": {"period": "N/A", "countdown": "00:00"},
    "WinGo_30S": {"period": "N/A", "countdown": "00:00"},
    "Moto_Race": {"period": "N/A", "countdown": "00:00"}
}

# ====================================================================
# Fungsi Bantu
# ====================================================================
def calculate_countdown(end_time_ms):
    """Menghitung hitungan mundur dari waktu berakhir dalam milidetik."""
    end_time_s = end_time_ms / 1000
    current_time_s = datetime.now().timestamp()
    countdown_s = max(0, int(end_time_s - current_time_s))

    minutes = countdown_s // 60
    seconds = countdown_s % 60
    return f"{minutes:02d}:{seconds:02d}"

# ====================================================================
# Fungsi Pengambilan Data Game (Background Task)
# ====================================================================
def game_data_fetcher():
    """Mengambil data game secara periodik dan mengirimkannya ke klien via SocketIO."""
    base_url_30s = "https://draw.ar-lottery01.com/WinGo/WinGo_30S.json"
    base_url_1m = "https://draw.ar-lottery01.com/WinGo/WinGo_1M.json"
    base_url_moto = "https://draw.ar-lottery01.com/WinGo/Moto_Race.json"

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
        # === WinGo 30S ===
        try:
            timestamp_30s = int(datetime.now().timestamp() * 1000)
            full_url_30s = f"{base_url_30s}?ts={timestamp_30s}"
            print(f"Mengambil data WinGo 30S dari: {full_url_30s}")
            response_30s = httpx.get(full_url_30s, headers=headers, timeout=5)
            response_30s.raise_for_status() # Akan memunculkan error untuk status kode HTTP yang buruk (4xx atau 5xx)
            data_30s = response_30s.json()

            current_data_30s = data_30s.get("current")
            if current_data_30s:
                issue_number_30s = current_data_30s.get("issueNumber")
                end_time_ms_30s = current_data_30s.get("endTime")
                countdown_30s = calculate_countdown(end_time_ms_30s)
                current_game_data["WinGo_30S"]["period"] = issue_number_30s
                current_game_data["WinGo_30S"]["countdown"] = countdown_30s
                print(f"Berhasil: WinGo 30S - Periode: {issue_number_30s}, Mundur: {countdown_30s}")
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response WinGo 30S.")
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP WinGo 30S: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error Jaringan WinGo 30S: {e}")
        except json.JSONDecodeError:
            print("Error: Gagal mengurai JSON dari respons WinGo 30S.")
        except Exception as e:
            print(f"Error tak terduga saat mengambil WinGo 30S: {e}")

        # === WinGo 1M ===
        try:
            timestamp_1m = int(datetime.now().timestamp() * 1000)
            full_url_1m = f"{base_url_1m}?ts={timestamp_1m}"
            print(f"Mengambil data WinGo 1M dari: {full_url_1m}")
            response_1m = httpx.get(full_url_1m, headers=headers, timeout=5)
            response_1m.raise_for_status()
            data_1m = response_1m.json()

            current_data_1m = data_1m.get("current")
            if current_data_1m:
                issue_number_1m = current_data_1m.get("issueNumber")
                end_time_ms_1m = current_data_1m.get("endTime")
                countdown_1m = calculate_countdown(end_time_ms_1m)
                current_game_data["WinGo_1Min"]["period"] = issue_number_1m
                current_game_data["WinGo_1Min"]["countdown"] = countdown_1m
                print(f"Berhasil: WinGo 1M - Periode: {issue_number_1m}, Mundur: {countdown_1m}")
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response WinGo 1M.")
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP WinGo 1M: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error Jaringan WinGo 1M: {e}")
        except json.JSONDecodeError:
            print("Error: Gagal mengurai JSON dari respons WinGo 1M.")
        except Exception as e:
            print(f"Error tak terduga saat mengambil WinGo 1M: {e}")

        # === Moto Race ===
        try:
            timestamp_moto = int(datetime.now().timestamp() * 1000)
            full_url_moto = f"{base_url_moto}?ts={timestamp_moto}"
            print(f"Mengambil data Moto Race dari: {full_url_moto}")
            response_moto = httpx.get(full_url_moto, headers=headers, timeout=5)
            response_moto.raise_for_status()
            data_moto = response_moto.json()

            current_data_moto = data_moto.get("current")
            if current_data_moto:
                issue_number_moto = current_data_moto.get("issueNumber")
                end_time_ms_moto = current_data_moto.get("endTime")
                countdown_moto = calculate_countdown(end_time_ms_moto)
                current_game_data["Moto_Race"]["period"] = issue_number_moto
                current_game_data["Moto_Race"]["countdown"] = countdown_moto
                print(f"Berhasil: Moto Race - Periode: {issue_number_moto}, Mundur: {countdown_moto}")
            else:
                print("Peringatan: Objek 'current' tidak ditemukan di response Moto Race.")
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP Moto Race: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error Jaringan Moto Race: {e}")
        except json.JSONDecodeError:
            print("Error: Gagal mengurai JSON dari respons Moto Race.")
        except Exception as e:
            print(f"Error tak terduga saat mengambil Moto Race: {e}")

        # Kirim data terbaru ke semua klien yang terhubung melalui SocketIO
        socketio.emit('game_update', current_game_data)
        print(f"Data game terbaru dikirim: {current_game_data}")

        # Tunggu 1 detik sebelum mengambil data lagi
        eventlet.sleep(1)

# ====================================================================
# Route Flask
# ====================================================================
@app.route('/')
def index():
    """Merender halaman utama aplikasi."""
    return render_template('prediction_tool.html', game_data=current_game_data)

# ====================================================================
# Event Listener SocketIO
# ====================================================================
@socketio.on('connect')
def handle_connect():
    """Menangani koneksi klien SocketIO baru."""
    print('Client terhubung!')
    # Kirim data game yang terakhir diketahui segera setelah klien terhubung
    emit('game_update', current_game_data)

    # Memulai background task untuk mengambil data jika belum berjalan.
    if not hasattr(socketio, '_background_task_started') or not socketio._background_task_started:
        socketio.start_background_task(target=game_data_fetcher)
        socketio._background_task_started = True # Tandai bahwa task sudah dimulai
        print("Memulai background task game_data_fetcher.")

@socketio.on('disconnect')
def handle_disconnect():
    """Menangani pemutusan koneksi klien SocketIO."""
    print('Client terputus!')

# ====================================================================
# Jalankan Aplikasi (Hanya untuk Pengembangan Lokal)
# ====================================================================
if __name__ == '__main__':
    pass # Tidak perlu kode di sini karena Gunicorn yang akan menjalankan