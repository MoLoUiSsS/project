@echo off
:: Vérifier les droits d'administrateur
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Demande des droits d'administrateur pour modifier le pare-feu...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
    
    echo ==============================================
    echo  Configuration du Pare-feu Windows (Firewall)
    echo ==============================================
    echo Autorisation du port 5000 pour la connexion du telephone...
    netsh advfirewall firewall add rule name="LAPI_Port_5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
    
    echo Lancement de l'application LAPI...
    echo.
    py app.py
    
    pause
