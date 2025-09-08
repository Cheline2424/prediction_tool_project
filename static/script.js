document.addEventListener('DOMContentLoaded', function() {
    var socket = io();

    socket.on('game_update', function(data) {
        console.log("Data diterima dari server:", data);
        
        // Update WinGo 30 Second
        const wingo30sec = data.wingo_30_sec;
        if (wingo30sec) {
            document.getElementById('wingo_30_sec_period').textContent = wingo30sec.period || 'N/A';
            document.getElementById('wingo_30_sec_countdown').textContent = wingo30sec.countdown || 'N/A';
            document.getElementById('wingo_30_sec_number').textContent = wingo30sec.number || 'N/A';
            document.getElementById('wingo_30_sec_color').textContent = wingo30sec.color || 'N/A';
            document.getElementById('wingo_30_sec_big_small').textContent = wingo30sec.big_small || 'N/A';
        }

        // Update WinGo 1 Minute
        const wingo1min = data.wingo_1_min;
        if (wingo1min) {
            document.getElementById('wingo_1_min_period').textContent = wingo1min.period || 'N/A';
            document.getElementById('wingo_1_min_countdown').textContent = wingo1min.countdown || 'N/A';
            document.getElementById('wingo_1_min_number').textContent = wingo1min.number || 'N/A';
            document.getElementById('wingo_1_min_color').textContent = wingo1min.color || 'N/A';
            document.getElementById('wingo_1_min_big_small').textContent = wingo1min.big_small || 'N/A';
        }
    });
});