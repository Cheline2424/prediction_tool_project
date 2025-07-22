// script.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded. Initializing Socket.IO...');

    // Inisialisasi koneksi Socket.IO
    // Jika di-deploy di Render, URL akan sama dengan URL Flask.
    // Jika ada masalah koneksi, coba spesifikasikan URL Render Anda:
    // var socket = io('https://prediction-tool-project.onrender.com');
    var socket = io();

    // Event listener ketika berhasil terhubung ke Socket.IO server
    socket.on('connect', function() {
        console.log('Socket.IO: Terhubung ke server!');
    });

    // Event listener ketika terputus dari Socket.IO server
    socket.on('disconnect', function() {
        console.log('Socket.IO: Terputus dari server!');
    });

    // Event listener untuk menerima update game dari server Flask
    socket.on('game_update', function(data) {
        console.log('Socket.IO: Menerima update game:', data); // Ini akan tampil di Console Developer Tools Anda

        // Pastikan data yang diterima memiliki struktur yang diharapkan
        if (data && typeof data === 'object') {
            // Update WinGo 1 Minute
            var wingo1MinPeriod = document.getElementById('wingo-1-min-period');
            var wingo1MinCountdown = document.getElementById('wingo-1-min-countdown');

            if (wingo1MinPeriod && wingo1MinCountdown && data.WinGo_1Min) {
                wingo1MinPeriod.textContent = data.WinGo_1Min.period || 'N/A';
                wingo1MinCountdown.textContent = data.WinGo_1Min.countdown || '00:00';
                console.log('WinGo 1 Min updated:', data.WinGo_1Min.period, data.WinGo_1Min.countdown);
            } else {
                console.warn('Could not find WinGo 1 Min elements or data is missing.', {wingo1MinPeriod, wingo1MinCountdown, dataWinGo1Min: data.WinGo_1Min});
            }

            // Update WinGo 30 Seconds
            var wingo30SecPeriod = document.getElementById('wingo-30-sec-period');
            var wingo30SecCountdown = document.getElementById('wingo-30-sec-countdown');

            if (wingo30SecPeriod && wingo30SecCountdown && data.WinGo_30S) {
                wingo30SecPeriod.textContent = data.WinGo_30S.period || 'N/A';
                wingo30SecCountdown.textContent = data.WinGo_30S.countdown || '00:00';
                console.log('WinGo 30 Sec updated:', data.WinGo_30S.period, data.WinGo_30S.countdown);
            } else {
                console.warn('Could not find WinGo 30 Sec elements or data is missing.', {wingo30SecPeriod, wingo30SecCountdown, dataWinGo30S: data.WinGo_30S});
            }
        } else {
            console.error('Socket.IO: Received invalid game_update data:', data);
        }
    });
});