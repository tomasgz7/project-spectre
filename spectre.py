"""
Space Aces - Recolector de cajitas con ruta automática
- Sigue las coordenadas del archivo XYF cada 3 segundos
- Si detecta una cajita, la recoge (clickea cada 0.5s hasta que desaparezca)
- Luego continúa con la ruta

pip install mss opencv-python pydirectinput numpy keyboard
F8 -> activar/pausar | Q -> salir
"""

import cv2
import numpy as np
import mss
import pydirectinput
import keyboard
import time
import struct

pydirectinput.FAILSAFE = True
pydirectinput.PAUSE = 0

# ─── CARGAR COORDENADAS ───────────────────────────────────────────────────────

def cargar_coords(path):
    data = open(path, 'rb').read()
    coords = []
    for i in range(0, len(data), 8):
        if i+8 <= len(data):
            x, y = struct.unpack('<II', data[i:i+8])
            if 100 < x < 3840 and 100 < y < 2160:
                coords.append((x, y))
    return coords

try:
    COORDS = cargar_coords('cordenadas.XYF')
    print(f"Coordenadas cargadas: {len(COORDS)}")
except Exception as e:
    print(f"Error cargando coordenadas: {e}")
    print("Asegurate que cordenadas.XYF esté en la misma carpeta que este script.")
    COORDS = []

INTERVALO_RUTA = 1.5   # segundos entre cada punto de la ruta
DELAY_POST     = 1.5   # espera tras recoger una caja

# ─── DETECCION ────────────────────────────────────────────────────────────────

ZONA = {"top": 100, "left": 220, "width": 1500, "height": 820, "mon": 1}

BLANCO_MIN  = np.array([0,   0,   245])
BLANCO_MAX  = np.array([180, 25,  255])
NARANJA_MIN = np.array([10,  100, 150])
NARANJA_MAX = np.array([30,  255, 255])

sct    = mss.mss()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))

def detectar():
    raw = sct.grab(ZONA)
    bgr = cv2.cvtColor(np.array(raw), cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mb  = cv2.inRange(hsv, BLANCO_MIN, BLANCO_MAX)
    mb  = cv2.morphologyEx(mb, cv2.MORPH_OPEN, kernel)
    cnts, _ = cv2.findContours(mb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cajas = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 10: continue
        x, y, w, h = cv2.boundingRect(c)
        if w > 55 or h > 55 or w < 8 or h < 8: continue
        M = cv2.moments(c)
        if M["m00"] == 0: continue
        cx = int(M["m10"]/M["m00"])
        cy = int(M["m01"]/M["m00"])
        r  = 30
        x1=max(0,cx-r); y1=max(0,cy-r)
        x2=min(hsv.shape[1],cx+r); y2=min(hsv.shape[0],cy+r)
        nar = np.sum(cv2.inRange(hsv[y1:y2,x1:x2], NARANJA_MIN, NARANJA_MAX) > 0)
        if nar < 20: continue
        cajas.append((cx + ZONA["left"], cy + ZONA["top"], nar))
    cajas.sort(key=lambda x: x[2], reverse=True)
    return cajas

def recoger(tx, ty):
    global total
    print(f"\r[BOX] ({tx},{ty}) recogiendo...           ", end="", flush=True)
    while True:
        pydirectinput.moveTo(tx, ty)
        pydirectinput.click()
        time.sleep(0.5)
        cajas = detectar()
        if not any(abs(cx-tx)<65 and abs(cy-ty)<65 for cx,cy,_ in cajas):
            total += 1
            print(f"\r[OK] #{total} recogida!                          ", end="", flush=True)
            time.sleep(DELAY_POST)
            return

# ─── ESTADO ───────────────────────────────────────────────────────────────────

activo    = False
total     = 0
ruta_idx  = 0
ultimo_pt = 0

def toggle():
    global activo
    activo = not activo
    print(f"\n[F8] {'ACTIVADO' if activo else 'PAUSADO'}")

keyboard.add_hotkey("f8", toggle)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

print("=" * 50)
print("  RECOLECTOR DE CAJITAS - Space Aces")
print("=" * 50)
print(f"  Ruta: {len(COORDS)} puntos | Intervalo: {INTERVALO_RUTA}s")
print("  F8 -> Activar/Pausar | Q -> Salir")
print("=" * 50)
print("  PAUSADO\n")

try:
    while True:
        if keyboard.is_pressed("q"):
            print("\n[Q] Saliendo...")
            break

        if not activo:
            time.sleep(0.1)
            continue

        # Primero chequear si hay cajita visible
        cajas = detectar()
        if cajas:
            tx, ty, nar = cajas[0]
            recoger(tx, ty)
            ultimo_pt = time.time()  # resetear timer de ruta
            continue

        # Si no hay cajita, avanzar en la ruta cada 3 segundos
        ahora = time.time()
        if COORDS and ahora - ultimo_pt >= INTERVALO_RUTA:
            px, py = COORDS[ruta_idx % len(COORDS)]
            pydirectinput.moveTo(px, py)
            pydirectinput.click()
            print(f"\r[RUTA] {ruta_idx+1}/{len(COORDS)} ({px},{py}) | cajas={total}   ", end="", flush=True)
            ruta_idx += 1
            ultimo_pt = ahora
        else:
            resto = max(0, INTERVALO_RUTA - (ahora - ultimo_pt))
            print(f"\r[SCAN] Buscando... | prox punto en {resto:.1f}s | cajas={total}   ", end="", flush=True)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n[Ctrl+C] Interrumpido.")
finally:
    sct.close()
    print(f"\nTotal recogidas: {total}")
