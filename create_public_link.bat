@echo off
title PSYCHIATRYK SWIZARLAND - PUBLIC TUNNEL
color 0A

echo ======================================================================
echo            PSYCHIATRYK SWIZARLAND - SEKTA LIKWIDACYJNA
echo                         PUBLIC TUNNEL
echo ======================================================================
echo.
echo Creating PUBLIC tunnel to your dashboard...
echo.
echo Your dashboard is running on: http://192.168.1.132:8080
echo.
echo Creating public URL...
echo.

ssh -R 80:localhost:8080 serveo.net

pause
