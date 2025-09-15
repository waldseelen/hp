@echo off
setlocal enabledelayedexpansion

REM roadmap.txt dosyasının tam yolu
set "ROADMAP=D:\FILES\BEST\roadmap.txt"

REM Son tamamlanan görevi bul
set "LAST_TASK="
for /f "delims=" %%A in ('type "%ROADMAP%" ^| findstr /b "# ✅"') do (
    set "LAST_TASK=%%A"
)

REM Başındaki "# ✅ " kısmını kaldır
set "LAST_TASK=!LAST_TASK:# ✅ =!"

REM Kontrol: görev bulundu mu?
if "!LAST_TASK!"=="" (
    echo Roadmap dosyasında tamamlanmış görev bulunamadı.
    exit /b 1
)

REM Git durumu kontrol et
git status
echo.
set /p proceed="Değişiklikleri commit edip pushlamak istiyor musunuz? (E/H): "
if /i not "!proceed!"=="E" (
    echo İşlem iptal edildi.
    exit /b 0
)

REM Git işlemleri
git add .
git commit -m "Gelinen son ilerleme / son task: !LAST_TASK!"
git push origin main
echo İşlem tamamlandı.
