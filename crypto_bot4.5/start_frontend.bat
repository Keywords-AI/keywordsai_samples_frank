@echo off
echo 🎨 Starting AI Crypto Trading Bot Frontend...
echo.
echo Make sure the backend is running first:
echo   python start_backend.py
echo.
echo Opening frontend in your default browser...
echo Frontend URL: file://%~dp0frontend\index.html
echo.
start "" "%~dp0frontend\index.html"
echo.
echo ✅ Frontend opened! 
echo If it doesn't work, manually open: frontend\index.html
pause 