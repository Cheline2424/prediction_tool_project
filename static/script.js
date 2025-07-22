// script.js
document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi koneksi Socket.IO
    // Jika di-deploy di Render, URL akan sama dengan URL Flask
    var socket = io();

    // Event listener untuk menerima update game dari server Flask
    socket.on('game_update', function(data) {
        console.log('Menerima update game:', data); // Ini akan tampil di Console Developer Tools Anda

        // Update WinGo 1 Minute
        var wingo1MinPeriod = document.getElementById('wingo-1-min-period');
        var wingo1MinCountdown = document.getElementById('wingo-1-min-countdown');
        if (wingo1MinPeriod && wingo1MinCountdown) {
            wingo1MinPeriod.textContent = data.WinGo_1Min.period;
            wingo1MinCountdown.textContent = data.WinGo_1Min.countdown;
        }

        // Update WinGo 30 Seconds
        var wingo30SecPeriod = document.getElementById('wingo-30-sec-period');
        var wingo30SecCountdown = document.getElementById('wingo-30-sec-countdown');
        if (wingo30SecPeriod && wingo30SecCountdown) {
            wingo30SecPeriod.textContent = data.WinGo_30S.period;
            wingo30SecCountdown.textContent = data.WinGo_30S.countdown;
        }
    });

    // Handle koneksi/diskoneksi (opsional, untuk debug di console)
    socket.on('connect', function() {
        console.log('Terhubung ke Socket.IO server!');
    });

    socket.on('disconnect', function() {
        console.log('Terputus dari Socket.IO server!');
    });
});