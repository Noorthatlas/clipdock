"use client";

import { useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowRight, Check, CircleAlert, FileVideo, Film, ImageOff, Link2, Music2, ShieldCheck } from 'lucide-react';
import { detectPlatform, PLATFORMS, safeDownload, safeThumbnail, type Platform } from '../lib/security';

type Inspection = { token: string; title: string; thumbnail: string | null; platform: Platform | 'sample'; source_url?: string; duration: number | null; qualities: number[]; has_audio: boolean };
type Props = { apiOrigin: string };

export default function Desk({ apiOrigin }: Props) {
  const [url, setUrl] = useState('');
  const [rights, setRights] = useState(false);
  const [media, setMedia] = useState<Inspection | null>(null);
  const [quality, setQuality] = useState(720);
  const [format, setFormat] = useState<'mp4' | 'mp3'>('mp4');
  const [imageFailed, setImageFailed] = useState(false);
  const [download, setDownload] = useState('');
  const [error, setError] = useState('');
  const [inspecting, setInspecting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [jobStatus, setJobStatus] = useState('queued');
  const revision = useRef(0);
  const controllers = useRef(new Set<AbortController>());
  const pendingDelays = useRef(new Set<() => void>());
  const platform = detectPlatform(url);
  const thumbnail = safeThumbnail(media?.thumbnail);
  const canExport = !!media && rights && !busy && !inspecting && (format === 'mp4' ? media.qualities.length > 0 : media.has_audio);

  useEffect(() => () => {
    revision.current++;
    for (const controller of controllers.current) controller.abort();
    for (const cancel of pendingDelays.current) cancel();
  }, []);

  function invalidate() {
    revision.current++;
    for (const controller of controllers.current) controller.abort();
    for (const cancel of pendingDelays.current) cancel();
    setMedia(null); setDownload(''); setError(''); setBusy(false); setInspecting(false); setImageFailed(false); setProgress(0);
  }

  async function request(path: string, body?: unknown) {
    const controller = new AbortController();
    controllers.current.add(controller);
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([
        fetch(apiOrigin + path, {
          method: body ? 'POST' : 'GET',
          headers: body ? { 'Content-Type': 'application/json' } : undefined,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
          credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer',
        }).then(async response => {
          const data = await response.json();
          if (!response.ok) throw Object.assign(new Error(data.error?.message ?? 'No se pudo completar la solicitud. Vuelve a intentarlo.'), { code: data.error?.code });
          return data;
        }),
        new Promise<never>((_resolve, reject) => {
          controller.signal.addEventListener('abort', () => reject(new Error('Solicitud cancelada.')), { once: true });
          timer = setTimeout(() => {
            reject(new Error('La solicitud tardó demasiado. El servidor puede estar iniciándose; vuelve a intentarlo.'));
            controller.abort();
          }, 45000);
        }),
      ]);
    } finally {
      clearTimeout(timer);
      controllers.current.delete(controller);
    }
  }

  async function inspect(sample = false) {
    if (!rights || (!sample && !platform) || inspecting || busy) return;
    if (sample) { invalidate(); setUrl(''); }
    const version = revision.current;
    setInspecting(true); setError(''); setMedia(null); setDownload(''); setImageFailed(false);
    try {
      const result: Inspection = await request(sample ? '/api/sample/inspect' : '/api/inspect', sample ? { authorized: true } : { url: url.trim(), authorized: true });
      if (version !== revision.current) return;
      if (sample) setUrl(result.source_url ?? '');
      setMedia(result); setQuality(result.qualities[0] ?? 0); setFormat(result.qualities.length ? 'mp4' : 'mp3');
    } catch (cause) {
      if (version === revision.current) setError(cause instanceof TypeError ? 'No pudimos conectar con el servidor. Comprueba tu conexión y vuelve a intentarlo.' : cause instanceof Error ? cause.message : 'No se pudo analizar el enlace.');
    } finally {
      if (version === revision.current) setInspecting(false);
    }
  }

  async function exportFile() {
    if (!canExport || !media) return;
    const version = revision.current;
    setBusy(true); setError(''); setProgress(0); setJobStatus('queued');
    try {
      const deadline = Date.now() + 600000;
      const job = await request('/api/jobs', { token: media.token, authorized: true, format, quality });
      if (version !== revision.current) return;
      while (version === revision.current) {
        if (Date.now() >= deadline) throw new Error('Se agotó el tiempo de preparación. Vuelve a intentarlo.');
        const result = await request('/api/jobs/' + encodeURIComponent(job.id) + '?secret=' + encodeURIComponent(job.secret));
        if (version !== revision.current) return;
        setProgress(Math.min(100, Math.max(0, Number(result.progress) || 0)));
        setJobStatus(result.status);
        if (result.status === 'failed') throw new Error(result.error?.message ?? 'No se pudo preparar el archivo. Vuelve a intentarlo.');
        if (result.status === 'completed') {
          const href = safeDownload(result.download_url, apiOrigin);
          if (!href) throw new Error('El servidor devolvió un enlace de descarga no válido. Vuelve a intentarlo.');
          setDownload(href);
          return;
        }
        await new Promise<void>((resolve, reject) => {
          const cancel = () => { clearTimeout(timer); pendingDelays.current.delete(cancel); reject(new Error('Solicitud cancelada.')); };
          const timer = setTimeout(() => { pendingDelays.current.delete(cancel); resolve(); }, 2000);
          pendingDelays.current.add(cancel);
        });
      }
    } catch (cause) {
      if (version === revision.current) {
        if (cause instanceof Error && 'code' in cause && cause.code === 'INVALID_TOKEN') { setMedia(null); setError('La inspección ha caducado. Vuelve a analizar el enlace.'); }
        else setError(cause instanceof TypeError ? 'Se perdió la conexión con el servidor. Vuelve a intentarlo.' : cause instanceof Error ? cause.message : 'No se pudo preparar el archivo.');
      }
    } finally {
      if (version === revision.current) setBusy(false);
    }
  }

  return (
    <div className="workspace" aria-label="Mesa de exportación">
      <section className="source-pane" aria-labelledby="source-heading">
        <div className="pane-heading"><h2 id="source-heading">Elige tu video</h2><span className="subtle">Enlace público</span></div>
        <form onSubmit={event => { event.preventDefault(); void inspect(); }}>
          <label htmlFor="url" className="field-label">Enlace del video</label>
          <div className="url-control"><Link2 size={19} aria-hidden="true"/><input id="url" type="url" value={url} placeholder="Pega aquí el enlace del video" autoComplete="off" spellCheck={false} aria-describedby="url-help" onChange={event => { invalidate(); setUrl(event.target.value); }}/></div>
          <div id="url-help" className="url-help">{media?.platform === 'sample' ? 'Muestra propia CC0 · no es una plataforma externa' : platform ? <><Check size={14} aria-hidden="true"/>{PLATFORMS[platform]} · enlace reconocido</> : url ? 'Introduce un enlace de una de las seis plataformas compatibles.' : 'YouTube, TikTok, Instagram, Facebook, LinkedIn o X.'}</div>
          <label className="rights"><input type="checkbox" checked={rights} onChange={event => { setRights(event.target.checked); if (!event.target.checked) invalidate(); }}/><span>Soy titular del contenido o tengo permiso para descargarlo.</span></label>
          <button className="button inspect-button" disabled={!rights || !platform || inspecting || busy} type="submit">{inspecting ? 'Analizando enlace…' : 'Analizar enlace'}{!inspecting && <ArrowRight size={17} aria-hidden="true"/>}</button>
        </form>
        <div className="owned-sample"><button type="button" disabled={!rights || inspecting || busy} onClick={() => void inspect(true)}>Probar con muestra propia CC0</button><p className="field-note">Comprueba el procesamiento, no el acceso a las plataformas.</p></div>
        <div className="preview-section">
          <div className="preview-top"><span>{media ? 'Vista previa · miniatura' : 'Vista previa'}</span>{media && <span>{media.platform === 'sample' ? 'Muestra propia CC0' : PLATFORMS[media.platform]}</span>}</div>
          <figure className="preview">
            {media && thumbnail && !imageFailed ? <img src={thumbnail} alt={'Miniatura de ' + media.title} referrerPolicy="no-referrer" onError={() => setImageFailed(true)}/> : <div className="preview-empty">{media ? <ImageOff size={28} strokeWidth={1.5} aria-hidden="true"/> : <Film size={30} strokeWidth={1.5} aria-hidden="true"/>}<strong>{media ? 'Miniatura no disponible' : inspecting ? 'Buscando tu video' : 'Tu video empieza con un enlace'}</strong><p>{media ? 'Puedes preparar el archivo sin la miniatura.' : inspecting ? 'Consultando los datos y formatos disponibles.' : 'Analiza el enlace para ver su información\ny las opciones de descarga.'}</p></div>}
            {inspecting && <figcaption className="sr-only" role="status">Consultando el video y sus formatos disponibles.</figcaption>}
          </figure>
          {media ? <div className="media-detail"><h3>{media.title}</h3><p>{media.duration !== null ? `${Math.floor(media.duration / 60)}:${String(Math.floor(media.duration % 60)).padStart(2,'0')} de duración` : 'Duración no disponible'}<span aria-hidden="true"> · </span>Contenido analizado</p></div> : <p className="preview-caption">Sin reproducción automática. Solo una miniatura del contenido.</p>}
        </div>
      </section>
      <section className="export-pane" aria-labelledby="export-heading">
        <div className="pane-heading"><h2 id="export-heading">Configura tu archivo</h2><ArrowDownToLine size={19} aria-hidden="true"/></div>
        <fieldset className="formats"><legend className="field-label">Formato de descarga</legend>
          <label className={`format-option ${format === 'mp4' ? 'selected' : ''}`}><input type="radio" name="format" disabled={!media?.qualities.length || busy} checked={format === 'mp4'} onChange={() => { setFormat('mp4'); setDownload(''); }}/><FileVideo size={21} aria-hidden="true"/><span><strong>MP4</strong><small>Video con audio, si está disponible</small></span><span className="radio-indicator" aria-hidden="true"/></label>
          <label className={`format-option ${format === 'mp3' ? 'selected' : ''}`}><input type="radio" name="format" disabled={!media?.has_audio || busy} checked={format === 'mp3'} onChange={() => { setFormat('mp3'); setDownload(''); }}/><Music2 size={21} aria-hidden="true"/><span><strong>MP3</strong><small>Solo audio</small></span><span className="radio-indicator" aria-hidden="true"/></label>
        </fieldset>
        <div className="quality-field"><label htmlFor="quality" className="field-label">Calidad del video</label><select id="quality" disabled={!media?.qualities.length || format === 'mp3' || busy} value={media ? quality : ''} onChange={event => { setQuality(Number(event.target.value)); setDownload(''); }}>{media?.qualities.length ? media.qualities.map(value => <option key={value} value={value}>{value === 0 ? 'Original' : value + 'p'}</option>) : <option value="">Disponible después de analizar</option>}</select><p className="field-note">{format === 'mp3' && media ? 'El audio se extrae del contenido disponible.' : 'Solo se muestran las calidades que ofrece el video.'}</p></div>
        <div className="export-summary"><div><span>Archivo</span><strong>{format.toUpperCase()}</strong></div><div><span>Calidad</span><strong>{!media ? 'Por determinar' : format === 'mp3' ? 'Solo audio' : quality === 0 ? 'Original' : `${quality}p`}</strong></div></div>
        <div className="export-action">
          {error && <div role="alert" className="error-message"><CircleAlert size={18} aria-hidden="true"/><p>{error}</p></div>}
          {busy && <div className="job-progress"><div className="progress-caption"><span>{jobStatus === 'queued' ? 'En cola de preparación' : 'Preparando tu archivo'}</span><strong>{progress}%</strong></div><div className="progress-track" role="progressbar" aria-label="Preparando archivo" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><div style={{ transform: `scaleX(${progress / 100})` }}/></div><p>Esta operación puede tardar unos minutos.</p></div>}
          {download ? <div className="completed"><p role="status"><Check size={17} aria-hidden="true"/>Tu archivo está listo</p><a className="button primary" href={download} referrerPolicy="no-referrer" rel="noreferrer" download><ArrowDownToLine size={18} aria-hidden="true"/>Descargar archivo</a><p className="field-note">El enlace es temporal. Descarga el archivo ahora.</p></div> : <><button className="button primary" disabled={!canExport} onClick={() => void exportFile()}><ArrowDownToLine size={18} aria-hidden="true"/>Preparar descarga</button><p className="action-note">{!rights ? 'Confirma que tienes permiso para continuar.' : !media ? 'Analiza el enlace antes de preparar el archivo.' : 'El archivo se prepara en un servidor independiente.'}</p></>}
        </div>
        <p className="permission-note"><ShieldCheck size={16} aria-hidden="true"/><span>Tu confirmación de permiso no es una verificación automática de los derechos.</span></p>
      </section>
    </div>
  );
}
