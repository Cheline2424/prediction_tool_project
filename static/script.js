document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi koneksi Socket.IO
    var socket = io();

    // Tangani event 'game_update' dari server
    socket.on('game_update', function(data) {
        // Update WinGo 1 Minute
        document.getElementById('wingo_1_min_period').textContent = data.wingo_1_min.period;
        document.getElementById('wingo_1_min_countdown').textContent = data.wingo_1_min.countdown;
        document.getElementById('wingo_1_min_number').textContent = data.wingo_1_min.number;
        document.getElementById('wingo_1_min_color').textContent = data.wingo_1_min.color;
        document.getElementById('wingo_1_min_big_small').textContent = data.wingo_1_min.big_small;

        // Update WinGo 30 Second
        document.getElementById('wingo_30_sec_period').textContent = data.wingo_30_sec.period;
        document.getElementById('wingo_30_sec_countdown').textContent = data.wingo_30_sec.countdown;
        document.getElementById('wingo_30_sec_number').textContent = data.wingo_30_sec.number;
        document.getElementById('wingo_30_sec_color').textContent = data.wingo_30_sec.color;
        document.getElementById('wingo_30_sec_big_small').textContent = data.wingo_30_sec.big_small;

        // Update Moto Race
        document.getElementById('moto_race_period').textContent = data.moto_race.period;
        document.getElementById('moto_race_countdown').textContent = data.moto_race.countdown;
        
        const motoRaceResultsList = document.getElementById('moto_race_results');
        motoRaceResultsList.innerHTML = ''; // Bersihkan hasil sebelumnya
        data.moto_race.results.forEach(result => {
            const li = document.createElement('li');
            li.textContent = `${result.position}: Number ${result.number} (${result.odd_even}, ${result.big_small})`;
            motoRaceResultsList.appendChild(li);
        });

        // Tambah Update Chicken Road
        document.getElementById('chicken_road_period').textContent = data.chicken_road.period || 'N/A';
        document.getElementById('chicken_road_countdown').textContent = data.chicken_road.countdown || 'N/A';

        const chickenRoadResultsList = document.getElementById('chicken_road_results');
        if (chickenRoadResultsList) {
            chickenRoadResultsList.innerHTML = ''; // Bersihkan hasil sebelumnya
            data.chicken_road.results.forEach(result => {
                const li = document.createElement('li');
                li.textContent = `Road: ${result.road} | Safe: ${result.safe} | Prediction: ${result.prediction}`;
                chickenRoadResultsList.appendChild(li);
            });
        }
    });
});