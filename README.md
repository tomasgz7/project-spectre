<div align="center">

<h1>👾 Project Spectre</h1>
<h3>Electron UI Automation Engine</h3>

<br>

<p>
RPA · Computer Vision · Ingeniería Inversa · DirectInput · WebSocket Interception<br>
<em>Construido sobre una app Electron de terceros. Sin acceso al código fuente. 100% externo.</em>
</p>

<br>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org)
[![DirectInput](https://img.shields.io/badge/DirectInput-Low%20Level%20Input-555?style=flat-square&logo=windows&logoColor=white)](https://learn.microsoft.com/en-us/windows/win32/xinput/xinput-and-directinput)
[![CDP](https://img.shields.io/badge/CDP-WebSocket%20Intercept-4285F4?style=flat-square&logo=googlechrome&logoColor=white)](https://chromedevtools.github.io/devtools-protocol/)

</div>

---

## El problema

Había una aplicación de escritorio basada en Electron con flujos manuales, repetitivos y lentos. Sin API pública. Sin documentación interna. Sin acceso al código fuente.

La solución obvia era automatizarla. La solución interesante era hacerlo desde afuera, tratándola como una caja negra, usando únicamente lo que el sistema expone: píxeles en pantalla, eventos de input y tráfico de red interno.

**Project Spectre** es esa solución.

---

## ¿Qué hace?

- Captura y analiza la pantalla en tiempo real para detectar objetos por color y forma (HSV + contornos)
- Toma decisiones autónomas basadas en lo que detecta visualmente en cada frame
- Inyecta movimientos y clics a nivel de hardware via DirectInput, bypaseando las capas de abstracción del SO
- Deserializa archivos binarios propietarios (`.XYF`) para leer y seguir rutas de navegación dinámicas
- Intercepta el tráfico WebSocket interno de la app via Chrome DevTools Protocol para auditar datos en tiempo real

---

## Arquitectura

### 1. Computer Vision - OpenCV + HSV

El motor captura cada frame con `mss` a la máxima velocidad posible. Convierte al espacio de color HSV para aislar con precisión los elementos de interés por rango de color, aplica máscaras morfológicas para limpiar ruido visual y calcula contornos y momentos para geolocalizar objetivos en pantalla.

```python
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, BLANCO_MIN, BLANCO_MAX)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

La detección valida cada candidato con una segunda máscara de color (naranja) en un radio de 30px alrededor del centroide, eliminando falsos positivos de forma precisa.

### 2. Parser .XYF - Deserialización binaria

La aplicación utiliza un formato propietario `.XYF` para almacenar coordenadas de navegación. Mediante ingeniería inversa del formato, el parser lee los pares de coordenadas con `struct` en Little-Endian y valida rangos para descartar datos corruptos.

```python
def cargar_coords(path):
    data = open(path, 'rb').read()
    coords = []
    for i in range(0, len(data), 8):
        if i + 8 <= len(data):
            x, y = struct.unpack('<II', data[i:i+8])
            if 100 < x < 3840 and 100 < y < 2160:
                coords.append((x, y))
    return coords
```

### 3. DirectInput - Input a nivel de hardware

`pydirectinput` en lugar de `pyautogui`. La diferencia es que DirectInput inyecta eventos directamente en el driver de input, garantizando que la aplicación Electron los detecte correctamente independientemente de sus capas internas.

### 4. Chrome DevTools Protocol - Interceptación WebSocket

Conecta al proceso Electron mediante CDP y captura los mensajes WebSocket internos entre cliente y servidor, permitiendo auditar qué datos transmite la aplicación en cada acción del usuario.

---

## Lógica de ejecución

El sistema corre un loop principal con dos prioridades:

1. **Si hay un objeto detectado** - lo procesa de inmediato: mueve el cursor, ejecuta la acción y verifica por distancia que el objeto desapareció antes de continuar.
2. **Si no hay nada** - avanza al siguiente punto de la ruta según el intervalo configurado.

```
loop
├── detectar() → ¿hay objeto?
│   ├── SÍ → recoger() → verificar desaparición → continuar
│   └── NO → ¿pasó el intervalo? → moveTo(siguiente punto)
└── sleep(0.05)
```

Hotkeys globales via `keyboard`: `F8` para activar/pausar, `Q` para salir.

---

## Stack

| Librería | Rol |
|---|---|
| `opencv-python` + `numpy` | Visión artificial, máscaras HSV, detección de contornos y momentos |
| `mss` | Captura de pantalla de alta velocidad |
| `pydirectinput` | Emulación de input a nivel de hardware |
| `struct` | Deserialización de binarios propietarios en Little-Endian |
| `keyboard` | Hotkeys globales - sistema de pausa y salida de emergencia |

---

## Instalación

```bash
git clone https://github.com/tomasgz7/project-spectre.git
cd project-spectre

pip install mss opencv-python pydirectinput numpy keyboard
```

Colocar el archivo `cordenadas.XYF` en la misma carpeta que el script antes de ejecutar.

> Requiere Python 3.10+ en Windows. DirectInput opera a nivel de hardware; algunas funciones pueden requerir permisos de administrador.

---

## Aviso legal

Proyecto desarrollado con fines educativos y de investigación técnica. Todas las técnicas aplicadas - visión artificial, análisis de protocolos, emulación de inputs - son públicas y ampliamente documentadas en la comunidad de desarrollo. No se distribuye ni vincula ningún software propietario.

---

<div align="center">

*[Tomas Guzman](https://github.com/tomasgz7)*

</div>
