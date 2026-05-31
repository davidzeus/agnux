export interface Shortcut {
  id: string;
  nombre: string;
  icono: string;
  tipo: 'app' | 'url' | 'command';
  destino: string;
  descripcion: string;
}
