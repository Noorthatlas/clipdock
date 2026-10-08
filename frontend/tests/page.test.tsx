import { render,screen } from '@testing-library/react';
import { afterEach,describe,expect,it,vi } from 'vitest';
import Page from '../src/app/page';
afterEach(()=>vi.unstubAllEnvs());
describe('public page',()=>{it('fails closed with a useful configuration message when the API origin is missing',()=>{vi.stubEnv('NEXT_PUBLIC_API_URL','');render(<Page/>);expect(screen.getByRole('alert')).toHaveTextContent('servidor');expect(screen.queryByRole('button',{name:'Analizar enlace'})).not.toBeInTheDocument();expect(screen.getByRole('link',{name:'Ayuda y límites'})).toHaveAttribute('href','#limites');});});
