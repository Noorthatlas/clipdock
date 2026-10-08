# Verificación de ClipDock

## Estado final actual: despliegue parcial, NO operativo de extremo a extremo

Frontend publicado en **Vercel Production**, no Preview:

- URL pública: https://clipdock-two.vercel.app
- Project ID: `prj_NQwe8XQZsFpY8Hg9AZm1oGzPoaC9`
- Deployment ID: `dpl_6mcoRhZdM1tS8Wo4iJW4WJfcXhno`
- Cuenta/equipo: MooProjects / `moo-projects-projects`
- API de Vercel leída después del despliegue: `target=production`, `readyState=READY`.
- Alias e immutable hostname: HTTP 200 sin autenticación.
- Framework Next.js, build `npm run build`, instalación `npm ci`, sin override de outputDirectory.
- No se modificaron otros proyectos ni la protección global del equipo.

**Backend no desplegado.** El usuario autorizó solo gratuito. No se obtuvo confirmación de ausencia de método de pago/gasto adicional en Render; no se creó servicio ni se contrató plan. No se alteró el servicio Render existente de otro proyecto. `NEXT_PUBLIC_API_URL` está deliberadamente sin configurar, no apunta a localhost ni a un hostname inventado. La aplicación muestra «El servidor aún no está conectado» y no ofrece descargas falsas.

## Pruebas ejecutadas por el agente principal

### Backend

```text
uv run pytest -q
22 passed in 6.10s
uv run ruff check .
All checks passed!
uv run pytest tests/test_real_pipeline.py -v
2 passed in 3.14s
```

El test real parametrizado ejecuta descarga yt-dlp y conversión FFmpeg de un vídeo propio generado localmente. Verifica MP4 con vídeo+audio y MP3 solo audio mediante FFprobe, con metadatos conocidos y desconocidos. La costura se inyecta exclusivamente en el test: no hay excepción de localhost ni extractor genérico en producción.

Uvicorn local real en 127.0.0.1:8310:
- `/health`: HTTP 200, `{"status":"ok"}`.
- Inspección con `authorized:false`: HTTP 403, `AUTHORIZATION_REQUIRED`.
- Inspección de `http://127.0.0.1/secret` aun con autorización: HTTP 400, `INVALID_URL`.
- OPTIONS con origen HTTPS configurado: HTTP 200, `Access-Control-Allow-Origin` exacto.
- Inspección del upload Blender Big Buck Bunny `YE7VzlLtp-4`: HTTP 400, `RESTRICTED_MEDIA`. No bypass ni descarga intentada tras el bloqueo. El acceso directo del principal a la página de licencia devolvió 403; la investigación auxiliar identificó la licencia CC BY 3.0 pero eso no establece accesibilidad desde esta red.

### Frontend

```text
npm test
Test Files 3 passed
Tests 21 passed
npm run typecheck
Sin errores (exit 0)
```

Vercel ejecutó `npm ci`: cero vulnerabilidades reportadas por esa ejecución de npm audit; Next.js 16.4.0; compilación, TypeScript y generación estática correctas. Esto no es una auditoría de seguridad absoluta.

### Navegador real

- Mesa de exportación local: capturas full-page desktop 1440 y móvil 390, sin overflow; estados vacíos reales sin metadatos ficticios.
- Producción pública con servidor desconectado: Chromium/Playwright desktop 1440 y móvil 390.
- Ambos HTTP 200, cero errores de consola/página observados, cero solicitudes fallidas, sin overflow horizontal.
- Enlace «Ayuda y límites» cambia a `#limites` y el bloque queda visible.
- El aviso de backend no conectado aparece en ambas capturas. **Descargas en producción no verificadas.**
- Evidencia local del principal: `/opt/data/cache/scratch/clipdock-production/browser-results.json`, `desktop.png`, `mobile.png`. No contiene credenciales.

## Integraciones remotas: resultado de metadatos, NO seis descargas

El implementador probó seis URLs de tests oficiales de yt-dlp con extracción de metadatos únicamente. JSON en `backend/smoke-results.json`:
- YouTube: `RESTRICTED_MEDIA`.
- TikTok: `RESTRICTED_MEDIA`.
- Instagram: metadatos obtenidos; miniatura null, audio no disponible en metadatos.
- Facebook: `EXTRACTION_FAILED`.
- LinkedIn: metadatos obtenidos; calidad «Original», duración desconocida.
- X: `RESTRICTED_MEDIA`.

Ninguna descarga remota autorizada completa de estas seis plataformas quedó verificada. No se puede anunciar compatibilidad plena a partir de esos probes o del fixture local.

## Bloqueos para completar producción

1. Backend compatible autorizado y coste verificado. Render Free es técnicamente posible, pero duerme, pierde datos/archivos, comparte cuotas y puede suspender tráfico saliente alto. No es base para prometer producción estable. Fuentes: https://render.com/docs/free, https://render.com/docs/outbound-bandwidth, https://render.com/acceptable-use.
2. Desplegar y leer de vuelta configuración real; configurar secreto de firma y CORS para el alias final; establecer `NEXT_PUBLIC_API_URL` en Production y recompilar.
3. Probar contenido propio o explícitamente autorizado, idealmente URLs de un mismo corto propio publicado en cada plataforma. No se recibió ese conjunto.
4. Verificar en el navegador público inspección → creación de trabajo → estado → descarga MP4 y MP3; archivos, tamaño/duración/códecs con FFprobe.
5. Dockerfile preparado, pero no construido: el daemon Docker no está disponible aquí. No se presenta el archivo como una imagen ejecutada.

No hay cargos contratados, evasión de DRM, uso de cookies ni simulación de éxitos.
