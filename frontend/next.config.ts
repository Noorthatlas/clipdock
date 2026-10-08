import type { NextConfig } from 'next';
import { THUMBNAIL_HOSTS,validateApiOrigin } from './src/lib/security';
const api=validateApiOrigin(process.env.NEXT_PUBLIC_API_URL);
const dev=process.env.NODE_ENV!=='production';
const localWs=dev&&api&&new URL(api).protocol==='http:'?api.replace('http:','ws:'):'';
const csp=["default-src 'self'",`script-src 'self' 'unsafe-inline'${dev?" 'unsafe-eval'":''}`,"style-src 'self' 'unsafe-inline'",`img-src 'self' ${THUMBNAIL_HOSTS.map(host=>'https://'+host).join(' ')}`,`connect-src 'self' ${api??''} ${localWs}`,"font-src 'self'","object-src 'none'","frame-src 'none'","frame-ancestors 'none'","base-uri 'self'","form-action 'self'"].join('; ');
const config:NextConfig={poweredByHeader:false,reactStrictMode:true,async headers(){return [{source:'/:path*',headers:[{key:'Content-Security-Policy',value:csp},{key:'X-Content-Type-Options',value:'nosniff'},{key:'X-Frame-Options',value:'DENY'},{key:'Referrer-Policy',value:'no-referrer'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=(), payment=()'}]}];}};
export default config;
