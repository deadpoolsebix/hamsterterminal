@echo off
cd /d "%~dp0"
echo Starting HTTP Server on port 8080...
echo.
echo Open on computer: http://localhost:8080/professional_dashboard_live.html
echo.
ipconfig | findstr /i "IPv4"
echo.
echo Open on phone: http://YOUR_IP:8080/professional_dashboard_live.html
echo.
python -m http.server 8080
pause
