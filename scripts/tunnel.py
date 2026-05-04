import os
import subprocess

print("=======================================")
print("      CREATION DU LIEN PUBLIC LAPI")
print("=======================================")

ssh_dir = os.path.expanduser("~/.ssh")
key_path = os.path.join(ssh_dir, "id_rsa")

if not os.path.exists(key_path):
    print("[+] Configuration de la sécurité de Windows (Clé SSH)...")
    os.makedirs(ssh_dir, exist_ok=True)
    subprocess.run(["ssh-keygen", "-t", "rsa", "-N", "", "-f", key_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[+] Configuration terminée.")

print("\n[+] Génération du lien public...")
print("[!] Attention : Laissez cette fenêtre ouverte !\n")

os.system("ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 localhost.run")
