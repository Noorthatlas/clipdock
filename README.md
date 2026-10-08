# ClipDock

MVP para inspeccionar y exportar vídeo público **propio o con permiso explícito** desde YouTube, TikTok, Instagram, Facebook, LinkedIn y X. Next.js + Tailwind en frontend, FastAPI + yt-dlp + FFmpeg en backend independiente.

> La declaración de permiso no verifica por sí sola los derechos. Compatibilidad significa extractor disponible, no descarga garantizada. No cookies de sesión, contenido privado, DRM ni mecanismos para eludir restricciones.

## Estructura

- `frontend/`: Next.js App Router, interfaz española responsive, tests de interfaz.
- `backend/`: API FastAPI, trabajos con capacidades secretas, límites de recursos, procesado aislado, pruebas.
- `INTEGRATIONS.md`: integraciones y restricciones con fuentes primarias.
- `backend/README.md`: contrato HTTP, seguridad, configuración y ejecución.
- `backend/TEST_RESULTS.md`: resultados ejecutados por el implementador (cuando finalice).
- `VERIFICATION.md`: verificación consolidada local y de producción; no sustituye pruebas reales por mocks.

## Prerrequisitos

Node.js compatible con la versión bloqueada de Next.js; Python 3.12+, uv, FFmpeg/ffprobe. El backend requiere Node.js para la extracción de YouTube y extras por defecto de yt-dlp; Dockerfile los incorpora. `npm ci` y `uv sync --frozen` respetan los lockfiles.

## Backend local

```bash
cd backend
uv sync --frozen
cp .env.example .env
# Genera CLIPDOCK_SIGNING_KEY con el comando de .env.example.
# Rellena únicamente tu archivo .env local. No lo subas a Git.
uv run --env-file .env uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

Para evitar depender de soporte dotenv opcional, también puedes exportar variables del entorno de forma segura antes de arrancar. No se permiten varios workers para el mismo directorio de datos. Consultar los comandos actualizados en `backend/README.md`.

## Frontend local

```bash
cd frontend
npm ci
npm run dev
```

Configura `NEXT_PUBLIC_API_URL` con el origen del backend antes de iniciar/compilar. La configuración de producción exige un backend HTTPS. La política CORS del backend debe incluir el origen exacto del frontend; no usar `*`. Para validación de navegador local con política HTTPS, utiliza desarrollo local HTTPS y un navegador de prueba que confíe en su certificado. Los tests unitarios de red son controlados y no equivalen a descargas remotas.

## Pruebas

```bash
cd backend
uv run pytest -q
uv run ruff check .
cd ../frontend
npm test
npm run typecheck
npm run build
```

La prueba de pipeline crea/usa un archivo de prueba propio, ejecuta yt-dlp y FFmpeg, y verifica streams con ffprobe. Esa prueba no habilita localhost ni extractores genéricos en la API de producción. Los probes de plataformas son de metadatos, no pruebas de descarga autorizada.

## Despliegue

### Backend

Servidor Linux independiente o servicio Docker con FFmpeg, Node.js, salida HTTPS y un proceso uvicorn. Configurar `CLIPDOCK_SIGNING_KEY` como secreto del proveedor, `CLIPDOCK_CORS_ORIGINS` con el origen exacto final y límites conservadores. El Dockerfile escucha `PORT` (por defecto 8000), corre sin root y no incluye credenciales. Health check: `/health`.

En Render: repositorio, raíz `backend`, Docker, plan **free explícito**, una instancia, sin previews, sin disco de pago, sin escalado. La API de Render puede asignar un plan de pago por defecto: nunca omitir `plan: free`. Consultar `.env.render.example`.

**Render Free no ofrece disponibilidad adecuada para prometer servicio de producción estable.** Se duerme, pierde SQLite y archivos al reiniciar, comparte cuotas con los otros servicios gratuitos del workspace y puede suspender tráfico saliente alto. Con método de pago puede cobrar exceso de tráfico; sin método de pago suspende. No introducir tarjeta ni contratar planes sin autorización. Fuente: https://render.com/docs/free y https://render.com/docs/outbound-bandwidth.

### Frontend en Vercel Production

Raíz `frontend`, framework Next.js, `npm ci`, `npm run build`, sin override de outputDirectory. Crear `NEXT_PUBLIC_API_URL` **en Production**, apuntando al backend HTTPS real. Cambiarla exige recompilar porque es variable pública incorporada al bundle. Desplegar usando `vercel --prod`, no Preview. Para acceso público revisar protección **del proyecto**, no cambiar el equipo global. El navegador llama directamente a la API y descarga directamente desde el backend: Vercel no procesa ni proxifica medios grandes.

### Gate de producción

1. Leer de vuelta proyecto, variables (sin revelar secretos), servicio y deployment.
2. Probar el alias sin autenticación y comprobar target Production y READY.
3. Verificar `/health`, CORS, CSP y comportamiento mobile/desktop.
4. Desde el navegador público, pegar una URL con permiso comprobado y descargar MP4 y MP3.
5. Verificar HTTP, archivos no vacíos, streams y códecs con ffprobe.
6. Si cualquier paso falla, declarar el bloqueo; no anunciar el conjunto como operativo.

## Retención y restricciones

Archivos y tokens caducan. El servicio no recupera archivos borrados por un host efímero. Los límites de tamaño, duración, plazo, colas y concurrencia evitan transcodificaciones sin cota; no prometen impedir cualquier abuso o probar derechos de autor. Antes de abrir al público, preparar condiciones y canal de reclamaciones del operador; este repositorio no inventa datos legales de la empresa.
