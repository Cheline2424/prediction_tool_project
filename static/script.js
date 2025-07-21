// script.js

// Fungsi pembantu untuk memformat waktu display
function updateTimerDisplay(element, seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    element.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Fungsi untuk mendapatkan data prediksi dari backend
async function fetchPrediction(gameType) {
    try {
        const response = await fetch(`/get_prediction_data/${gameType}`);
        const data = await response.json();
        if (data.error) {
            console.error('Backend Error for ' + gameType + ':', data.error);
            return { period: 'Error', prediction: data.prediction, remainingTime: 0, error: data.error };
        }
        return {
            period: data.period_number,
            prediction: data.prediction,
            remainingTime: data.remaining_time
        };
    } catch (error) {
        console.error('Network or Parsing Error for ' + gameType + ':', error);
        return { period: 'Error', prediction: 'Network Error', remainingTime: 0, error: error.message };
    }
}

// Fungsi utama untuk memulai timer dan fetching data
function startTimer(timerId, predictionId, periodId, defaultDuration, gameType) {
    let timerElement = document.getElementById(timerId);
    let predictionElement = document.getElementById(predictionId);
    let periodElement = document.getElementById(periodId);

    let currentInterval; // Untuk menyimpan referensi interval agar bisa di-clear

    const updateDataAndStartNewTimer = async () => {
        // Hentikan interval sebelumnya jika ada
        if (currentInterval) {
            clearInterval(currentInterval);
        }

        // Tampilkan status loading
        predictionElement.textContent = 'Getting prediction...';
        periodElement.textContent = 'Loading period...';
        updateTimerDisplay(timerElement, defaultDuration); // Tampilkan durasi default saat loading

        // Fetch data dari backend
        const data = await fetchPrediction(gameType);
        
        if (data.error) {
            periodElement.textContent = `Error: ${data.period}`;
            predictionElement.textContent = `Prediction: ${data.prediction}`;
            updateTimerDisplay(timerElement, 0); // Timer jadi 0 jika ada error
            // Coba lagi setelah jeda jika ada error
            setTimeout(updateDataAndStartNewTimer, 5000); // Coba lagi setelah 5 detik
            return;
        }

        // Update tampilan dengan data yang diterima
        periodElement.textContent = `Period: ${data.period}`;
        predictionElement.textContent = `Prediction: ${data.prediction}`;
        
        // Atur waktu sisa berdasarkan data dari backend
        let timeLeft = data.remainingTime > 0 ? data.remainingTime : defaultDuration;

        // Mulai interval baru
        currentInterval = setInterval(() => {
            timeLeft--;
            updateTimerDisplay(timerElement, timeLeft);

            if (timeLeft <= 0) {
                clearInterval(currentInterval); // Hentikan interval saat habis
                updateDataAndStartNewTimer(); // Ambil data baru dan mulai timer baru
            }
        }, 1000); // Update setiap 1 detik
    };

    // Panggil pertama kali saat halaman dimuat
    updateDataAndStartNewTimer();
}

// Event listener saat DOM sudah siap
document.addEventListener('DOMContentLoaded', () => {
    // Panggil startTimer untuk setiap jenis game
    // defaultDuration adalah fallback jika backend tidak memberikan remainingTime
    startTimer('timer-wingo-1-min', 'prediction-wingo-1-min', 'period-wingo-1-min', 60, 'wingo-1-min');
    startTimer('timer-wingo-30-sec', 'prediction-wingo-30-sec', 'period-wingo-30-sec', 30, 'wingo-30-sec');
    startTimer('timer-moto-race', 'prediction-moto-race', 'period-moto-race', 15, 'moto-race');
});