# Integraciones y límites reales

## Criterio de compatibilidad

Una entrada en yt-dlp significa que existe extractor, no que todos los vídeos funcionen ni que una plataforma haya concedido autorización de descarga. El MVP no usa APIs oficiales para obtener archivos: integra extractores de yt-dlp para enlaces públicos compatibles. No recoge cookies, contraseñas ni sesiones; no evade DRM ni ofrece proxies para sortear restricciones geográficas o anti-bot.

Fuentes primarias consultadas durante la implementación:
- https://github.com/yt-dlp/yt-dlp
- https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md (advierte explícitamente que la lista no garantiza funcionamiento).
- https://github.com/yt-dlp/yt-dlp/wiki/Extractors
- https://github.com/yt-dlp/yt-dlp/wiki/EJS
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/linkedin.py
- https://nextjs.org/docs/app/getting-started/installation
- https://vercel.com/docs/functions/limitations

## Plataformas

- **YouTube**: vídeos públicos individuales, Shorts y youtu.be; extractor YouTube. Soporte completo puede requerir yt-dlp-ejs y runtime JavaScript; Node instalado en el servidor. Vídeos con DRM, miembros, privados, login obligatorio, bloqueo por región/edad o anti-bot no se desbloquean. No listas ni directos.
- **TikTok**: vídeos públicos y enlaces cortos compatibles; extractor TikTok. Cambios de firmas, restricciones de región/login o desafíos del sitio pueden impedir extracción. No promesa de quitar marcas de agua.
- **Instagram**: publicaciones/reels públicos compatibles; extractor Instagram. No cuentas privadas ni historias que requieren sesión. Un carrusel o publicación con varias entradas puede rechazarse como colección; preferir enlace a vídeo individual.
- **Facebook**: vídeos/reels públicos compatibles; extractores Facebook. Las páginas pueden exigir sesión aun cuando el usuario vea el vídeo desde su navegador; no se importan sus cookies. No grupos privados ni contenido restringido.
- **LinkedIn**: publicaciones con vídeo público y enlace reconocido por LinkedInIE, especialmente URLs de posts con activity ID. No LinkedIn Learning ni contenido autenticado. El extractor puede proporcionar formatos sin altura o duración: la interfaz presenta «Original» cuando no hay resolución fiable, sin inventar calidades.
- **X (Twitter)**: enlaces a estados públicos que contienen vídeo, vía extractor Twitter; también dominio x.com. Imágenes, estados sin vídeo, privados o que requieren autenticación se rechazan. Cambios del sitio pueden romper temporalmente extracción.

## Autorización

El usuario declara propiedad o permiso explícito antes de inspeccionar y descargar. El backend exige la declaración: la UI por sí sola no basta. Una casilla no demuestra derechos de autor de manera independiente. La plataforma no puede determinar automáticamente si alguien posee todos los derechos: antes de abrir un servicio público, el operador debe definir sus condiciones, canal de reclamaciones y tratamiento de abusos. No se han inventado licencias para vídeos ajenos.

## Vista previa y formatos

La vista previa usa metadatos y miniatura segura cuando están disponibles; no es un reproductor que retransmite automáticamente el contenido. Calidades derivadas de metadatos, nunca 1080p/4K inventados. MP4 requiere vídeo; MP3 requiere pista de audio. Un formato no descrito completamente puede fallar al sondear el archivo, con error explícito en vez de un archivo corrupto.

## Separación de despliegue

Vercel aloja Next.js; el navegador llama directamente al backend HTTPS y descarga del backend. No se hacen transcodificaciones ni se transportan archivos grandes a través de funciones Vercel. Esas funciones tienen límites de duración y payload, por lo que no son la arquitectura de procesamiento de este proyecto.

## Evidencia de pruebas

Los resultados realmente ejecutados están en backend/TEST_RESULTS.md y el informe raíz VERIFICATION.md cuando finalice la validación. Los tests con metadatos controlados no equivalen a descargas reales de seis plataformas. La prueba de conversión usa exclusivamente vídeo de prueba generado localmente y una costura de test aislada; la API de producción no permite URLs arbitrarias ni localhost.
