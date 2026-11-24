# Telegram Audio Downloader

Script en Python con **Arquitectura Limpia (Clean Architecture)** para descargar archivos de audio desde múltiples canales de Telegram de forma concurrente, mostrando barras de progreso en consola con `rich` y registrando cada descarga en un log JSON (`logs/downloads_log.json`).

## Características

- **Arquitectura Limpia**: separación estricta entre `domain`, `application`, `infrastructure` y `presentation`.
- **Pool de descargas concurrentes**: descarga múltiples audios en paralelo (por defecto `3`, configurable con `--concurrency`).
- **Barras de progreso simultáneas (`rich`)**: muestra progreso, tamaño, velocidad y tiempo restante por cada descarga activa.
- **Idempotencia**: consulta `logs/downloads_log.json` para omitir archivos ya descargados y continuar desde donde quedó si se interrumpe.
- **Multicanal**: gestiona canales desde `config/channels.json` o mediante parámetros CLI.
- **Autenticación flexible**: inicio de sesión estándar por teléfono/código o mediante **código QR** (`--qr`) en terminal.
- **Preparado para IA**: carga credenciales de Together AI y Ollama desde `.env` con un puerto/adaptador base desacoplado (`src/infrastructure/ai/together_client.py`).

## Estructura del proyecto

```text
musica_nueva/
├── config/
│   └── channels.json             # Lista de canales habilitados
├── downloads/                    # Audios descargados, organizados por canal
├── logs/
│   └── downloads_log.json        # Registro JSON de descargas
├── src/
│   ├── domain/                   # Entidades y puertos (Protocol)
│   ├── application/              # Casos de uso (DownloadChannelAudiosUseCase)
│   ├── infrastructure/           # Telethon, .env, persistencia JSON y cliente AI
│   └── presentation/             # CLI (cli.py)
├── tests/                        # Pruebas unitarias (pytest)
├── main.py                       # Punto de entrada
├── pyproject.toml                # Configuración de proyecto, ruff, mypy y pytest
├── requirements.txt              # Dependencias de ejecución
└── requirements-dev.txt          # Dependencias de desarrollo y calidad
```

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements-dev.txt
```

### Configuración inicial

Copia las plantillas de entorno y canales antes de ejecutar el script:

```powershell
Copy-Item .env.example .env
Copy-Item config\channels.example.json config\channels.json
```

Edita `.env` con tu `API_ID` y `API_HASH` obtenidos en [my.telegram.org](https://my.telegram.org).

## Uso

### 1. Primer inicio de sesión
Si el código de verificación no llega o prefieres vincular desde tu celular:
```powershell
.\.venv\Scripts\python.exe main.py --qr
```
En tu celular abre **Telegram → Ajustes → Dispositivos → Vincular dispositivo** y escanea el QR de la terminal. Una vez creada la sesión (`.session`), las siguientes ejecuciones no volverán a pedirlo.

### 2. Descargar audios
```powershell
# Descargar todos los canales habilitados en config/channels.json (3 descargas simultáneas)
.\.venv\Scripts\python.exe main.py

# Ajustar el pool de descargas simultáneas (ej. 2 archivos a la vez)
.\.venv\Scripts\python.exe main.py --concurrency 2

# Probar solo con los últimos 10 mensajes por canal
.\.venv\Scripts\python.exe main.py --limit 10

# Descargar un canal específico sin modificar channels.json
.\.venv\Scripts\python.exe main.py --channel https://t.me/deathmetal2
```

### 3. Gestionar canales
```powershell
# Agregar un nuevo canal a config/channels.json
.\.venv\Scripts\python.exe main.py --add-channel https://t.me/otro_canal

# Listar canales habilitados
.\.venv\Scripts\python.exe main.py --list-channels
```

## Calidad, formateo y pruebas

El proyecto incluye **Ruff** (formateo estilo Prettier y linting), **Mypy** (chequeo de tipos) y **Pytest**:

```powershell
.\.venv\Scripts\ruff.exe format src tests main.py
.\.venv\Scripts\ruff.exe check src tests main.py
.\.venv\Scripts\mypy.exe src tests main.py
.\.venv\Scripts\pytest.exe -v
```
