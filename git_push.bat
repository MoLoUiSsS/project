@echo off
echo =========================================
echo  Nettoyage et Envoi sur GitHub (LAPI)
echo =========================================

echo.
echo [1] Creation du dossier scripts...
if not exist "scripts" mkdir scripts

echo.
echo [2] Deplacement des documents vers docs\...
move /Y LAPI_Cahier_Des_Charges.tex docs\ >nul 2>&1
move /Y LAPI_Description_For_Claude.md docs\ >nul 2>&1
move /Y LAPI_IEEE_Report.md docs\ >nul 2>&1
move /Y LAPI_IEEE_Report.pdf docs\ >nul 2>&1
move /Y LAPI_IEEE_Report.tex docs\ >nul 2>&1

echo.
echo [3] Deplacement des scripts vers scripts\...
move /Y compile_tex.py scripts\ >nul 2>&1
move /Y md_to_pdf.py scripts\ >nul 2>&1
move /Y test_arduino.py scripts\ >nul 2>&1
move /Y start_lapi.py scripts\ >nul 2>&1
move /Y tunnel.py scripts\ >nul 2>&1
move /Y tunnel_https.py scripts\ >nul 2>&1
move /Y lancer_application.bat scripts\ >nul 2>&1

echo.
echo [4] Git Add...
git add .

echo.
echo [5] Git Commit...
git commit -m "chore: clean up project structure and add IoT phone camera features"

echo.
echo [6] Git Push vers GitHub...
git push origin main

echo.
echo =========================================
echo  TERMINE ! Tout est clean et en ligne.
echo =========================================
pause
