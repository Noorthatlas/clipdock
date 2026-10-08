import type { Metadata, Viewport } from 'next';
import './globals.css';
export const metadata:Metadata={title:'ClipDock — Tu video, tu archivo',description:'Prepara archivos MP4 o MP3 de contenido propio o autorizado. Compatibilidad condicionada con YouTube, TikTok, Instagram, Facebook, LinkedIn y X.',robots:{index:false,follow:false}};
export const viewport:Viewport={width:'device-width',initialScale:1,themeColor:'#f1f3f6'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="es"><body>{children}</body></html>;}
