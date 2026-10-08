import { ArrowUpRight, CircleAlert, Layers2, ShieldCheck } from 'lucide-react';
import Desk from '../components/desk';
import { validateApiOrigin } from '../lib/security';

export default function Page() {
  const apiOrigin = validateApiOrigin(process.env.NEXT_PUBLIC_API_URL);
  return <>
    <a className="skip-link" href="#contenido">Saltar al contenido</a>
    <header className="site-header"><div className="header-inner"><a className="brand" href="/" aria-label="ClipDock, inicio"><Layers2 size={25} strokeWidth={1.7} aria-hidden="true"/><span>ClipDock</span></a><a className="help-link" href="#limites">Ayuda y límites<ArrowUpRight size={16} aria-hidden="true"/></a></div></header>
    <main id="contenido" className="page-shell">
      <div className="page-intro"><div><h1>Del enlace al archivo.</h1><p>Guarda tus videos. Elige el formato. Llévatelos contigo.</p></div><span className="intro-note"><ShieldCheck size={17} aria-hidden="true"/>Solo contenido propio o con permiso</span></div>
      {apiOrigin ? <Desk apiOrigin={apiOrigin}/> : <section className="configuration-error" role="alert"><CircleAlert size={24} aria-hidden="true"/><div><h2>El servidor aún no está conectado</h2><p>La descarga no está disponible por ahora. Falta configurar una dirección válida de NEXT_PUBLIC_API_URL para el servidor de medios.</p></div></section>}
      <div className="platform-row"><span>Plataformas compatibles</span><ul aria-label="Plataformas compatibles">{['YouTube','TikTok','Instagram','Facebook','LinkedIn','X'].map(name => <li key={name}>{name}</li>)}</ul><p>Disponibilidad según el enlace y la plataforma.</p></div>
      <section className="restrictions" id="limites" aria-labelledby="limits-heading"><div><h2 id="limits-heading">Un enlace público. Un uso responsable.</h2><p>Descarga únicamente contenido propio o para el que tengas permiso explícito. Respeta los derechos de autor y las condiciones de cada plataforma.</p></div><div><h3>Qué puedes esperar</h3><p>La compatibilidad depende del video y puede cambiar. No se admiten contenido privado, DRM, acceso mediante cookies ni evasión de restricciones. Si un enlace no funciona, te indicaremos el motivo.</p><p>La vista previa es una miniatura, no un reproductor. Los archivos y enlaces de descarga son temporales; no constituyen un archivo permanente.</p></div></section>
    </main>
    <footer className="site-footer"><span>ClipDock</span><p>Tu contenido, en el formato que necesitas.</p><span>Sin registro · Sin anuncios</span></footer>
  </>;
}
