import os
import urllib.request
import subprocess
import threading
import time
import re

CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
EXE_PATH = "cloudflared.exe"

def download_cloudflared():
    if not os.path.exists(EXE_PATH):
        print("[+] Téléchargement de Cloudflare (Tunnel HTTPS sécurisé)...")
        urllib.request.urlretrieve(CLOUDFLARED_URL, EXE_PATH)
        print("[+] Téléchargement terminé.")

def run_tunnel():
    print("[+] Démarrage du tunnel HTTPS...")
    # Cloudflared outputs to stderr
    process = subprocess.Popen(
        [EXE_PATH, "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    url_found = False
    
    while True:
        line = process.stderr.readline()
        if not line:
            break
            
        # Search for the trycloudflare URL
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match and not url_found:
            url = match.group(0)
            print("\n" + "="*60)
            print(" ✅ SUCCÈS ! VOICI LE LIEN POUR VOTRE TÉLÉPHONE :")
            print(f" 👉 {url}/camera")
            print("="*60 + "\n")
            url_found = True

if __name__ == "__main__":
    try:
        download_cloudflared()
        
        print("\n[!] Assurez-vous que votre application LAPI est déjà lancée (py app.py) dans un autre terminal !")
        print("[!] Patientez quelques secondes pour l'obtention du lien HTTPS...\n")
        
        run_tunnel()
    except Exception as e:
        print(f"Erreur : {e}")
