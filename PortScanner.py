#!/usr/bin/env python3
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor

SERVICIOS_COMUNES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    1723: "PPTP", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 8080: "HTTP-alt", 8443: "HTTPS-alt",
}

TIMEOUT = 1.0

if len(sys.argv) < 2:print(__doc__);sys.exit(1)

objetivo = sys.argv[1]
inicio = int(sys.argv[2]) if len(sys.argv) > 2 else 1
fin = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
hilos = int(sys.argv[4]) if len(sys.argv) > 4 else 100

if not (1 <= inicio <= fin <= 65535):print("[!] Rango de puertos inválido (1-65535).");sys.exit(1)

try:ip = socket.gethostbyname(objetivo)
except socket.gaierror:print(f"[!] No se pudo resolver el host: {objetivo}"):sys.exit(1)

def escanear(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        resultado = s.connect_ex((ip, puerto))
        return puerto if resultado == 0 else None
    except OSError:return None
    finally:s.close()

def obtener_banner(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        s.connect((ip, puerto))
        if puerto in (80, 8080):s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
        datos = s.recv(128).decode(errors="ignore").strip()
        return datos.splitlines()[0][:60] if datos else ""
    except OSError:return ""
    finally:s.close()

print(f"[*] Objetivo : {objetivo} ({ip})")
print(f"[*] Puertos  : {inicio}-{fin} | Hilos: {hilos}")
print("[*] Escaneando...\n")

t0 = time.time()
abiertos = []

try:
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        for puerto in pool.map(escanear, range(inicio, fin + 1)):
            if puerto:
                abiertos.append(puerto)
                servicio = SERVICIOS_COMUNES.get(puerto)
                if not servicio:
                    try:servicio = socket.getservbyport(puerto, "tcp")
                    except OSError:servicio = "desconocido"
                banner = obtener_banner(puerto)
                extra = f" | {banner}" if banner else ""
                print(f"[+] {puerto:<5}/tcp  abierto  {servicio}{extra}")
except KeyboardInterrupt:print("\n[!] Escaneo interrumpido por el usuario.")

print(f"\n[*] Terminado en {time.time() - t0:.2f}s")
print(f"[*] Puertos abiertos: {len(abiertos)}")
