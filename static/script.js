document.addEventListener('DOMContentLoaded', function() {
    var socket = io();

    socket.on('game_update', function(data) {
        // Log data yang diterima untuk debugging
        console.log("Data diterima dari server:", data);

        const wingo30sec = data.wingo_30_sec;
        if (wingo30sec) {
            document.getElementById('wingo_30_sec_period').textContent = wingo30sec.period || 'N/A';
            document.getElementById('wingo_30_sec_countdown').textContent = wingo30sec.countdown || 'N/A';
            document.getElementById('wingo_30_sec_number').textContent = wingo30sec.number || 'N/A';
            document.getElementById('wingo_30_sec_color').textContent = wingo30sec.color || 'N/A';
            document.getElementById('wingo_30_sec_big_small').textContent = wingo30sec.big_small || 'N/A';
        }

        // Anda dapat menambahkan logika untuk WinGo 1 Minute di sini jika diperlukan
        const wingo1min = data.wingo_1_min;
        if (wingo1min) {
            // Contoh: perbarui elemen untuk WinGo 1 Minute
            // document.getElementById('wingo_1_min_period').textContent = wingo1min.period || 'N/A';
            // ... dan seterusnya
        }
    });
});