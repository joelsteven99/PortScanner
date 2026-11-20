import json, os, socket, time
from concurrent.futures import ThreadPoolExecutor

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "puertos.json")

config = {"objetivo": None, "ip": None, "hilos": 100, "timeout": 1.0}

def CargarPuertos():
    try:
        with open(ARCHIVO, encoding="utf-8") as f:data = json.load(f)
        return {int(p): s for p, s in data.items() if 1 <= int(p) <= 65535}
    except FileNotFoundError:print(f"[!] No se encontró el archivo: {ARCHIVO}")
    except (json.JSONDecodeError, ValueError, AttributeError):print(f"[!] El archivo {ARCHIVO} tiene un formato inválido.")
    return {}

def Objetivo():
    host = input("Host o IP objetivo: ").strip()
    if not host:return
    try:
        config["ip"] = socket.gethostbyname(host)
        config["objetivo"] = host
        print(f"[*] Objetivo: {host} ({config['ip']})")
    except socket.gaierror:print(f"[!] No se pudo resolver el host: {host}")


def Configurar():
    h = input(f"Hilos [{config['hilos']}]: ").strip()
    t = input(f"Timeout en segundos [{config['timeout']}]: ").strip()
    try:
        if h:
            if int(h) < 1:raise ValueError
            config["hilos"] = int(h)
        if t:
            if float(t) <= 0:raise ValueError
            config["timeout"] = float(t)
        print(f"[*] Hilos: {config['hilos']} | Timeout: {config['timeout']}s")
    except ValueError:print("[!] Valor inválido.")

def Escanear(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(config["timeout"])
    try:return puerto if s.connect_ex((config["ip"], puerto)) == 0 else None
    except OSError:return None
    finally:s.close()

def ObtenerBanner(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        s.connect((config["ip"], puerto))
        if puerto in (80, 8000, 8080, 8888):s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
        datos = s.recv(128).decode(errors="ignore").strip()
        return datos.splitlines()[0][:60] if datos else ""
    except OSError:return ""
    finally:s.close()

def Ejecutar(puertos, servicios):
    if not config["ip"]:print("[!] Primero define un objetivo (opción 1).");return

    print(f"\n[*] Objetivo : {config['objetivo']} ({config['ip']})")
    print(f"[*] Puertos  : {len(puertos)} | Hilos: {config['hilos']}")
    print("[*] Escaneando... (Ctrl+C para detener)\n")

    t0 = time.time()
    abiertos = []
    try:
        with ThreadPoolExecutor(max_workers=config["hilos"]) as pool:
            for puerto in pool.map(Escanear, puertos):
                if puerto:
                    abiertos.append(puerto)
                    servicio = servicios.get(puerto)
                    if not servicio:
                        try:servicio = socket.getservbyport(puerto, "tcp")
                        except OSError:servicio = "desconocido"
                    banner = ObtenerBanner(puerto)
                    extra = f" | {banner}" if banner else ""
                    print(f"[+] {puerto:<5}/tcp  abierto  {servicio}{extra}")
    except KeyboardInterrupt:print("\n[!] Escaneo interrumpido por el usuario.")

    print(f"\n[*] Terminado en {time.time() - t0:.2f}s")
    print(f"[*] Puertos abiertos: {len(abiertos)}")

def EscanearLista():
    servicios = CargarPuertos()
    if servicios:Ejecutar(sorted(servicios), servicios)

def EscanearRango():
    valor = input("Rango (ej: 1-1024) [1-1024]: ").strip() or "1-1024"
    try:
        ini, fin = (int(x) for x in valor.split("-"))
        if not (1 <= ini <= fin <= 65535):raise ValueError
    except ValueError:print("[!] Rango de puertos inválido (1-65535).");return
    Ejecutar(range(ini, fin + 1), CargarPuertos())

def VerPuertos():
    servicios = CargarPuertos()
    for puerto in sorted(servicios):print(f"{puerto:<6} {servicios[puerto]}")
    if servicios:print(f"\nTotal: {len(servicios)} puertos en {ARCHIVO}")

while True:
    print("\n" + "=" * 46)
    print("\n Escáner de puertos ")
    print("=" * 46)
    print(f"Objetivo: {config['objetivo'] or 'sin definir'}"
          f"{' (' + config['ip'] + ')' if config['ip'] else ''}"
          f" | Hilos: {config['hilos']} | Timeout: {config['timeout']}s")
    print("-" * 46)
    print("1. Definir objetivo")
    print("2. Escanear puertos del JSON")
    print("3. Escanear rango de puertos")
    print("4. Configurar hilos y timeout")
    print("5. Ver puertos del JSON")
    print("0. Salir")
    print("=" * 46)

    try:
        match input("Selecciona una opción: ").strip():
            case "1":Objetivo()
            case "2":EscanearLista()
            case "3":EscanearRango()
            case "4":Configurar()
            case "5":VerPuertos()
            case "0":print("Hasta luego!");break
            case _:print("[!] Opción no válida.")
    except (KeyboardInterrupt, EOFError):print("\nScript detenido!")
