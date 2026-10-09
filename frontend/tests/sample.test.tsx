import { render, screen, fireEvent } from '@testing-library/react';
import { it, expect, vi } from 'vitest';
import Desk from '../src/components/desk';

it('labels the first-party diagnostic honestly and uses the real API contract (mock transport)', async () => {
  const api = 'https://api.clipdock.test';
  const fetcher = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
    token:'owned-token', title:'ClipDock · muestra propia CC0', platform:'sample',
    duration:2, qualities:[180], has_audio:true, thumbnail:null,
    source_url:'https://raw.githubusercontent.com/Noorthatlas/clipdock/90089cc28480b1195c955e5333d06cb886f9a2f9/backend/tests/assets/owner-test.mp4',
  })));
  render(<Desk apiOrigin={api}/>);
  const button = screen.getByRole('button', { name:'Probar con muestra propia CC0' });
  expect(button).toBeDisabled();
  expect(screen.getByText('Comprueba el procesamiento, no el acceso a las plataformas.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(button);
  await screen.findByText('ClipDock · muestra propia CC0');
  expect(fetcher).toHaveBeenCalledWith(api+'/api/sample/inspect', expect.objectContaining({body:JSON.stringify({authorized:true})}));
  expect(screen.getByText('Muestra propia CC0 · no es una plataforma externa')).toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Analizar enlace'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Preparar descarga'})).toBeEnabled();
  fireEvent.change(screen.getByLabelText('Enlace del video'),{target:{value:'https://x.com/user/status/123'}});
  expect(screen.queryByText('ClipDock · muestra propia CC0')).not.toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Preparar descarga'})).toBeDisabled();
});
