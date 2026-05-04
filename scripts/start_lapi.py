import ctypes
import sys
import os
import socket

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_local_ips():
    ips = []
    try:
        host_name = socket.gethostname()
        for ip in socket.gethostbyname_ex(host_name)[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except:
        pass
    return ips if ips else ["127.0.0.1"]

if is_admin():
    print("==================================================")
    print("  DÉBLOCAGE DU RÉSEAU POUR LE TÉLÉPHONE")
    print("==================================================")
    
    # Autoriser le port 5000
    os.system('netsh advfirewall firewall add rule name="LAPI_5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1')
    
    # Désactiver la sécurité "Public" temporairement pour être 100% sûr
    os.system('netsh advfirewall set publicprofile state off >nul 2>&1')
    
    print("\n[+] Sécurité débloquée avec succès !")
    print("[+] Lancement de l'application...\n")
    
    os.system(f'"{sys.executable}" app.py')
    
    # Réactiver la sécurité à la fermeture
    print("\n[+] Réactivation de la sécurité Windows...")
    os.system('netsh advfirewall set publicprofile state on >nul 2>&1')
    
    input("Appuyez sur Entrée pour quitter...")
else:
    print("Demande des droits d'administrateur...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
