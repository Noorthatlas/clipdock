# ClipDock backend

FastAPI + yt-dlp + FFmpeg. Solo medios públicos de los que el usuario es propietario o tiene permiso. No importa cookies de sesión, credenciales, proxies ni argumentos libres de yt-dlp. No elude DRM, restricciones de edad/geográficas, contenido privado o membresías.

## Ejecutar

Requisitos: Python 3.12+, uv, FFmpeg/FFprobe y Node 22+. Las dependencias Python están fijadas en `uv.lock`.

```sh
uv sync --frozen
# Generar una clave; guardarla fuera del repositorio y mantenerla al reiniciar.
export CLIPDOCK_SIGNING_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export CLIPDOCK_DATA_DIR=./data
uv run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --no-access-log
```

La aplicación no lee `.env` automáticamente. Exportar las variables o configurarlas en el proveedor. Se niega a arrancar sin clave de al menos 32 caracteres o si otro proceso usa el mismo directorio.

## API

- `GET /health` → `{"status":"ok"}`.
- `POST /api/inspect` con `{url, authorized:true}` → `{token,title,thumbnail,platform,duration,qualities,has_audio}`.
- `POST /api/jobs` con `{token,authorized:true,format:"mp4"|"mp3",quality:720}` → HTTP 202 `{id,secret,status}`.
- `GET /api/jobs/{id}?secret=...` → `{id,status,progress,error?,download_url?}`.
- `GET /api/jobs/{id}/file?secret=...` devuelve el archivo mediante FileResponse, sin cargarlo completo en memoria.
- Errores JSON: `{"error":{"code":"...","message":"..."}}`, en español. Falta de permiso → 403; URL/opción/token inválidos → 400; validación → 422; cola llena → 429; capacidad incorrecta/ausente → 404.

**Extensiones honestas para extractores incompletos:** `qualities` puede contener **0**, que la interfaz debe etiquetar **«Original»**, nunca «0p». `duration` puede ser **null** hasta verificar el archivo local con FFprobe. `has_audio:true` con códec desconocido es una oferta provisional: si no existe pista de audio, la tarea MP3 falla con `NO_AUDIO`. No se inventan alturas ni duraciones. Para MP3, `quality` no altera el audio; la salida usa 192 kbps. Las opciones MP4 se vuelven a validar contra la extracción actual.

`authorized:true` es una declaración del usuario, no una prueba automática de titularidad. No hay endpoint de enumeración de tareas. Los secretos de tarea son capacidades de 256 bits, se almacenan como SHA-256 y los enlaces completos deben tratarse como secretos. Desactivar registros de URL completos en cualquier proxy para no registrar el parámetro `secret`.

## Límites y arquitectura

Un solo proceso Uvicorn, SQLite durable **si el disco persiste**, dos trabajadores por defecto y admisión limitada a ocho tareas pendientes/en proceso. Al reiniciar, trabajos interrumpidos pasan a `SERVICE_RESTARTED`; trabajos completos persisten hasta caducar. Limpieza al arrancar y cada 30 segundos, TTL de una hora; tokens de inspección firmados caducan en diez minutos.

Cada extracción/descarga ocurre en un subproceso con grupo propio, tiempo máximo de 300 s y eliminación del grupo completo (incluidos Node/FFmpeg) al finalizar o exceder límites. FFprobe local tiene 20 s; FFmpeg 180 s, además del límite externo. Duración máxima por defecto: 1200 s, verificada después de descargar antes de convertir, incluso si el extractor la desconoce. Tamaño máximo: 64 MiB; presupuesto agregado: 1 GiB.

Se combinan `max_filesize`, hooks de progreso, supervisión del presupuesto global cada 50 ms, límites de archivo del kernel (`RLIMIT_FSIZE`) y reservas conservadoras de cuatro archivos máximos más 4 MiB por trabajo. Las reservas impiden sobreasignación concurrente; ante exceso se mata el grupo. Para una cuota física estricta que cubra también SQLite, logs y cambios externos al servicio, limitar además el volumen de datos a nivel de filesystem/contenedor: la supervisión por sí sola no es una cuota instantánea de filesystem. El directorio de datos debe ser privado del servicio.

Configuración de límites mediante `CLIPDOCK_CONCURRENCY`, `CLIPDOCK_QUEUE_CAP`, `CLIPDOCK_MAX_DURATION_SECONDS`, `CLIPDOCK_MAX_FILE_BYTES`, `CLIPDOCK_DISK_BUDGET_BYTES`, `CLIPDOCK_TIMEOUT_SECONDS`, `CLIPDOCK_JOB_TTL_SECONDS` y `CLIPDOCK_TOKEN_TTL_SECONDS`. No se permiten más de dos trabajadores ni duraciones superiores a 1200 s. Peticiones JSON limitadas a 32 KiB antes de analizarse.

## Frontera SSRF

Las URLs iniciales deben ser HTTPS, con hosts exactos y IDs de publicación válidos en YouTube, TikTok, Instagram, Facebook, LinkedIn o X/Twitter. Se rechazan puertos explícitos, IPs, credenciales, hosts falsificados y listas. Este MVP acepta enlaces directos, no acortadores de TikTok ni variantes de compartir arbitrarias.

En producción solo se registran familias de extractores de esas plataformas; **no GenericIE**. Se fuerza exclusivamente el transporte Python `UrllibRH`. En cada resolución se comprueba que **todos** los resultados DNS son globales y en cada `connect`/`connect_ex` se vuelve a comprobar la IP numérica efectiva. Esto cubre URLs de extractor, redirecciones, manifests, segmentos y medios, y evita una segunda resolución DNS dentro de `connect`. Se eliminan variables de proxy del subproceso. Los descargadores externos, incluido fallback HLS a FFmpeg, quedan bloqueados. FFprobe/FFmpeg reciben únicamente archivos ya descargados, con protocolos `file,pipe` y demuxers de medios explícitos (no HLS/DASH/concat). Node solo es el runtime local EJS de yt-dlp.

No se devuelven URLs de medios extraídas. Miniaturas HTTPS solo de una allowlist pequeña y explícita de CDN; las demás se suprimen (`null`). Si se exponen directamente a otro origen web, configurar `CLIPDOCK_CORS_ORIGINS` con orígenes HTTPS exactos separados por comas, sin barra final; vacío por defecto. Sin comodines ni cookies CORS.

## Render Free

Usar `Dockerfile`, health check `/health`, plan gratuito y **una instancia**. La imagen contiene Python, FFmpeg/FFprobe y Node 22 y escucha en `0.0.0.0:$PORT`.

`.env.render.example` propone concurrencia 1, cola 3, duración 120 s, archivo 16 MiB, disco 128 MiB y timeout 60 s para 512 MiB de RAM. Configurar la clave como secreto del proveedor; no incluirla en el repositorio. El disco gratuito es efímero: archivos y tareas pueden desaparecer al reemplazar la instancia. Suspensión/reinicio del proveedor no equivale a una cola durable externa. La aplicación no crea servicios ni contrata recursos.

## Verificación

```sh
uv run pytest -q
uv run ruff check clipdock tests main.py smoke.py
uv lock --check
TMPDIR=/opt/data/cache/scratch uv run python smoke.py
```

Las pruebas generan video/audio propio y ejercitan descargas HTTP reales con yt-dlp, conversión real a MP4/MP3 y FFprobe. El extractor de fixture se inyecta desde Python **solo en tests**; no hay flag de producción que permita localhost. `tests/assets/owner-test.mp4` es una muestra pequeña reproducible, CC0.

`smoke.py` usa fixtures públicos de los extractores instalados y **solo inspecciona metadatos**, nunca descarga videos remotos. La presencia de un extractor no garantiza compatibilidad con una plataforma o URL en tiempo real. Ver `TEST_RESULTS.md` y `smoke-results.json`; no se afirman seis descargas verificadas.

Referencias oficiales: README y `supportedsites.md` del repositorio `yt-dlp/yt-dlp` en GitHub. Se instala el extra `[default]` que incluye EJS, y se configura explícitamente Node para YouTube.
