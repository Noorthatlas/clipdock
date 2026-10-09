# Verificación pública — 9 de octubre de 2026

Estos resultados proceden de Chromium real contra https://clipdock-two.vercel.app y https://clipdock-api.onrender.com. No hubo rutas interceptadas, fetch simulado ni runner inyectado. Se guardaron cuatro archivos mediante el evento nativo de descarga del navegador: MP4 y MP3 en escritorio 1440×1000 y emulación móvil táctil 390×844. FFprobe verificó sus streams; FFmpeg también decodificó MP4 y MP3 sin errores.

La fuente es únicamente el vídeo propio CC0 de 2 segundos con tono sintetizado, publicado y fijado por commit y SHA-256. **No son cuatro descargas de plataformas sociales ni prueban compatibilidad plena con las seis integraciones.** La muestra usa la cola, worker aislado, transporte HTTP guardado, yt-dlp, FFmpeg, capacidades y límites reales de producción.

- Código desplegado: `b1589b894a6e9fcb7abd001da34a4fde20cde903`.
- Vercel: `dpl_H4fi4JcorjxZrVMradYxS5WGu3ZS`, Production / READY; meta Git coincide con ese SHA.
- Render: `dep-db4dfo3ncjis73cl62cg`, live / Docker / Free; mismo SHA.
- `browser-results.json`: HTTP, jobs, tamaños, hashes y streams obtenidos; no contiene capacidades ni tokens de inspección.
- `policy-results.json`: siete verificaciones de permiso, fuente fija, allowlist, capacidades de un trabajo REAL completado y CORS.
- Binarios y capturas correspondientes se adjuntan en el ZIP de entrega bajo `evidence/public-downloads/`. No se guardan en el repositorio.

Para reproducir desde la web: confirmar permiso → «Probar con muestra propia CC0» → MP4 180p o MP3 → «Preparar descarga» → «Descargar archivo». Cambiar de formato y repetir. Para una plataforma externa, pegar una URL propia/autorizada; no se reemplazan fallos por la muestra. YouTube devolvió HTTP400/RESTRICTED_MEDIA en las dos muestras Blender probadas. El resto de plataformas no tiene una descarga pública autorizada acreditada en este informe.
